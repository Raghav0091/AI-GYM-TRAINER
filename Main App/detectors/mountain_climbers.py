from core.base_exercise import BaseExercise


class MountainClimbersDetector(BaseExercise):
    MIN_VISIBILITY = 0.65
    KNEE_DRIVE_THRESHOLD = 0.16

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
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
        left_drive = abs(landmarks[self.LEFT_KNEE].x - landmarks[self.LEFT_HIP].x) < self.KNEE_DRIVE_THRESHOLD
        right_drive = abs(landmarks[self.RIGHT_KNEE].x - landmarks[self.RIGHT_HIP].x) < self.KNEE_DRIVE_THRESHOLD

        shoulder_mid_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2
        hip_mid_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2
        plank_level = abs(shoulder_mid_y - hip_mid_y)

        key_visible = all(
            landmarks[idx].visibility > self.MIN_VISIBILITY
            for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_HIP, self.RIGHT_HIP, self.LEFT_KNEE, self.RIGHT_KNEE]
        )

        active_side = None

        if key_visible:
            if left_drive and not right_drive:
                active_side = "left"
            elif right_drive and not left_drive:
                active_side = "right"

            if active_side and active_side != self.stage:
                self.stage = active_side
                self.reps += 1

        knee_drive = "GOOD DRIVE" if active_side else "LOW DRIVE"
        hip_status = "LEVEL" if plank_level <= 0.16 else "HIPS HIGH"
        visibility = sum(landmarks[idx].visibility for idx in [self.LEFT_SHOULDER, self.RIGHT_SHOULDER, self.LEFT_HIP, self.RIGHT_HIP, self.LEFT_KNEE, self.RIGHT_KNEE, self.LEFT_ANKLE, self.RIGHT_ANKLE]) / 8
        issue = None if key_visible else "Required body parts are not visible"

        return {
            "reps": self.reps,
            "knee_drive": knee_drive,
            "hip_status": hip_status,
            "active_knee": active_side or "none",
            "stage": self.stage or "setup",
            "pose_detected": key_visible,
            "pose_visibility": round(visibility, 3),
            "camera_status": "Tracking" if key_visible else "Adjust camera",
            "issue": issue,
            "camera_guidance": "Side view is best for mountain climbers" if key_visible else "Show shoulders, hips, knees, and ankles",
            "processing_status": "tracking" if key_visible else "low visibility",
            "is_valid_rep": key_visible and bool(active_side),
            "debug": {"required_body_parts": ["shoulders", "hips", "knees", "ankles"]},
        }
