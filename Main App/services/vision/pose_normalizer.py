import math
from collections import deque


VISIBILITY_THRESHOLD = 0.35
_MOTION_WINDOWS: dict[str, deque] = {}


KEYPOINT_SPECS = [
    ("nose", 0),
    ("neck", None),
    ("right_shoulder", 12),
    ("right_elbow", 14),
    ("right_wrist", 16),
    ("left_shoulder", 11),
    ("left_elbow", 13),
    ("left_wrist", 15),
    ("right_hip", 24),
    ("right_knee", 26),
    ("right_ankle", 28),
    ("left_hip", 23),
    ("left_knee", 25),
    ("left_ankle", 27),
    ("right_eye", 5),
    ("left_eye", 2),
    ("right_ear", 8),
    ("left_ear", 7),
]


def extract_keypoints_18(landmarks):
    keypoints = {}

    for name, index in KEYPOINT_SPECS:
        if name == "neck":
            keypoints[name] = _midpoint(_landmark_to_point(landmarks, 11), _landmark_to_point(landmarks, 12))
        else:
            keypoints[name] = _landmark_to_point(landmarks, index)

    return keypoints


def normalize_keypoints(keypoints):
    visible_points = [point for point in keypoints.values() if point["visible"]]

    if not visible_points:
        return {name: {"x": 0.0, "y": 0.0, "visibility": 0.0, "visible": False} for name in keypoints}

    center_x = sum(point["x"] for point in visible_points) / len(visible_points)
    center_y = sum(point["y"] for point in visible_points) / len(visible_points)
    body_scale = _estimate_body_scale(keypoints, visible_points)

    normalized = {}
    for name, point in keypoints.items():
        if not point["visible"] or body_scale <= 0:
            normalized[name] = {"x": 0.0, "y": 0.0, "visibility": point.get("visibility", 0.0), "visible": False}
            continue

        normalized[name] = {
            "x": round((point["x"] - center_x) / body_scale, 4),
            "y": round((point["y"] - center_y) / body_scale, 4),
            "visibility": point["visibility"],
            "visible": True,
        }

    return normalized


def flatten_keypoints(keypoints):
    flattened = []
    for name, _ in KEYPOINT_SPECS:
        point = keypoints.get(name, {})
        flattened.extend([float(point.get("x", 0.0)), float(point.get("y", 0.0))])
    return flattened


def calculate_visibility_score(landmarks):
    if not landmarks:
        return 0.0

    keypoints = extract_keypoints_18(landmarks)
    visible_count = sum(1 for point in keypoints.values() if point["visible"])
    return round(visible_count / max(1, len(keypoints)), 3)


def get_pose_features(landmarks):
    raw_keypoints = extract_keypoints_18(landmarks)
    normalized_keypoints = normalize_keypoints(raw_keypoints)
    feature_vector = flatten_keypoints(normalized_keypoints)
    visibility_score = calculate_visibility_score(landmarks)

    return {
        "raw_keypoints": raw_keypoints,
        "normalized_keypoints": normalized_keypoints,
        "feature_vector": feature_vector,
        "visibility_score": visibility_score,
        "pose_detected": visibility_score >= 0.45,
        "landmarks": landmarks,
        "torso_motion": _motion_score("torso", raw_keypoints.get("neck"), raw_keypoints.get("left_hip"), raw_keypoints.get("right_hip")),
        "knee_motion": _motion_score("knees", raw_keypoints.get("left_knee"), raw_keypoints.get("right_knee")),
        "elbow_motion": _motion_score("elbows", raw_keypoints.get("left_elbow"), raw_keypoints.get("right_elbow")),
    }


def _landmark_to_point(landmarks, index):
    try:
        landmark = landmarks[index]
    except (IndexError, TypeError):
        return _empty_point()

    visibility = float(getattr(landmark, "visibility", 1.0) or 0.0)
    return {
        "x": float(getattr(landmark, "x", 0.0) or 0.0),
        "y": float(getattr(landmark, "y", 0.0) or 0.0),
        "visibility": visibility,
        "visible": visibility >= VISIBILITY_THRESHOLD,
    }


def _midpoint(first, second):
    visibility = min(first.get("visibility", 0.0), second.get("visibility", 0.0))
    visible = first.get("visible", False) and second.get("visible", False)

    if not visible:
        return _empty_point(visibility)

    return {
        "x": (first["x"] + second["x"]) / 2,
        "y": (first["y"] + second["y"]) / 2,
        "visibility": visibility,
        "visible": True,
    }


def _empty_point(visibility=0.0):
    return {"x": 0.0, "y": 0.0, "visibility": float(visibility or 0.0), "visible": False}


def _estimate_body_scale(keypoints, visible_points):
    candidates = [
        _distance(keypoints.get("left_shoulder"), keypoints.get("right_shoulder")),
        _distance(keypoints.get("left_hip"), keypoints.get("right_hip")),
        _distance(keypoints.get("left_shoulder"), keypoints.get("left_hip")),
        _distance(keypoints.get("right_shoulder"), keypoints.get("right_hip")),
        _distance(keypoints.get("left_hip"), keypoints.get("left_knee")),
        _distance(keypoints.get("right_hip"), keypoints.get("right_knee")),
        _distance(keypoints.get("left_knee"), keypoints.get("left_ankle")),
        _distance(keypoints.get("right_knee"), keypoints.get("right_ankle")),
    ]
    useful = [value for value in candidates if value and value > 0.01]

    if useful:
        return max(sum(useful) / len(useful), max(useful), 0.1)

    xs = [point["x"] for point in visible_points]
    ys = [point["y"] for point in visible_points]
    return max(max(xs) - min(xs), max(ys) - min(ys), 0.1)


def _distance(first, second):
    if not first or not second or not first.get("visible") or not second.get("visible"):
        return 0.0

    return math.hypot(first["x"] - second["x"], first["y"] - second["y"])


def _center(points):
    visible = [point for point in points if point and point.get("visible")]
    if not visible:
        return None
    return {
        "x": sum(point["x"] for point in visible) / len(visible),
        "y": sum(point["y"] for point in visible) / len(visible),
    }


def _motion_score(name, *points):
    center = _center(points)
    if center is None:
        return 0.0

    window = _MOTION_WINDOWS.setdefault(name, deque(maxlen=5))
    window.append(center)
    if len(window) < 2:
        return 0.0

    distances = []
    for i in range(1, len(window)):
        prev = window[i - 1]
        curr = window[i]
        distances.append(math.hypot(curr["x"] - prev["x"], curr["y"] - prev["y"]))

    return round(sum(distances) / len(distances), 4)
