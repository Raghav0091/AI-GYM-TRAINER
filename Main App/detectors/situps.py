from core.base_exercise import BaseExercise


class SitUpsDetector(BaseExercise):
    UP_THRESHOLD = 95
    DOWN_THRESHOLD = 145
    MIN_VISIBILITY = 0.65

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def reset(self):
        self.reps = 0
        self.stage = "down"

    def process(self, landmarks):
        left_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
        )
        right_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_SHOULDER),
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
        )

        torso_angle = min(left_angle, right_angle)
        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_HIP, self.RIGHT_HIP]
        )

        if key_visible and torso_angle < self.UP_THRESHOLD:
            self.stage = "up"

        if key_visible and torso_angle > self.DOWN_THRESHOLD and self.stage == "up":
            self.stage = "down"
            self.reps += 1

        range_status = "FULL SIT-UP" if torso_angle < self.UP_THRESHOLD else "LOW RANGE"
        control_status = "CONTROLLED" if key_visible else "CHECK POSITION"

        return {
            "reps": self.reps,
            "torso_angle": int(torso_angle),
            "range_status": range_status,
            "control_status": control_status,
        }
