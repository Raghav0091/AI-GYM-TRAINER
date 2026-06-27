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
        self.reset()

    def reset(self):
        self.reps = 0
        self.stage = "hold"
        self._hold_started_at = None
        self._accumulated_hold_seconds = 0.0

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

        # ponytail: keep timer movement-tracking tolerant; strictness is handled in form scoring.
        valid_hold = key_visible

        if valid_hold and self._hold_started_at is None:
            self._hold_started_at = time.time()
            self.stage = "HOLD"
        elif not valid_hold and self._hold_started_at is not None:
            self._accumulated_hold_seconds += time.time() - self._hold_started_at
            self._hold_started_at = None
            self.stage = "PAUSED"

        active_seconds = time.time() - self._hold_started_at if self._hold_started_at is not None else 0
        hold_seconds = int(self._accumulated_hold_seconds + active_seconds)
        self.reps = hold_seconds

        issue = None
        if not key_visible:
            issue = "Required body parts are not visible"
        elif hip_status == "SAGGING":
            issue = "Lift your hips slightly and brace your core."
        elif hip_status == "PIKED UP":
            issue = "Lower your hips until your body forms a straight line."
        elif body_alignment == "POOR FORM":
            issue = "Keep your shoulders, hips, and ankles aligned."

        return {
            "reps": 0,
            "hold_seconds": hold_seconds,
            "body_alignment": body_alignment,
            "body_alignment_angle": int(body_angle),
            "hip_status": hip_status,
            "stage": self.stage,
            "issue": issue,
            "is_valid_rep": False,
            "camera_status": "Tracking" if key_visible else "Adjust camera",
            "pose_detected": key_visible,
            "pose_visibility": round(sum(landmarks[idx].visibility for idx in [shoulder_idx, hip_idx, ankle_idx]) / 3, 3),
            "camera_guidance": "Side view is best for plank" if key_visible else "Show shoulders, hips, and ankles",
            "processing_status": "tracking" if key_visible else "low visibility",
            "debug": {
                "required_body_parts": ["shoulders", "hips", "ankles"],
                "body_alignment_angle": int(body_angle),
                "hip_status": hip_status,
                "hold_seconds": hold_seconds,
                "pose_visibility": round(sum(landmarks[idx].visibility for idx in [shoulder_idx, hip_idx, ankle_idx]) / 3, 3),
                "issue": issue,
            },
        }
