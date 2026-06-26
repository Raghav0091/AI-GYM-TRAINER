from collections import defaultdict, deque

from services.vision.geometry import calculate_angle


_SMOOTHING_WINDOWS = {}


def safe_get_landmark(landmarks, index):
    if landmarks is None or index is None or index < 0 or index >= len(landmarks):
        return None

    return landmarks[index]


def is_landmark_visible(landmark, threshold=0.5):
    return landmark is not None and getattr(landmark, "visibility", 0) >= threshold


def get_landmark_visibility(landmarks, indices):
    values = []

    for index in indices:
        landmark = safe_get_landmark(landmarks, index)
        values.append(getattr(landmark, "visibility", 0) if landmark else 0)

    return sum(values) / len(values) if values else 0


def choose_best_side(landmarks, left_points, right_points):
    left_visibility = get_landmark_visibility(landmarks, left_points)
    right_visibility = get_landmark_visibility(landmarks, right_points)

    if left_visibility >= right_visibility:
        return "left", left_points, left_visibility

    return "right", right_points, right_visibility


def point(landmark):
    if landmark is None:
        return None

    return (landmark.x, landmark.y)


def angle_from_indices(landmarks, a_idx, b_idx, c_idx):
    return calculate_angle(
        point(safe_get_landmark(landmarks, a_idx)),
        point(safe_get_landmark(landmarks, b_idx)),
        point(safe_get_landmark(landmarks, c_idx)),
    )


def smooth_value(metric_name, value, window_size=5):
    if value is None:
        return 0

    window = _SMOOTHING_WINDOWS.get(metric_name)

    if window is None or window.maxlen != window_size:
        window = deque(maxlen=window_size)
        _SMOOTHING_WINDOWS[metric_name] = window

    window.append(float(value))
    return sum(window) / len(window)


def normalize_angle(value):
    if value is None:
        return 0

    return max(0, min(180, float(value)))
