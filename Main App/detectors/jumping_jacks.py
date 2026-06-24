from core.base_exercise import BaseExercise


class JumpingJacksDetector(BaseExercise):
    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self.reps = 0
        self.stage = "closed"
        self._open_frames = 0
        self._closed_frames = 0

    def process(self, landmarks):
        shoulder_width = abs(landmarks[self.LEFT_SHOULDER].x - landmarks[self.RIGHT_SHOULDER].x)
        ankle_width = abs(landmarks[self.LEFT_ANKLE].x - landmarks[self.RIGHT_ANKLE].x)
        hip_width = abs(landmarks[self.LEFT_HIP].x - landmarks[self.RIGHT_HIP].x)
        wrist_height = min(landmarks[self.LEFT_WRIST].y, landmarks[self.RIGHT_WRIST].y)
        shoulder_height = min(landmarks[self.LEFT_SHOULDER].y, landmarks[self.RIGHT_SHOULDER].y)
        hands_overhead = wrist_height < shoulder_height + 0.04
        feet_apart = ankle_width > max(shoulder_width * 1.28, hip_width * 1.75)
        feet_closed = ankle_width < max(shoulder_width * 1.05, hip_width * 1.35)
        hands_down = (
            landmarks[self.LEFT_WRIST].y > landmarks[self.LEFT_HIP].y - 0.08
            and landmarks[self.RIGHT_WRIST].y > landmarks[self.RIGHT_HIP].y - 0.08
        )

        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_WRIST, self.RIGHT_WRIST, self.LEFT_ANKLE, self.RIGHT_ANKLE]
        )

        if key_visible and hands_overhead and feet_apart:
            self._open_frames += 1
            self._closed_frames = 0
        elif key_visible and hands_down and feet_closed:
            self._closed_frames += 1
            self._open_frames = 0
        elif key_visible:
            self._open_frames = max(0, self._open_frames - 1)
            self._closed_frames = max(0, self._closed_frames - 1)

        if self._open_frames >= 1 and self.stage == "closed":
            self.stage = "open"

        if self._closed_frames >= 1 and self.stage == "open":
            self.stage = "closed"
            self.reps += 1
            self._closed_frames = 0

        arm_status = "HANDS UP" if hands_overhead else "RAISE ARMS"
        foot_status = "FEET APART" if feet_apart else "FEET TOGETHER"
        visibility = sum(landmarks[idx].visibility for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_WRIST, self.RIGHT_WRIST, self.LEFT_HIP, self.RIGHT_HIP, self.LEFT_ANKLE, self.RIGHT_ANKLE]) / 8
        issue = None if key_visible else "Required body parts are not visible"

        return {
            "reps": self.reps,
            "arm_status": arm_status,
            "foot_status": foot_status,
            "jumping_jack_stage": self.stage,
            "stage": self.stage,
            "pose_detected": key_visible,
            "pose_visibility": round(visibility, 3),
            "camera_status": "Tracking" if key_visible else "Adjust camera",
            "issue": issue,
            "camera_guidance": "Front-facing full body view is best" if key_visible else "Show shoulders, wrists, hips, and ankles",
            "processing_status": "tracking" if key_visible else "low visibility",
            "is_valid_rep": key_visible and self.stage == "closed",
            "debug": {"required_body_parts": ["shoulders", "wrists", "hips", "ankles"]},
        }
