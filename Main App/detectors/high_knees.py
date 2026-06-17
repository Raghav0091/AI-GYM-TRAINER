from core.base_exercise import BaseExercise


class HighKneesDetector(BaseExercise):
    MIN_VISIBILITY = 0.65
    KNEE_LIFT_THRESHOLD = 0.06

    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_knee_y = landmarks[self.LEFT_KNEE].y
        right_knee_y = landmarks[self.RIGHT_KNEE].y
        hip_line_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2

        left_lifted = left_knee_y < hip_line_y + self.KNEE_LIFT_THRESHOLD
        right_lifted = right_knee_y < hip_line_y + self.KNEE_LIFT_THRESHOLD

        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [self.LEFT_HIP, self.RIGHT_HIP, self.LEFT_KNEE, self.RIGHT_KNEE]
        )

        active_side = None

        if key_visible:
            if left_lifted and not right_lifted:
                active_side = "left"
            elif right_lifted and not left_lifted:
                active_side = "right"

            if active_side and active_side != self.stage:
                self.stage = active_side
                self.reps += 1

        knee_height = "GOOD HEIGHT" if left_lifted or right_lifted else "LOW KNEES"
        pace_status = "ALTERNATING" if active_side else "RESET"

        return {
            "reps": self.reps,
            "knee_height": knee_height,
            "pace_status": pace_status,
            "active_knee": active_side or "none",
        }
