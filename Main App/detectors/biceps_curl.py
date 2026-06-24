import math
from core.base_exercise import BaseExercise
from services.vision.pose_utils import angle_from_indices, choose_best_side, get_landmark_visibility, smooth_value


class BicepsCurlDetector(BaseExercise):
    UP_THRESHOLD = 50
    DOWN_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    ELBOW_DRIFT_TOLERANCE = 0.06
    SWING_THRESHOLD = 15

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()
        self._shoulder_x_baseline = None

    def reset(self) -> None:
        self.reps = 0
        self.stage = None
        self._shoulder_x_baseline = None

    def process(self, landmarks) -> dict:
        _, side_points, visibility = choose_best_side(
            landmarks,
            [self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST],
            [self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST],
        )
        shoulder_idx, elbow_idx, wrist_idx = side_points
        elbow_angle = smooth_value("curl_elbow_angle", angle_from_indices(landmarks, shoulder_idx, elbow_idx, wrist_idx))

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[elbow_idx].visibility > self.MIN_VISIBILITY and landmarks[wrist_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if elbow_angle < self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle > self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        shoulder_x = landmarks[shoulder_idx].x
        elbow_x = landmarks[elbow_idx].x
        elbow_drift = abs(elbow_x - shoulder_x)

        if elbow_drift <= self.ELBOW_DRIFT_TOLERANCE:
            shoulder_status = "STABLE"
        else:
            shoulder_status = "ELBOW DRIFTING"

        shoulder_mid_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) / 2
        shoulder_mid_y = (landmarks[self.LEFT_SHOULDER].y + landmarks[self.RIGHT_SHOULDER].y) / 2

        hip_mid_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        hip_mid_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2

        dx = shoulder_mid_x - hip_mid_x
        dy = shoulder_mid_y - hip_mid_y

        torso_angle_from_vertical = self._safe_angle(dx, dy)

        if torso_angle_from_vertical <= self.SWING_THRESHOLD:
            swing_status = "NO SWING"
        else:
            swing_status = "SWINGING"

        pose_visibility = get_landmark_visibility(landmarks, [shoulder_idx, elbow_idx, wrist_idx, self.LEFT_HIP, self.RIGHT_HIP])
        issue = None if key_landmarks_visible else "Required body parts are not visible"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_status": shoulder_status,
            "swing_status": swing_status,
            "stage": self.stage or "setup",
            "landmark_confidence": round(visibility, 2),
            "camera_guidance": "Front or side view good" if key_landmarks_visible else "Keep shoulder, elbow, and wrist visible",
            "processing_status": "tracking" if key_landmarks_visible else "low visibility",
            "pose_detected": key_landmarks_visible,
            "pose_visibility": round(pose_visibility, 3),
            "camera_status": "Tracking" if key_landmarks_visible else "Adjust camera",
            "issue": issue,
            "is_valid_rep": key_landmarks_visible and self.stage == "down",
            "debug": {"required_body_parts": ["shoulders", "elbows", "wrists", "hips"]},
        }

    def _safe_angle(self, dx, dy):
        return math.degrees(math.atan2(abs(dx), abs(dy))) if dy != 0 else 0.0
    
