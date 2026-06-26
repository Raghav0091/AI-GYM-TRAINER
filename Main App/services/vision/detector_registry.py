from detectors.plank import PlankDetector
from detectors.pushup import PushUpDetector
from detectors.squat import SquatDetector


DETECTOR_REGISTRY = {
    "Squats": SquatDetector,
    "Push-ups": PushUpDetector,
    "Plank": PlankDetector,
}


def get_detector(exercise_name):
    detector_class = DETECTOR_REGISTRY.get(exercise_name)

    if not detector_class:
        return None

    detector = detector_class()
    if hasattr(detector, "reset"):
        detector.reset()

    return detector


def detector_available(exercise_name):
    return exercise_name in DETECTOR_REGISTRY


def list_supported_exercises():
    return list(DETECTOR_REGISTRY.keys())


def build_detectors():
    detectors = {}

    for exercise_name, detector_class in DETECTOR_REGISTRY.items():
        detector = detector_class()

        if hasattr(detector, "reset"):
            detector.reset()

        detectors[exercise_name] = detector

    return detectors
