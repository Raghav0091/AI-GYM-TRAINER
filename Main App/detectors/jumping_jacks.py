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

    def process(self, landmarks):
        shoulder_width = abs(landmarks[self.LEFT_SHOULDER].x - landmarks[self.RIGHT_SHOULDER].x)
        ankle_width = abs(landmarks[self.LEFT_ANKLE].x - landmarks[self.RIGHT_ANKLE].x)
        hands_overhead = (
            landmarks[self.LEFT_WRIST].y < landmarks[self.LEFT_SHOULDER].y
            and landmarks[self.RIGHT_WRIST].y < landmarks[self.RIGHT_SHOULDER].y
        )
        feet_apart = ankle_width > shoulder_width * 1.55

        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_WRIST, self.RIGHT_WRIST, self.LEFT_ANKLE, self.RIGHT_ANKLE]
        )

        if key_visible and hands_overhead and feet_apart:
            self.stage = "open"

        if key_visible and not hands_overhead and not feet_apart and self.stage == "open":
            self.stage = "closed"
            self.reps += 1

        arm_status = "HANDS UP" if hands_overhead else "RAISE ARMS"
        foot_status = "FEET APART" if feet_apart else "FEET TOGETHER"

        return {
            "reps": self.reps,
            "arm_status": arm_status,
            "foot_status": foot_status,
            "jumping_jack_stage": self.stage,
        }
