import cv2
import av
import numpy as np
import mediapipe as mp
import threading
import time
from pathlib import Path
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from services.config.workout_config import POSE_CONNECTIONS
from services.vision.detector_base import standardize_detector_metrics
from services.vision.detector_registry import build_detectors, detector_available
from services.vision.exercise_classifier import HeuristicExerciseClassifier
from services.vision.pose_data_collector import PoseDataCollector
from services.vision.pose_normalizer import get_pose_features
from services.vision.prediction_smoother import PredictionSmoother


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"
        self._started_at = time.perf_counter()

        app_root = Path(__file__).resolve().parents[2]
        model_path = str(app_root / "ml_models" / "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.55,
            min_pose_presence_confidence=0.55,
            min_tracking_confidence=0.55,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = build_detectors()
        self._classifier = HeuristicExerciseClassifier()
        self._prediction_smoother = PredictionSmoother()
        self._pose_data_collector = PoseDataCollector()

        self._frame_timestamps_ms = 0
        self._draw_pose_overlay = False
        self._auto_detect_enabled = False
        self._pose_data_collection_enabled = False
        self._collector_context = {}
        self._last_error = ""
        self._last_frame_at = 0.0
        self._frame_count = 0
        self._fps = 0.0
        self._last_fps_check_at = time.perf_counter()
        self._last_fps_frame_count = 0

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def set_draw_pose_overlay(self, enabled):
        with self._lock:
            self._draw_pose_overlay = bool(enabled)

    def get_draw_pose_overlay(self):
        with self._lock:
            return self._draw_pose_overlay

    def set_auto_detect_enabled(self, enabled):
        with self._lock:
            changed = self._auto_detect_enabled != bool(enabled)
            self._auto_detect_enabled = bool(enabled)

        if changed:
            self._prediction_smoother.reset()

    def get_auto_detect_enabled(self):
        with self._lock:
            return self._auto_detect_enabled

    def set_pose_data_collection(self, enabled, context=None):
        with self._lock:
            self._pose_data_collection_enabled = bool(enabled)
            self._collector_context = dict(context or {})

    def get_pose_data_collection(self):
        with self._lock:
            return self._pose_data_collection_enabled, dict(self._collector_context)

    def get_debug_snapshot(self):
        with self._lock:
            detector = self._detectors.get(self._exercise_type)
            return {
                "exercise": self._exercise_type,
                "detector_class": detector.__class__.__name__ if detector else "Unavailable",
                "last_error": self._last_error,
                "last_frame_at": self._last_frame_at,
                "frame_timestamp_ms": self._frame_timestamps_ms,
                "fps": round(self._fps, 1),
                "auto_detect_enabled": self._auto_detect_enabled,
                "using_tflite": self._classifier.using_tflite,
            }

    def _mark_frame_processed(self):
        now = time.perf_counter()
        wall_now = time.time()

        with self._lock:
            self._last_frame_at = wall_now
            self._frame_count += 1

            elapsed = now - self._last_fps_check_at
            if elapsed >= 1.0:
                frames = self._frame_count - self._last_fps_frame_count
                self._fps = frames / elapsed
                self._last_fps_check_at = now
                self._last_fps_frame_count = self._frame_count

    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    (0, 186, 255),
                    3,
                    cv2.LINE_AA,
                )

        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    5,
                    (255, 122, 0),
                    -1
                )

    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        if ex_type == "Squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Biceps Curls (Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunge_overlays(img, metrics)
        elif ex_type == "Jumping Jacks":
            self._draw_jumping_jack_overlays(img, metrics)
        elif ex_type == "High Knees":
            self._draw_high_knee_overlays(img, metrics)
        elif ex_type == "Crunches":
            self._draw_crunch_overlays(img, metrics)
        elif ex_type == "Sit-ups":
            self._draw_situp_overlays(img, metrics)
        elif ex_type == "Plank":
            self._draw_plank_overlays(img, metrics)
        elif ex_type == "Mountain Climbers":
            self._draw_mountain_climber_overlays(img, metrics)


    def _draw_squats_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"DEPTH: {metrics['depth_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BODY: {metrics['body_alignment']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"SWING: {metrics['swing_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"EXT: {metrics['extension_status']} | BACK: {metrics['back_arch_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BALANCE: {metrics['balance_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_jumping_jack_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"ARMS: {metrics['arm_status']} | FEET: {metrics['foot_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_high_knee_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"KNEES: {metrics['knee_height']} | PACE: {metrics['pace_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_crunch_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"RANGE: {metrics['range_status']} | NECK: {metrics['neck_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_situp_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"RANGE: {metrics['range_status']} | CONTROL: {metrics['control_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_plank_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"HOLD: {metrics['hold_seconds']}s | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_mountain_climber_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"KNEE: {metrics['knee_drive']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def recv(self, frame):
        image = np.asarray(cv2.flip(frame.to_ndarray(format="bgr24"), 1), dtype=np.uint8)
        self._mark_frame_processed()

        try:
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            )

            self._frame_timestamps_ms = int((time.perf_counter() - self._started_at) * 1000)
            result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]
                pose_features = get_pose_features(landmarks)
                auto_detect_enabled = self.get_auto_detect_enabled()
                selected_exercise = self.get_exercise()
                classifier_prediction = self._classifier.predict(pose_features)
                smoothed_prediction = self._prediction_smoother.update(classifier_prediction)

                if self.get_draw_pose_overlay():
                    self._draw_skeleton(image, landmarks)

                detected_exercise = smoothed_prediction.get("exercise", "Unknown")
                exercise_confidence = float(smoothed_prediction.get("confidence", 0.0) or 0.0)
                pose_visibility_score = float(pose_features.get("visibility_score", 0.0) or 0.0)
                ex_type = selected_exercise

                if auto_detect_enabled:
                    if detected_exercise != "Unknown" and exercise_confidence >= 0.55 and detector_available(detected_exercise):
                        ex_type = detected_exercise
                    else:
                        metrics = standardize_detector_metrics(
                            selected_exercise,
                            None,
                            {
                                "pose_detected": True,
                                "selected_exercise": selected_exercise,
                                "detected_exercise": "Unknown",
                                "exercise_confidence": exercise_confidence,
                                "auto_detect_enabled": True,
                                "pose_visibility_score": pose_visibility_score,
                                "detector_name": "Waiting for confident prediction",
                                "camera_status": "Exercise not detected",
                                "processing_status": "auto detect waiting",
                                "camera_guidance": "Move farther back and keep your full body visible.",
                                "issue": "Exercise not detected. Keep full body visible.",
                                "frame_timestamp_ms": self._frame_timestamps_ms,
                                "last_frame_at": self._last_frame_at,
                                "fps": round(self._fps, 1),
                                "debug": {
                                    "classifier_scores": smoothed_prediction.get("scores", {}),
                                    "raw_prediction": classifier_prediction,
                                    "using_tflite": self._classifier.using_tflite,
                                },
                            },
                        )
                        self.set_latest_metrics(metrics)
                        self._maybe_collect_pose_sample(
                            pose_features,
                            metrics,
                            selected_exercise,
                            "Unknown",
                            exercise_confidence,
                        )
                        return av.VideoFrame.from_ndarray(image, format="bgr24")

                detector = self._detectors.get(ex_type)

                if detector:
                    metrics = standardize_detector_metrics(
                        ex_type,
                        detector,
                        detector.process(landmarks),
                    )
                    metrics["pose_detected"] = True
                    metrics["selected_exercise"] = selected_exercise
                    metrics["selected_detector"] = ex_type
                    metrics["detected_exercise"] = detected_exercise if auto_detect_enabled else ex_type
                    metrics["exercise_confidence"] = exercise_confidence if auto_detect_enabled else 1.0
                    metrics["confidence"] = metrics["exercise_confidence"]
                    metrics["auto_detect_enabled"] = auto_detect_enabled
                    metrics["pose_visibility_score"] = pose_visibility_score
                    metrics["detector_name"] = detector.__class__.__name__
                    metrics["frame_timestamp_ms"] = self._frame_timestamps_ms
                    metrics["last_frame_at"] = self._last_frame_at
                    metrics["fps"] = round(self._fps, 1)
                    metrics["debug"] = {
                        **metrics.get("debug", {}),
                        "classifier_scores": smoothed_prediction.get("scores", {}),
                        "raw_prediction": classifier_prediction,
                        "using_tflite": self._classifier.using_tflite,
                    }
                    self._draw_overlays(image, metrics, ex_type)
                    self.set_latest_metrics(metrics)
                    self._maybe_collect_pose_sample(
                        pose_features,
                        metrics,
                        selected_exercise,
                        metrics["detected_exercise"],
                        metrics["exercise_confidence"],
                    )
                else:
                    self.set_latest_metrics(
                        standardize_detector_metrics(
                            ex_type,
                            None,
                            {
                                "pose_detected": False,
                                "selected_exercise": selected_exercise,
                                "detected_exercise": detected_exercise,
                                "exercise_confidence": exercise_confidence,
                                "auto_detect_enabled": auto_detect_enabled,
                                "pose_visibility_score": pose_visibility_score,
                                "camera_status": "Detector unavailable",
                                "processing_status": "detector unavailable",
                                "issue": "Detector not available for this exercise yet.",
                                "detector_name": "Unavailable",
                                "last_frame_at": self._last_frame_at,
                                "fps": round(self._fps, 1),
                            },
                        )
                    )
            else:
                self._draw_no_pose_warnings(image)
                self.set_latest_metrics(
                    {
                        "pose_detected": False,
                        "processing_status": "no pose",
                        "camera_guidance": "Move farther back and keep your full body in frame.",
                        "selected_detector": self.get_exercise(),
                        "selected_exercise": self.get_exercise(),
                        "detected_exercise": "Unknown",
                        "exercise_confidence": 0.0,
                        "auto_detect_enabled": self.get_auto_detect_enabled(),
                        "pose_visibility_score": 0.0,
                        "detector_name": "Unavailable",
                        "last_frame_at": self._last_frame_at,
                        "fps": round(self._fps, 1),
                    }
                )
        except Exception as exc:
            with self._lock:
                self._last_error = str(exc)

            self.set_latest_metrics(
                {
                    "pose_detected": False,
                    "processing_status": "frame error",
                    "frame_error": str(exc),
                    "selected_detector": self.get_exercise(),
                    "selected_exercise": self.get_exercise(),
                    "detected_exercise": "Unknown",
                    "exercise_confidence": 0.0,
                    "auto_detect_enabled": self.get_auto_detect_enabled(),
                    "pose_visibility_score": 0.0,
                    "detector_name": "Unavailable",
                    "last_frame_at": self._last_frame_at,
                    "fps": round(self._fps, 1),
                }
            )
        else:
            with self._lock:
                self._last_error = ""

        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def _maybe_collect_pose_sample(self, pose_features, metrics, selected_exercise, detected_exercise, confidence):
        enabled, context = self.get_pose_data_collection()
        if not enabled:
            return

        self._pose_data_collector.save_sample(
            {
                "user_id": context.get("user_id"),
                "username": context.get("username"),
                "selected_exercise": selected_exercise,
                "detected_exercise": detected_exercise,
                "confidence": confidence,
                "feature_vector": pose_features.get("feature_vector", []),
                "pose_visibility_score": pose_features.get("visibility_score", 0.0),
                "reps": metrics.get("reps", 0),
                "stage": metrics.get("stage", "setup"),
                "form_score": metrics.get("form_score", 0),
                "issue": metrics.get("issue"),
            }
        )
