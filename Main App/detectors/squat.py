from core.base_exercise import BaseExercise
from services.vision.pose_utils import angle_from_indices, choose_best_side, get_landmark_visibility, smooth_value


class SquatDetector(BaseExercise):
    DOWN_THRESHOLD = 100   
    UP_THRESHOLD = 160     
    MIN_VISIBILITY = 0.7

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

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        _, side_points, visibility = choose_best_side(
            landmarks,
            [self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE, self.LEFT_SHOULDER],
            [self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE, self.RIGHT_SHOULDER],
        )
        hip_idx, knee_idx, ankle_idx, shoulder_idx = side_points
        knee_angle = smooth_value("squat_knee_angle", angle_from_indices(landmarks, hip_idx, knee_idx, ankle_idx))
        back_angle = smooth_value("squat_back_angle", angle_from_indices(landmarks, shoulder_idx, hip_idx, knee_idx))
        full_body_visibility = get_landmark_visibility(landmarks, [hip_idx, knee_idx, ankle_idx, shoulder_idx])
        key_landmark_visible = full_body_visibility >= self.MIN_VISIBILITY

        if key_landmark_visible:
            if knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        if self.stage == "down":
            depth_status = "GOOD DEPTH" if knee_angle <= self.DOWN_THRESHOLD else "TOO HIGH"
        elif self.stage == "up":
            depth_status = "STANDING"
        else:
            depth_status = "N/A"

        return {
            "reps": self.reps,
            "knee_angle": int(knee_angle),
            "back_angle": int(back_angle),
            "depth_status": depth_status,
            "stage": self.stage or "setup",
            "landmark_confidence": round(visibility, 2),
            "camera_guidance": "Full body visible" if key_landmark_visible else "Move back so hips, knees, and ankles are visible",
            "processing_status": "tracking" if key_landmark_visible else "low visibility",
        }
    
