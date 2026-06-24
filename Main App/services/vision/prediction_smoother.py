from collections import Counter, deque
import time


class PredictionSmoother:
    def __init__(self, window_size=30, unknown_threshold=0.6, dominance_threshold=0.6, switch_cooldown_seconds=2.0):
        self.window_size = window_size
        self.unknown_threshold = unknown_threshold
        self.dominance_threshold = dominance_threshold
        self.switch_cooldown_seconds = switch_cooldown_seconds
        self.predictions = deque(maxlen=window_size)
        self._active_exercise = "Unknown"
        self._last_switch_at = 0.0

    def update(self, prediction):
        self.predictions.append(prediction or {"exercise": "Unknown", "confidence": 0.0})
        return self.get_smoothed_prediction()

    def get_smoothed_prediction(self):
        if not self.predictions:
            return self._result("Unknown", 0.0, False, {})

        exercises = [item.get("exercise", "Unknown") for item in self.predictions]
        unknown_count = exercises.count("Unknown")

        if unknown_count / len(exercises) >= self.unknown_threshold:
            self._active_exercise = "Unknown"
            return self._result("Unknown", 0.0, False, {})

        known_predictions = [item for item in self.predictions if item.get("exercise") != "Unknown"]
        if not known_predictions:
            self._active_exercise = "Unknown"
            return self._result("Unknown", 0.0, False, {})

        counter = Counter(item["exercise"] for item in known_predictions)
        most_common_exercise, count = counter.most_common(1)[0]
        dominance = count / len(known_predictions)
        matching = [item for item in known_predictions if item.get("exercise") == most_common_exercise]
        average_confidence = sum(float(item.get("confidence", 0.0) or 0.0) for item in matching) / len(matching)

        merged_scores = {}
        for item in known_predictions:
            for exercise, score in (item.get("scores") or {}).items():
                merged_scores.setdefault(exercise, []).append(float(score or 0.0))

        scores = {
            exercise: round(sum(values) / len(values), 3)
            for exercise, values in merged_scores.items()
            if values
        }
        is_stable = dominance >= self.dominance_threshold and average_confidence >= 0.65

        if not is_stable:
            if self._active_exercise != "Unknown":
                return self._result(self._active_exercise, round(average_confidence, 3), False, scores)
            return self._result("Unknown", round(average_confidence, 3), False, scores)

        now = time.time()
        switching = self._active_exercise not in ["Unknown", most_common_exercise]
        if switching and (now - self._last_switch_at) < self.switch_cooldown_seconds:
            return self._result(self._active_exercise, round(average_confidence, 3), False, scores)

        if switching or self._active_exercise != most_common_exercise:
            self._active_exercise = most_common_exercise
            self._last_switch_at = now

        return self._result(self._active_exercise, round(average_confidence, 3), True, scores)

    def reset(self):
        self.predictions.clear()
        self._active_exercise = "Unknown"
        self._last_switch_at = 0.0

    def _result(self, exercise, confidence, is_stable, scores):
        return {
            "exercise": exercise,
            "confidence": confidence,
            "is_stable": bool(is_stable),
            "window_size": self.window_size,
            "scores": scores,
        }
