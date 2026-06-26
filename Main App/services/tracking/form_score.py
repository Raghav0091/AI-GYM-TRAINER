import streamlit as st


def _angle_score(value, ideal, tolerance, max_penalty=30):
    if not isinstance(value, (int, float)) or value <= 0:
        return 0

    penalty = min(max_penalty, abs(value - ideal) / tolerance * max_penalty)
    return max(0, int(round(100 - penalty)))


def _status_score(value, scores, default=70):
    return scores.get(str(value).upper(), default)


def calculate_form_score(exercise, metrics):
    """Return a beginner-friendly 0-100 score from the live detector metrics."""
    if not metrics:
        return 0

    if exercise == "Squats":
        scores = [
            _status_score(metrics.get("depth_status"), {"GOOD DEPTH": 100, "STANDING": 85, "TOO HIGH": 55, "N/A": 70}),
            _angle_score(metrics.get("back_angle"), ideal=165, tolerance=45),
            _angle_score(metrics.get("knee_angle"), ideal=95, tolerance=60),
        ]
    elif exercise == "Push-ups":
        scores = [
            _status_score(metrics.get("body_alignment"), {"STRAIGHT": 100, "SLIGHT BEND": 80, "POOR FORM": 45, "N/A": 70}),
            _status_score(metrics.get("hip_status"), {"LEVEL": 100, "SAGGING": 55, "PIKED UP": 65, "N/A": 70}),
            _angle_score(metrics.get("elbow_angle"), ideal=90, tolerance=70),
        ]
    elif exercise == "Plank":
        scores = [
            _status_score(metrics.get("body_alignment"), {"STRAIGHT": 100, "SLIGHT BEND": 78, "POOR FORM": 45, "N/A": 70}),
            _status_score(metrics.get("hip_status"), {"LEVEL": 100, "SAGGING": 55, "PIKED UP": 60, "N/A": 70}),
        ]
    else:
        scores = [70]

    return int(round(sum(scores) / len(scores)))


def update_form_score_state(exercise, metrics):
    score = calculate_form_score(exercise, metrics)

    st.session_state.form_score = score
    st.session_state.form_score_total = st.session_state.get("form_score_total", 0) + score
    st.session_state.form_score_samples = st.session_state.get("form_score_samples", 0) + 1

    samples = st.session_state.form_score_samples
    st.session_state.average_form_score = int(round(st.session_state.form_score_total / samples)) if samples else score

    return score
