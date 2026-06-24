from __future__ import annotations

from dataclasses import dataclass


VISIBILITY_THRESHOLD = 0.45
LOW_LIGHT_THRESHOLD = 0.35


@dataclass(frozen=True)
class BodyPoint:
    name: str
    index: int


BODY_POINTS = {
    "left_shoulder": BodyPoint("left_shoulder", 11),
    "right_shoulder": BodyPoint("right_shoulder", 12),
    "left_elbow": BodyPoint("left_elbow", 13),
    "right_elbow": BodyPoint("right_elbow", 14),
    "left_wrist": BodyPoint("left_wrist", 15),
    "right_wrist": BodyPoint("right_wrist", 16),
    "left_hip": BodyPoint("left_hip", 23),
    "right_hip": BodyPoint("right_hip", 24),
    "left_knee": BodyPoint("left_knee", 25),
    "right_knee": BodyPoint("right_knee", 26),
    "left_ankle": BodyPoint("left_ankle", 27),
    "right_ankle": BodyPoint("right_ankle", 28),
}

UPPER_BODY = [
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
]
LOWER_BODY = ["left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
FULL_BODY = ["left_shoulder", "right_shoulder", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]


def _visibility_for(landmarks, key: str) -> float:
    point = BODY_POINTS[key]
    if landmarks is None or point.index >= len(landmarks):
        return 0.0
    lm = landmarks[point.index]
    return float(getattr(lm, "visibility", 0.0) or 0.0)


def _group_visibility(landmarks, keys: list[str]) -> float:
    values = [_visibility_for(landmarks, key) for key in keys]
    return sum(values) / len(values) if values else 0.0


def _group_detected(landmarks, keys: list[str], threshold: float = VISIBILITY_THRESHOLD, min_ratio: float = 0.75) -> bool:
    if not keys:
        return False
    visible = sum(1 for key in keys if _visibility_for(landmarks, key) >= threshold)
    return (visible / len(keys)) >= min_ratio


def calculate_pose_visibility(landmarks) -> float:
    return round(_group_visibility(landmarks, list(BODY_POINTS.keys())), 3)


def has_upper_body(landmarks) -> bool:
    return _group_detected(landmarks, UPPER_BODY, min_ratio=0.7)


def has_lower_body(landmarks) -> bool:
    return _group_detected(landmarks, LOWER_BODY, min_ratio=0.7)


def has_full_body(landmarks) -> bool:
    return _group_detected(landmarks, FULL_BODY, min_ratio=0.75)


def get_missing_body_parts(landmarks) -> list[str]:
    missing = []
    for key in BODY_POINTS:
        if _visibility_for(landmarks, key) < VISIBILITY_THRESHOLD:
            missing.append(key.replace("_", " "))
    return missing


def get_camera_guidance(landmarks) -> list[str]:
    visibility = calculate_pose_visibility(landmarks)
    upper_ok = has_upper_body(landmarks)
    lower_ok = has_lower_body(landmarks)
    full_ok = has_full_body(landmarks)
    messages: list[str] = []

    if not full_ok:
        messages.append("Move farther back so your full body is visible.")
    if not lower_ok:
        messages.append("Your legs are not visible. Move camera lower or step back.")
    if not upper_ok:
        messages.append("Your upper body is not visible. Adjust camera angle.")
    if visibility < LOW_LIGHT_THRESHOLD:
        messages.append("Lighting is low. Try brighter lighting.")

    messages.append("Stand sideways for push-ups and planks.")
    messages.append("Stand front-facing for squats, curls, shoulder press, and jumping jacks.")
    return messages
