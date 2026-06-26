import threading
import time

import av
import cv2
import mediapipe as mp
import numpy as np
from streamlit_webrtc import VideoProcessorBase

from services.config.workout_config import POSE_CONNECTIONS
from services.vision.detector_base import standardize_detector_metrics
from services.vision.detector_registry import build_detectors
from services.vision.pose_quality import calculate_pose_visibility, get_camera_guidance, get_missing_body_parts


SUPPORTED_EXERCISES = {"Squats", "Push-ups", "Plank"}


class VideoProcessorClass(VideoProcessorBase):
    """Small live processor for the public MVP camera flow.

    It keeps all heavy or unreliable work out of the frame loop: no LLM calls,
    no TTS, no database writes, and no exercise classifier.
    """

    POSE_CONFIGS = {
        "faster": {"model_complexity": 0, "min_detection_confidence": 0.45, "min_tracking_confidence": 0.45},
        "accuracy": {"model_complexity": 1, "min_detection_confidence": 0.45, "min_tracking_confidence": 0.45},
    }
    QUALITY_PROFILES = {
        "Low": {"process_every_n_frames": 2},
        "Standard": {"process_every_n_frames": 1},
        "High": {"process_every_n_frames": 1},
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"
        self._started_at = time.perf_counter()
        self._pose_profile = "accuracy"
        self._quality = "Standard"
        self._process_every_n_frames = 1
        self._pose = self._create_pose(self.POSE_CONFIGS[self._pose_profile])
        self._detectors = build_detectors()
        self._draw_pose_overlay = False
        self._last_error = ""
        self._last_frame_at = 0.0
        self._frame_count = 0
        self._fps = 0.0
        self._last_fps_check_at = time.perf_counter()
        self._last_fps_frame_count = 0
        self._processed_frame_count = 0
        self._skipped_frames = 0
        self._total_processing_ms = 0.0
        self._last_input_frame_at = 0.0
        self._input_fps = 0.0
        self._frame_timestamps_ms = 0

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = dict(metrics)

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else dict(self._latest_metrics)

    def set_exercise(self, exercise_type):
        selected = exercise_type if exercise_type in SUPPORTED_EXERCISES else "Squats"
        with self._lock:
            self._exercise_type = selected

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def set_draw_pose_overlay(self, enabled):
        with self._lock:
            self._draw_pose_overlay = bool(enabled)

    def get_draw_pose_overlay(self):
        with self._lock:
            return self._draw_pose_overlay

    def set_quality_profile(self, quality):
        selected = quality if quality in self.QUALITY_PROFILES else "Standard"
        with self._lock:
            self._quality = selected
            self._process_every_n_frames = int(self.QUALITY_PROFILES[selected]["process_every_n_frames"])

    def set_pose_profile(self, profile):
        selected = profile if profile in self.POSE_CONFIGS else "accuracy"
        with self._lock:
            if self._pose_profile == selected:
                return
            self._pose_profile = selected
            self._pose = self._create_pose(self.POSE_CONFIGS[selected])

    def get_debug_snapshot(self):
        with self._lock:
            detector = self._detectors.get(self._exercise_type)
            elapsed = max(1e-6, time.perf_counter() - self._started_at)
            return {
                "exercise": self._exercise_type,
                "detector_class": detector.__class__.__name__ if detector else "Unavailable",
                "last_error": self._last_error,
                "last_frame_at": self._last_frame_at,
                "frame_timestamp_ms": self._frame_timestamps_ms,
                "fps": round(self._fps, 1),
                "input_fps": round(self._input_fps, 1),
                "processed_fps": round(self._processed_frame_count / elapsed, 1),
                "frame_count": self._frame_count,
                "processed_frame_count": self._processed_frame_count,
                "skipped_frames": self._skipped_frames,
                "average_processing_ms": round(self._total_processing_ms / max(1, self._processed_frame_count), 2),
                "pose_profile": self._pose_profile,
                "quality_profile": self._quality,
            }

    def _create_pose(self, cfg):
        return mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=int(cfg.get("model_complexity", 1)),
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=float(cfg.get("min_detection_confidence", 0.45)),
            min_tracking_confidence=float(cfg.get("min_tracking_confidence", 0.45)),
        )

    def _mark_frame_received(self):
        now = time.perf_counter()
        wall_now = time.time()

        with self._lock:
            if self._last_input_frame_at:
                elapsed_input = now - self._last_input_frame_at
                if elapsed_input > 0:
                    self._input_fps = 1.0 / elapsed_input
            self._last_input_frame_at = now
            self._last_frame_at = wall_now
            self._frame_count += 1

            elapsed = now - self._last_fps_check_at
            if elapsed >= 1.0:
                frames = self._frame_count - self._last_fps_frame_count
                self._fps = frames / elapsed
                self._last_fps_check_at = now
                self._last_fps_frame_count = self._frame_count

    def _finish_processing(self, process_start):
        processing_ms = (time.perf_counter() - process_start) * 1000.0
        with self._lock:
            self._processed_frame_count += 1
            self._total_processing_ms += processing_ms

    def _draw_skeleton(self, image, landmarks):
        h, w = image.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            if p1.visibility > 0.6 and p2.visibility > 0.6:
                cv2.line(
                    image,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 186, 255),
                    3,
                    cv2.LINE_AA,
                )

        for landmark in landmarks:
            if landmark.visibility > 0.6:
                cv2.circle(image, (int(landmark.x * w), int(landmark.y * h)), 5, (255, 122, 0), -1)

    def _draw_no_pose_warnings(self, image):
        cv2.putText(image, "NO POSE DETECTED", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(image, "STEP BACK INTO FRAME", (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)

    def _draw_simple_overlay(self, image, metrics):
        h, _ = image.shape[:2]
        exercise = metrics.get("exercise", self.get_exercise())
        value = f"{metrics.get('hold_seconds', 0)}s" if exercise == "Plank" else metrics.get("reps", 0)
        cv2.putText(image, f"{exercise}: {value}", (20, h - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 122, 0), 2)
        cv2.putText(image, f"Form {metrics.get('form_score', 0)}/100", (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (139, 92, 246), 2)

    def _pose_status(self, landmarks, exercise):
        visibility = calculate_pose_visibility(landmarks)
        missing_parts = get_missing_body_parts(landmarks)

        upper_indices = [11, 12, 13, 14, 15, 16]
        lower_indices = [23, 24, 25, 26, 27, 28]
        upper_visible = sum(1 for idx in upper_indices if landmarks[idx].visibility >= 0.55) >= 4
        lower_visible = sum(1 for idx in lower_indices if landmarks[idx].visibility >= 0.55) >= 4

        if upper_visible and lower_visible:
            status = "Full body visible"
        elif exercise == "Push-ups" and upper_visible:
            status = "Upper body visible"
        elif exercise == "Squats" and lower_visible:
            status = "Lower body visible"
        else:
            status = "Missing body parts"

        return status, visibility, missing_parts

    def _debug_metrics(self, landmarks, process_start):
        elapsed = max(1e-6, time.perf_counter() - self._started_at)
        return {
            "last_frame_at": self._last_frame_at,
            "frame_timestamp_ms": self._frame_timestamps_ms,
            "fps": round(self._fps, 1),
            "input_fps": round(self._input_fps, 1),
            "processed_fps": round(self._processed_frame_count / elapsed, 1),
            "frame_count": self._frame_count,
            "skipped_frames": self._skipped_frames,
            "average_processing_ms": round((self._total_processing_ms + ((time.perf_counter() - process_start) * 1000.0)) / max(1, self._processed_frame_count + 1), 2),
            "pose_profile": self._pose_profile,
            "quality_profile": self._quality,
        }

    def recv(self, frame):
        image = np.asarray(cv2.flip(frame.to_ndarray(format="bgr24"), 1), dtype=np.uint8)
        self._mark_frame_received()
        process_start = time.perf_counter()

        if (self._frame_count % max(1, self._process_every_n_frames)) != 0:
            self._skipped_frames += 1
            return av.VideoFrame.from_ndarray(image, format="bgr24")

        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self._frame_timestamps_ms = int((time.perf_counter() - self._started_at) * 1000)
            result = self._pose.process(rgb_image)
            exercise = self.get_exercise()

            if result and result.pose_landmarks:
                landmarks = result.pose_landmarks.landmark
                pose_status, pose_visibility, missing_parts = self._pose_status(landmarks, exercise)
                camera_guidance = get_camera_guidance(landmarks)
                detector = self._detectors.get(exercise)

                if self.get_draw_pose_overlay():
                    self._draw_skeleton(image, landmarks)

                if detector:
                    raw_metrics = detector.process(landmarks)
                    metrics = standardize_detector_metrics(exercise, detector, raw_metrics)
                else:
                    metrics = standardize_detector_metrics(
                        exercise,
                        None,
                        {
                            "pose_detected": False,
                            "camera_status": "Detector unavailable",
                            "issue": "This exercise is not enabled in the public MVP.",
                        },
                    )

                metrics.update(
                    {
                        "exercise": exercise,
                        "selected_exercise": exercise,
                        "detected_exercise": exercise,
                        "exercise_confidence": 1.0,
                        "confidence": 1.0,
                        "pose_detected": True,
                        "pose_visibility": round(pose_visibility, 3),
                        "pose_visibility_score": round(pose_visibility, 3),
                        "camera_status": metrics.get("camera_status") or pose_status,
                        "camera_guidance": metrics.get("camera_guidance") or (camera_guidance[0] if camera_guidance else "Keep your body visible in frame."),
                        **self._debug_metrics(landmarks, process_start),
                    }
                )
                metrics["debug"] = {
                    **metrics.get("debug", {}),
                    "pose_status": pose_status,
                    "missing_body_parts": missing_parts,
                    "camera_guidance_messages": camera_guidance,
                }

                self._draw_simple_overlay(image, metrics)
                self.set_latest_metrics(metrics)
            else:
                self._draw_no_pose_warnings(image)
                self.set_latest_metrics(
                    standardize_detector_metrics(
                        self.get_exercise(),
                        None,
                        {
                            "pose_detected": False,
                            "camera_status": "Pose not detected",
                            "camera_guidance": "Move farther back, improve lighting, and keep your body in the camera frame.",
                            "issue": "Pose not detected.",
                            **self._debug_metrics([], process_start),
                            "debug": {"pose_status": "Pose detected: false"},
                        },
                    )
                )

            with self._lock:
                self._last_error = ""
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)

            self.set_latest_metrics(
                standardize_detector_metrics(
                    self.get_exercise(),
                    None,
                    {
                        "pose_detected": False,
                        "camera_status": "Camera processing error",
                        "camera_guidance": "Refresh the page and allow camera permission. Try Standard quality if this continues.",
                        "issue": "Camera processing error.",
                        "frame_error": str(exc),
                        **self._debug_metrics([], process_start),
                        "debug": {"last_error": str(exc)},
                    },
                )
            )
        finally:
            self._finish_processing(process_start)

        return av.VideoFrame.from_ndarray(image, format="bgr24")
