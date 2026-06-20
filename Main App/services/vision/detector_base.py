STANDARD_METRICS = {
    "exercise": "",
    "reps": 0,
    "stage": "setup",
    "form_score": 0,
    "issue": None,
    "is_valid_rep": False,
    "hold_seconds": 0,
    "camera_status": "tracking",
    "debug": {},
}


def standardize_detector_metrics(exercise_name, detector, metrics):
    safe_metrics = dict(STANDARD_METRICS)
    safe_metrics.update(metrics or {})
    safe_metrics["exercise"] = exercise_name
    safe_metrics["reps"] = int(safe_metrics.get("reps") or 0)
    safe_metrics["stage"] = str(safe_metrics.get("stage") or getattr(detector, "stage", "setup") or "setup")
    safe_metrics["hold_seconds"] = float(safe_metrics.get("hold_seconds") or 0)
    safe_metrics["camera_status"] = safe_metrics.get("camera_status") or "tracking"
    safe_metrics["is_valid_rep"] = bool(safe_metrics.get("is_valid_rep", False))

    debug = dict(safe_metrics.get("debug") or {})
    debug.setdefault("detector_class", detector.__class__.__name__ if detector else "Unavailable")
    debug.setdefault("stage", safe_metrics["stage"])
    debug.setdefault("reps", safe_metrics["reps"])
    debug.setdefault("form_score", safe_metrics["form_score"])
    debug.setdefault("issue", safe_metrics["issue"])
    debug.setdefault("hold_seconds", safe_metrics["hold_seconds"])
    debug.setdefault("camera_status", safe_metrics["camera_status"])
    safe_metrics["debug"] = debug

    return safe_metrics
