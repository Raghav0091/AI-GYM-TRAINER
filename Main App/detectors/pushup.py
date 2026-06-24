from core.base_exercise import BaseExercise
from services.vision.pose_utils import angle_from_indices, choose_best_side, get_landmark_visibility, smooth_value


class PushUpDetector(BaseExercise):
    DOWN_THRESHOLD = 90
    UP_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    HIP_SAG_TOLERANCE = 0.08

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None

    def process(self, landmarks) -> dict:
        _, side_points, visibility = choose_best_side(
            landmarks,
            [self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST, self.LEFT_HIP, self.LEFT_ANKLE],
            [self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST, self.RIGHT_HIP, self.RIGHT_ANKLE],
        )
        shoulder_idx, elbow_idx, wrist_idx, hip_idx, ankle_idx = side_points
        elbow_angle = smooth_value("pushup_elbow_angle", angle_from_indices(landmarks, shoulder_idx, elbow_idx, wrist_idx))
        body_angle = smooth_value("pushup_body_angle", angle_from_indices(landmarks, shoulder_idx, hip_idx, ankle_idx))

        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        hip_y = landmarks[hip_idx].y

        expected_hip_y = (shoulder_y + ankle_y) / 2
        hip_deviation = hip_y - expected_hip_y

        key_landmarks_visible = get_landmark_visibility(landmarks, [shoulder_idx, elbow_idx, wrist_idx, hip_idx, ankle_idx]) > self.MIN_VISIBILITY
        
        if key_landmarks_visible:
            if elbow_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if elbow_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        if body_angle > 160:
            body_alignment = "Straight"
        elif body_angle > 140:
            body_alignment = "Slight Bend"
        else:
            body_alignment = "Poor Form"

        if abs(hip_deviation) <= self.HIP_SAG_TOLERANCE:
            hip_status = "LEVEL"
        elif hip_deviation > self.HIP_SAG_TOLERANCE:
            hip_status = "SAGGING"
        else:
            hip_status = "PIKED UP"

        issue = None if key_landmarks_visible else "Required body parts are not visible"
        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "body_alignment": body_alignment,
            "hip_status": hip_status,
            "stage": self.stage or "setup",
            "landmark_confidence": round(visibility, 2),
            "camera_guidance": "Side view good" if key_landmarks_visible else "Show shoulders, wrists, hips, and ankles",
            "processing_status": "tracking" if key_landmarks_visible else "low visibility",
            "pose_detected": key_landmarks_visible,
            "pose_visibility": round(get_landmark_visibility(landmarks, [shoulder_idx, elbow_idx, wrist_idx, hip_idx, ankle_idx]), 3),
            "camera_status": "Tracking" if key_landmarks_visible else "Adjust camera",
            "issue": issue,
            "is_valid_rep": key_landmarks_visible and self.stage == "up",
            "debug": {"required_body_parts": ["shoulders", "elbows", "wrists", "hips", "ankles"]},
        }
    
