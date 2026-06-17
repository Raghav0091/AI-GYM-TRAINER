import time
from core.base_exercise import BaseExercise


class PlankDetector(BaseExercise):
    MIN_VISIBILITY = 0.65
    HIP_SAG_TOLERANCE = 0.08

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self._started_at = None

    def reset(self):
        self.reps = 0
        self.stage = "hold"
        self._started_at = None

    def process(self, landmarks):
        shoulder_idx = self.LEFT_SHOULDER if landmarks[self.LEFT_SHOULDER].visibility >= landmarks[self.RIGHT_SHOULDER].visibility else self.RIGHT_SHOULDER
        hip_idx = self.LEFT_HIP if shoulder_idx == self.LEFT_SHOULDER else self.RIGHT_HIP
        ankle_idx = self.LEFT_ANKLE if shoulder_idx == self.LEFT_SHOULDER else self.RIGHT_ANKLE

        body_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        hip_y = landmarks[hip_idx].y
        expected_hip_y = (shoulder_y + ankle_y) / 2
        hip_deviation = hip_y - expected_hip_y

        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [shoulder_idx, hip_idx, ankle_idx]
        )

        if key_visible and self._started_at is None:
            self._started_at = time.time()

        if key_visible and self._started_at is not None:
            self.reps = int(time.time() - self._started_at)

        if body_angle > 160:
            body_alignment = "STRAIGHT"
        elif body_angle > 140:
            body_alignment = "SLIGHT BEND"
        else:
            body_alignment = "POOR FORM"

        if abs(hip_deviation) <= self.HIP_SAG_TOLERANCE:
            hip_status = "LEVEL"
        elif hip_deviation > self.HIP_SAG_TOLERANCE:
            hip_status = "SAGGING"
        else:
            hip_status = "PIKED UP"

        return {
            "reps": self.reps,
            "hold_seconds": self.reps,
            "body_alignment": body_alignment,
            "hip_status": hip_status,
        }
