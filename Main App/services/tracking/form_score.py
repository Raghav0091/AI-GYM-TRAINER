import streamlit as st


def _angle_score(value, ideal, tolerance, max_penalty=30):
    if not isinstance(value, (int, float)) or value <= 0:
        return 0

    penalty = min(max_penalty, abs(value - ideal) / tolerance * max_penalty)
    return max(0, int(round(100 - penalty)))


def _status_score(value, scores, default=70):
    return scores.get(str(value).upper(), default)


def _clamp_score(value):
    return max(0, min(100, int(round(value))))


def _visibility_multiplier(metrics):
    visibility = float(metrics.get("pose_visibility", metrics.get("pose_visibility_score", 0.0)) or 0.0)
    if visibility >= 0.75:
        return 1.0
    if visibility >= 0.6:
        return 0.85
    if visibility >= 0.5:
        return 0.7
    return 0.5


def calculate_form_score(exercise, metrics):
    """Return a beginner-friendly 0-100 score from the live detector metrics."""
    if not metrics:
        return 0

    if exercise == "Squats":
        knee_angle = float(metrics.get("knee_angle", 0) or 0)
        torso_lean = float(metrics.get("torso_lean", max(0, 180 - float(metrics.get("back_angle", 180) or 180))) or 0)
        scores = [
            _status_score(metrics.get("depth_status"), {"GOOD DEPTH": 100, "STANDING": 85, "TOO HIGH": 55, "N/A": 70}),
            _angle_score(knee_angle, ideal=95, tolerance=45),
            _angle_score(torso_lean, ideal=20, tolerance=25, max_penalty=40),
        ]
        base = sum(scores) / len(scores)
        if metrics.get("depth_status") == "TOO HIGH":
            base -= 8
        if torso_lean > 50:
            base -= 12
        if metrics.get("issue"):
            base -= 8
        return _clamp_score(base * _visibility_multiplier(metrics))
    elif exercise == "Push-ups":
        elbow_angle = float(metrics.get("elbow_angle", 0) or 0)
        scores = [
            _status_score(metrics.get("body_alignment"), {"STRAIGHT": 100, "SLIGHT BEND": 80, "POOR FORM": 45, "N/A": 70}),
            _status_score(metrics.get("hip_status"), {"LEVEL": 100, "SAGGING": 50, "PIKED UP": 50, "N/A": 70}),
            _angle_score(elbow_angle, ideal=85, tolerance=45, max_penalty=45),
        ]
        base = sum(scores) / len(scores)
        if elbow_angle > 115:
            base -= 10
        if str(metrics.get("hip_status", "")).upper() in ["SAGGING", "PIKED UP"]:
            base -= 10
        if metrics.get("issue"):
            base -= 8
        return _clamp_score(base * _visibility_multiplier(metrics))
    elif exercise == "Plank":
        body_alignment_angle = float(metrics.get("body_alignment_angle", 0) or 0)
        scores = [
            _status_score(metrics.get("body_alignment"), {"STRAIGHT": 100, "SLIGHT BEND": 72, "POOR FORM": 40, "N/A": 65}),
            _status_score(metrics.get("hip_status"), {"LEVEL": 100, "SAGGING": 50, "PIKED UP": 50, "N/A": 65}),
            _angle_score(body_alignment_angle, ideal=170, tolerance=25, max_penalty=45),
        ]
        base = sum(scores) / len(scores)
        if str(metrics.get("hip_status", "")).upper() in ["SAGGING", "PIKED UP"]:
            base -= 10
        if str(metrics.get("body_alignment", "")).upper() == "POOR FORM":
            base -= 10
        if metrics.get("issue"):
            base -= 8
        return _clamp_score(base * _visibility_multiplier(metrics))
    else:
        scores = [70]

    return _clamp_score(sum(scores) / len(scores))


def update_form_score_state(exercise, metrics):
    score = calculate_form_score(exercise, metrics)

    st.session_state.form_score = score
    st.session_state.form_score_total = st.session_state.get("form_score_total", 0) + score
    st.session_state.form_score_samples = st.session_state.get("form_score_samples", 0) + 1

    samples = st.session_state.form_score_samples
    st.session_state.average_form_score = int(round(st.session_state.form_score_total / samples)) if samples else score

    return score
