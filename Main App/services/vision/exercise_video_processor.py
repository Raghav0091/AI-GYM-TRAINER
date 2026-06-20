import os
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
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from detectors.jumping_jacks import JumpingJacksDetector
from detectors.high_knees import HighKneesDetector
from detectors.crunches import CrunchesDetector
from detectors.situps import SitUpsDetector
from detectors.plank import PlankDetector
from detectors.mountain_climbers import MountainClimbersDetector
from services.config.workout_config import POSE_CONNECTIONS


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

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
            "Jumping Jacks": JumpingJacksDetector(),
            "High Knees": HighKneesDetector(),
            "Crunches": CrunchesDetector(),
            "Sit-ups": SitUpsDetector(),
            "Plank": PlankDetector(),
            "Mountain Climbers": MountainClimbersDetector(),
        }

        self._frame_timestamps_ms = 0
        self._draw_pose_overlay = False

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

        try:
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            )

            self._frame_timestamps_ms = int((time.perf_counter() - self._started_at) * 1000)
            result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]

                if self.get_draw_pose_overlay():
                    self._draw_skeleton(image, landmarks)

                ex_type = self.get_exercise()
                detector = self._detectors.get(ex_type)

                if detector:
                    metrics = detector.process(landmarks)
                    metrics["pose_detected"] = True
                    metrics["selected_detector"] = ex_type
                    metrics["frame_timestamp_ms"] = self._frame_timestamps_ms
                    self._draw_overlays(image, metrics, ex_type)
                    self.set_latest_metrics(metrics)
            else:
                self._draw_no_pose_warnings(image)
                self.set_latest_metrics(
                    {
                        "pose_detected": False,
                        "processing_status": "no pose",
                        "camera_guidance": "Move farther back and keep your full body in frame.",
                        "selected_detector": self.get_exercise(),
                    }
                )
        except Exception as exc:
            self.set_latest_metrics(
                {
                    "pose_detected": False,
                    "processing_status": "frame error",
                    "frame_error": str(exc),
                    "selected_detector": self.get_exercise(),
                }
            )

        return av.VideoFrame.from_ndarray(image, format="bgr24")
