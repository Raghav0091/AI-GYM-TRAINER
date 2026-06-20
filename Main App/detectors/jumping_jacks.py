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

    def reset(self):
        self.reps = 0
        self.stage = "closed"
        self.open_score = 0
        self.closed_score = 0

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
            self.open_score += 1
            self.closed_score = 0
        elif key_visible and hands_down and feet_closed:
            self.closed_score += 1
            self.open_score = 0
        elif key_visible:
            self.open_score = max(0, self.open_score - 1)
            self.closed_score = max(0, self.closed_score - 1)

        if self.open_score >= 1 and self.stage == "closed":
            self.stage = "open"

        if self.closed_score >= 1 and self.stage == "open":
            self.stage = "closed"
            self.reps += 1
            self.closed_score = 0

        arm_status = "HANDS UP" if hands_overhead else "RAISE ARMS"
        foot_status = "FEET APART" if feet_apart else "FEET TOGETHER"

        return {
            "reps": self.reps,
            "arm_status": arm_status,
            "foot_status": foot_status,
            "jumping_jack_stage": self.stage,
        }
