from core.base_exercise import BaseExercise
from services.vision.pose_utils import angle_from_indices, choose_best_side, get_landmark_visibility, smooth_value


class ShoulderPressDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90
    MIN_VISIBILITY = 0.7

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        _, side_points, visibility = choose_best_side(
            landmarks,
            [self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST, self.LEFT_HIP, self.LEFT_KNEE],
            [self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST, self.RIGHT_HIP, self.RIGHT_KNEE],
        )
        shoulder_idx, elbow_idx, wrist_idx, hip_idx, knee_idx = side_points
        elbow_angle = smooth_value("press_elbow_angle", angle_from_indices(landmarks, shoulder_idx, elbow_idx, wrist_idx))

        key_landmarks_visible = get_landmark_visibility(landmarks, [shoulder_idx, elbow_idx, wrist_idx]) > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if elbow_angle > self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle < self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        if elbow_angle >= self.UP_THRESHOLD:
            extension_status = "FULL EXTENSION"
        elif elbow_angle >= 130:
            extension_status = "NEARLY EXTENDED"
        elif elbow_angle >= self.DOWN_THRESHOLD:
            extension_status = "PRESSING"
        else:
            extension_status = "START POSITION"

        back_angle = smooth_value("press_back_angle", angle_from_indices(landmarks, shoulder_idx, hip_idx, knee_idx))

        if back_angle >= 160:
            back_arch_status = "Neutral"
        elif back_angle >= 140:
            back_arch_status = "Slight Arch"
        else:
            back_arch_status = "Excessive Arch"

        issue = None if key_landmarks_visible else "Required body parts are not visible"
        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status,
            "stage": self.stage or "setup",
            "landmark_confidence": round(visibility, 2),
            "camera_guidance": "Front view good" if key_landmarks_visible else "Keep shoulders, elbows, and wrists visible",
            "processing_status": "tracking" if key_landmarks_visible else "low visibility",
            "pose_detected": key_landmarks_visible,
            "pose_visibility": round(get_landmark_visibility(landmarks, [shoulder_idx, elbow_idx, wrist_idx]), 3),
            "camera_status": "Tracking" if key_landmarks_visible else "Adjust camera",
            "issue": issue,
            "is_valid_rep": key_landmarks_visible and self.stage == "down",
            "debug": {"required_body_parts": ["shoulders", "elbows", "wrists"]},
        }
    
