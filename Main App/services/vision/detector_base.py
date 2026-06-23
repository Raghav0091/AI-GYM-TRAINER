from services.vision.detector_result import default_detector_result


STANDARD_METRICS = {
    **default_detector_result(""),
    "is_valid_rep": False,
    "selected_exercise": "",
    "detected_exercise": "Unknown",
    "exercise_confidence": 0.0,
    "auto_detect_enabled": False,
    "pose_visibility_score": 0.0,
    "detector_name": "Unavailable",
    "processing_status": "waiting",
}


class DetectorMetricsAdapter:
    """Small compatibility wrapper so every detector exposes the same shape."""

    def __init__(self, exercise_name, detector):
        self.exercise_name = exercise_name
        self.detector = detector
        self.metrics = standardize_detector_metrics(exercise_name, detector, {})

    def process_landmarks(self, landmarks):
        raw_metrics = self.detector.process(landmarks) if self.detector else {}
        self.metrics = standardize_detector_metrics(self.exercise_name, self.detector, raw_metrics)
        return self.metrics

    def get_metrics(self):
        return dict(self.metrics)


def standardize_detector_metrics(exercise_name, detector, metrics):
    safe_metrics = dict(STANDARD_METRICS)
    safe_metrics.update(metrics or {})
    safe_metrics["exercise"] = exercise_name
    safe_metrics["reps"] = int(safe_metrics.get("reps") or 0)
    safe_metrics["stage"] = str(safe_metrics.get("stage") or getattr(detector, "stage", "setup") or "setup")
    safe_metrics["form_score"] = int(safe_metrics.get("form_score") or 0)
    safe_metrics["hold_seconds"] = float(safe_metrics.get("hold_seconds") or 0)
    safe_metrics["sets_completed"] = int(safe_metrics.get("sets_completed") or 0)
    safe_metrics["current_set_reps"] = int(safe_metrics.get("current_set_reps") or 0)
    safe_metrics["confidence"] = float(safe_metrics.get("confidence") or 0.0)
    safe_metrics["exercise_confidence"] = float(safe_metrics.get("exercise_confidence") or safe_metrics["confidence"] or 0.0)
    safe_metrics["pose_visibility_score"] = float(safe_metrics.get("pose_visibility_score") or 0.0)
    safe_metrics["camera_status"] = safe_metrics.get("camera_status") or "tracking"
    safe_metrics["is_valid_rep"] = bool(safe_metrics.get("is_valid_rep", False))
    safe_metrics["pose_detected"] = bool(safe_metrics.get("pose_detected", False))
    safe_metrics["selected_exercise"] = safe_metrics.get("selected_exercise") or exercise_name
    safe_metrics["detected_exercise"] = safe_metrics.get("detected_exercise") or exercise_name
    safe_metrics["detector_name"] = safe_metrics.get("detector_name") or (detector.__class__.__name__ if detector else "Unavailable")

    debug = dict(safe_metrics.get("debug") or {})
    debug.setdefault("detector_class", detector.__class__.__name__ if detector else "Unavailable")
    debug.setdefault("detector_name", safe_metrics["detector_name"])
    debug.setdefault("stage", safe_metrics["stage"])
    debug.setdefault("reps", safe_metrics["reps"])
    debug.setdefault("form_score", safe_metrics["form_score"])
    debug.setdefault("issue", safe_metrics["issue"])
    debug.setdefault("hold_seconds", safe_metrics["hold_seconds"])
    debug.setdefault("camera_status", safe_metrics["camera_status"])
    debug.setdefault("exercise_confidence", safe_metrics["exercise_confidence"])
    debug.setdefault("pose_visibility_score", safe_metrics["pose_visibility_score"])
    safe_metrics["debug"] = debug

    return safe_metrics
