import math
from pathlib import Path

from services.vision.detector_registry import list_supported_exercises
from services.vision.pose_quality import (
    calculate_pose_visibility,
    has_full_body,
    has_lower_body,
    has_upper_body,
)


UNKNOWN_EXERCISE = "Unknown"
CONFIDENCE_THRESHOLD = 0.60


class HeuristicExerciseClassifier:
    """Heuristic auto-detect classifier (rule-based, not a trained model)."""

    def __init__(self, model_path=None):
        app_root = Path(__file__).resolve().parents[2]
        self.model_path = Path(model_path) if model_path else app_root / "ml_models" / "exercise_classifier.tflite"
        self.using_tflite = self.model_path.exists()

        # Future TFLite classifier hook. When exercise_classifier.tflite exists,
        # load it here and replace heuristic scores with model probabilities.

    def predict(self, pose_features):
        if not pose_features or not pose_features.get("pose_detected"):
            return _unknown_prediction()

        raw = pose_features.get("raw_keypoints", {})
        normalized = pose_features.get("normalized_keypoints", {})
        landmarks = pose_features.get("landmarks")
        visibility = float(calculate_pose_visibility(landmarks)) if landmarks is not None else float(pose_features.get("visibility_score", 0.0) or 0.0)
        upper_visible = has_upper_body(landmarks) if landmarks is not None else visibility >= 0.45
        lower_visible = has_lower_body(landmarks) if landmarks is not None else visibility >= 0.45
        full_visible = has_full_body(landmarks) if landmarks is not None else visibility >= 0.45

        if visibility < 0.40 or not (upper_visible or lower_visible):
            return _unknown_prediction(visibility=visibility)

        scores = {exercise: 0.0 for exercise in list_supported_exercises()}

        torso_angle = _torso_angle(raw)
        body_horizontal = _score_range(abs(torso_angle), 70, 25)
        body_upright = _score_range(abs(torso_angle), 0, 35)
        left_knee = _joint_angle(raw, "left_hip", "left_knee", "left_ankle")
        right_knee = _joint_angle(raw, "right_hip", "right_knee", "right_ankle")
        avg_knee_bend = _bend_score([left_knee, right_knee])
        wrists_above_shoulders = _wrists_above_shoulders(normalized)
        feet_width = _horizontal_distance(normalized, "left_ankle", "right_ankle")
        wrist_width = _horizontal_distance(normalized, "left_wrist", "right_wrist")
        high_knee = _max_knee_lift(normalized)
        split_stance = abs(_point(normalized, "left_ankle")["x"] - _point(normalized, "right_ankle")["x"])
        left_elbow = _joint_angle(raw, "left_shoulder", "left_elbow", "left_wrist")
        right_elbow = _joint_angle(raw, "right_shoulder", "right_elbow", "right_wrist")
        elbow_bend = _bend_score([left_elbow, right_elbow])
        torso_motion = float(pose_features.get("torso_motion", 0.0) or 0.0)
        knee_motion = float(pose_features.get("knee_motion", 0.0) or 0.0)
        elbow_motion = float(pose_features.get("elbow_motion", 0.0) or 0.0)

        if lower_visible:
            scores["Squats"] = max(scores["Squats"], 0.18 + body_upright * 0.30 + avg_knee_bend * 0.35 + min(1.0, knee_motion * 4.0) * 0.15)
            scores["Lunges"] = max(scores["Lunges"], 0.15 + body_upright * 0.2 + avg_knee_bend * 0.2 + min(1.0, split_stance * 1.5) * 0.25 + min(1.0, knee_motion * 4.0) * 0.1)
            scores["High Knees"] = max(scores["High Knees"], 0.15 + body_upright * 0.30 + high_knee * 0.4 + min(1.0, knee_motion * 4.0) * 0.15)

        if upper_visible:
            scores["Biceps Curls (Dumbbell)"] = max(scores["Biceps Curls (Dumbbell)"], 0.2 + body_upright * 0.3 + elbow_bend * 0.25 + _elbows_near_torso(normalized) * 0.15 + min(1.0, elbow_motion * 4.0) * 0.1)
            scores["Shoulder Press"] = max(scores["Shoulder Press"], 0.18 + body_upright * 0.25 + wrists_above_shoulders * 0.4 + min(1.0, elbow_motion * 4.0) * 0.15)

        if full_visible:
            scores["Jumping Jacks"] = max(scores["Jumping Jacks"], 0.15 + min(1.0, feet_width * 0.9) * 0.3 + min(1.0, wrist_width * 0.5) * 0.2 + wrists_above_shoulders * 0.15 + min(1.0, knee_motion * 4.0) * 0.2)

        scores["Plank"] = max(scores["Plank"], 0.20 + body_horizontal * 0.5 + _hip_level_score(raw) * 0.2 + max(0.0, 1.0 - min(1.0, torso_motion * 8.0)) * 0.1)
        scores["Push-ups"] = max(scores["Push-ups"], 0.18 + body_horizontal * 0.40 + elbow_bend * 0.20 + _hands_near_shoulders(normalized) * 0.08 + min(1.0, elbow_motion * 4.0) * 0.08)
        scores["Mountain Climbers"] = max(scores["Mountain Climbers"], 0.12 + body_horizontal * 0.35 + high_knee * 0.25 + min(1.0, knee_motion * 4.0) * 0.2)
        scores["Crunches"] = max(scores["Crunches"], 0.15 + _lying_core_score(raw) * 0.45 + _shoulders_near_hips(normalized) * 0.2 + min(1.0, torso_motion * 4.0) * 0.2)
        scores["Sit-ups"] = max(scores["Sit-ups"], 0.15 + _lying_core_score(raw) * 0.35 + body_upright * 0.15 + _shoulders_near_hips(normalized) * 0.15 + min(1.0, torso_motion * 4.0) * 0.2)

        scores = {exercise: round(max(0.0, min(1.0, score * visibility)), 3) for exercise, score in scores.items()}
        exercise, confidence = max(scores.items(), key=lambda item: item[1])

        if confidence < CONFIDENCE_THRESHOLD:
            exercise = UNKNOWN_EXERCISE

        return {
            "exercise": exercise,
            "confidence": confidence,
            "scores": scores,
            "using_tflite": self.using_tflite,
            "visibility": visibility,
            "classifier_type": "heuristic",
        }


def _unknown_prediction(visibility=0.0):
    return {
        "exercise": UNKNOWN_EXERCISE,
        "confidence": 0.0,
        "scores": {},
        "using_tflite": False,
        "visibility": round(float(visibility or 0.0), 3),
        "classifier_type": "heuristic",
    }


def _point(points, name):
    return points.get(name, {"x": 0.0, "y": 0.0, "visible": False})


def _horizontal_distance(points, first, second):
    a = _point(points, first)
    b = _point(points, second)
    return abs(a["x"] - b["x"]) if a.get("visible") and b.get("visible") else 0.0


def _joint_angle(points, a_name, b_name, c_name):
    a = _point(points, a_name)
    b = _point(points, b_name)
    c = _point(points, c_name)

    if not a.get("visible") or not b.get("visible") or not c.get("visible"):
        return None

    ab = (a["x"] - b["x"], a["y"] - b["y"])
    cb = (c["x"] - b["x"], c["y"] - b["y"])
    dot = ab[0] * cb[0] + ab[1] * cb[1]
    mag = math.hypot(*ab) * math.hypot(*cb)

    if mag <= 0:
        return None

    return math.degrees(math.acos(max(-1.0, min(1.0, dot / mag))))


def _torso_angle(points):
    left_shoulder = _point(points, "left_shoulder")
    right_shoulder = _point(points, "right_shoulder")
    left_hip = _point(points, "left_hip")
    right_hip = _point(points, "right_hip")

    if not all(point.get("visible") for point in [left_shoulder, right_shoulder, left_hip, right_hip]):
        return 0.0

    shoulder = ((left_shoulder["x"] + right_shoulder["x"]) / 2, (left_shoulder["y"] + right_shoulder["y"]) / 2)
    hip = ((left_hip["x"] + right_hip["x"]) / 2, (left_hip["y"] + right_hip["y"]) / 2)
    dx = shoulder[0] - hip[0]
    dy = shoulder[1] - hip[1]
    return math.degrees(math.atan2(abs(dx), abs(dy) or 0.001))


def _score_range(value, target, tolerance):
    return max(0.0, 1.0 - abs(value - target) / max(1.0, tolerance))


def _bend_score(angles):
    useful = [angle for angle in angles if angle is not None]
    if not useful:
        return 0.0
    return max(0.0, min(1.0, (170 - min(useful)) / 90))


def _wrists_above_shoulders(points):
    pairs = [("left_wrist", "left_shoulder"), ("right_wrist", "right_shoulder")]
    hits = 0
    total = 0
    for wrist_name, shoulder_name in pairs:
        wrist = _point(points, wrist_name)
        shoulder = _point(points, shoulder_name)
        if wrist.get("visible") and shoulder.get("visible"):
            total += 1
            hits += 1 if wrist["y"] < shoulder["y"] - 0.15 else 0
    return hits / total if total else 0.0


def _max_knee_lift(points):
    scores = []
    for knee_name, hip_name in [("left_knee", "left_hip"), ("right_knee", "right_hip")]:
        knee = _point(points, knee_name)
        hip = _point(points, hip_name)
        if knee.get("visible") and hip.get("visible"):
            scores.append(max(0.0, min(1.0, (hip["y"] - knee["y"] + 0.15) * 2.5)))
    return max(scores) if scores else 0.0


def _hip_level_score(points):
    left_hip = _point(points, "left_hip")
    right_hip = _point(points, "right_hip")
    if not left_hip.get("visible") or not right_hip.get("visible"):
        return 0.0
    return max(0.0, 1.0 - abs(left_hip["y"] - right_hip["y"]) * 8)


def _hands_near_shoulders(points):
    distances = []
    for wrist_name, shoulder_name in [("left_wrist", "left_shoulder"), ("right_wrist", "right_shoulder")]:
        wrist = _point(points, wrist_name)
        shoulder = _point(points, shoulder_name)
        if wrist.get("visible") and shoulder.get("visible"):
            distances.append(math.hypot(wrist["x"] - shoulder["x"], wrist["y"] - shoulder["y"]))
    if not distances:
        return 0.0
    return max(0.0, 1.0 - min(distances))


def _elbows_near_torso(points):
    distances = []
    for elbow_name, hip_name in [("left_elbow", "left_hip"), ("right_elbow", "right_hip")]:
        elbow = _point(points, elbow_name)
        hip = _point(points, hip_name)
        if elbow.get("visible") and hip.get("visible"):
            distances.append(abs(elbow["x"] - hip["x"]))
    if not distances:
        return 0.0
    return max(0.0, 1.0 - min(distances) * 3)


def _lying_core_score(points):
    return _score_range(abs(_torso_angle(points)), 70, 35)


def _shoulders_near_hips(points):
    shoulder = _point(points, "neck")
    left_hip = _point(points, "left_hip")
    right_hip = _point(points, "right_hip")
    if not shoulder.get("visible") or not left_hip.get("visible") or not right_hip.get("visible"):
        return 0.0
    hip_y = (left_hip["y"] + right_hip["y"]) / 2
    return max(0.0, 1.0 - abs(shoulder["y"] - hip_y) * 1.4)
