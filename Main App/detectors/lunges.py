from core.base_exercise import BaseExercise
from services.vision.pose_utils import angle_from_indices, get_landmark_visibility, smooth_value


class LungesDetector(BaseExercise):
    DOWN_THRESHOLD = 100
    UP_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    BALANCE_TOLERANCE = 0.10

    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        left_knee_angle = angle_from_indices(landmarks, self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE)
        right_knee_angle = angle_from_indices(landmarks, self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE)

        if left_knee_angle <= right_knee_angle:
            front_knee_angle = left_knee_angle
            front_hip_idx = self.LEFT_HIP
            front_knee_idx = self.LEFT_KNEE
            front_ankle_idx = self.LEFT_ANKLE
            shoulder_idx_for_torso = self.LEFT_SHOULDER
        else:
            front_knee_angle = right_knee_angle
            front_hip_idx = self.RIGHT_HIP
            front_knee_idx = self.RIGHT_KNEE
            front_ankle_idx = self.RIGHT_ANKLE
            shoulder_idx_for_torso = self.RIGHT_SHOULDER

        visibility = get_landmark_visibility(landmarks, [front_hip_idx, front_knee_idx, front_ankle_idx, shoulder_idx_for_torso])
        front_knee_angle = smooth_value("lunge_front_knee_angle", front_knee_angle)
        key_landmarks_visible = visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if front_knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if front_knee_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        torso_angle = smooth_value("lunge_torso_angle", angle_from_indices(landmarks, shoulder_idx_for_torso, front_hip_idx, front_knee_idx))

        shoulder_mid_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) / 2
        hip_mid_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        lateral_offset = abs(shoulder_mid_x - hip_mid_x)

        if lateral_offset <= self.BALANCE_TOLERANCE:
            balance_status = "BALANCED"
        else:
            balance_status = "OFF BALANCE"

        issue = None if key_landmarks_visible else "Required body parts are not visible"
        return {
            "reps": self.reps,
            "front_knee_angle": int(front_knee_angle),
            "torso_angle": int(torso_angle),
            "balance_status": balance_status,
            "stage": self.stage or "setup",
            "landmark_confidence": round(visibility, 2),
            "camera_guidance": "Side view good" if key_landmarks_visible else "Show hips, knees, ankles, and torso",
            "processing_status": "tracking" if key_landmarks_visible else "low visibility",
            "pose_detected": key_landmarks_visible,
            "pose_visibility": round(visibility, 3),
            "camera_status": "Tracking" if key_landmarks_visible else "Adjust camera",
            "issue": issue,
            "is_valid_rep": key_landmarks_visible and self.stage == "up",
            "debug": {"required_body_parts": ["hips", "knees", "ankles"]},
        }
    
