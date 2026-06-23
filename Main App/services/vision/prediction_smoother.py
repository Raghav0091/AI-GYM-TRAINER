from collections import Counter, deque


class PredictionSmoother:
    def __init__(self, window_size=30, unknown_threshold=0.6):
        self.window_size = window_size
        self.unknown_threshold = unknown_threshold
        self.predictions = deque(maxlen=window_size)

    def update(self, prediction):
        self.predictions.append(prediction or {"exercise": "Unknown", "confidence": 0.0})
        return self.get_smoothed_prediction()

    def get_smoothed_prediction(self):
        if not self.predictions:
            return {"exercise": "Unknown", "confidence": 0.0, "scores": {}}

        exercises = [item.get("exercise", "Unknown") for item in self.predictions]
        unknown_count = exercises.count("Unknown")

        if unknown_count / len(exercises) >= self.unknown_threshold:
            return {"exercise": "Unknown", "confidence": 0.0, "scores": {}}

        known_predictions = [item for item in self.predictions if item.get("exercise") != "Unknown"]
        if not known_predictions:
            return {"exercise": "Unknown", "confidence": 0.0, "scores": {}}

        most_common_exercise = Counter(item["exercise"] for item in known_predictions).most_common(1)[0][0]
        matching = [item for item in known_predictions if item.get("exercise") == most_common_exercise]
        average_confidence = sum(float(item.get("confidence", 0.0) or 0.0) for item in matching) / len(matching)

        merged_scores = {}
        for item in matching:
            for exercise, score in (item.get("scores") or {}).items():
                merged_scores.setdefault(exercise, []).append(float(score or 0.0))

        scores = {
            exercise: round(sum(values) / len(values), 3)
            for exercise, values in merged_scores.items()
            if values
        }

        return {
            "exercise": most_common_exercise,
            "confidence": round(average_confidence, 3),
            "scores": scores,
        }

    def reset(self):
        self.predictions.clear()
