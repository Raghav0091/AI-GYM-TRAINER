from detectors.biceps_curl import BicepsCurlDetector
from detectors.crunches import CrunchesDetector
from detectors.high_knees import HighKneesDetector
from detectors.jumping_jacks import JumpingJacksDetector
from detectors.lunges import LungesDetector
from detectors.mountain_climbers import MountainClimbersDetector
from detectors.plank import PlankDetector
from detectors.pushup import PushUpDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.situps import SitUpsDetector
from detectors.squat import SquatDetector


DETECTOR_REGISTRY = {
    "Squats": SquatDetector,
    "Push-ups": PushUpDetector,
    "Biceps Curls (Dumbbell)": BicepsCurlDetector,
    "Shoulder Press": ShoulderPressDetector,
    "Lunges": LungesDetector,
    "Jumping Jacks": JumpingJacksDetector,
    "High Knees": HighKneesDetector,
    "Crunches": CrunchesDetector,
    "Sit-ups": SitUpsDetector,
    "Plank": PlankDetector,
    "Mountain Climbers": MountainClimbersDetector,
}


def build_detectors():
    detectors = {}

    for exercise_name, detector_class in DETECTOR_REGISTRY.items():
        detector = detector_class()

        if hasattr(detector, "reset"):
            detector.reset()

        detectors[exercise_name] = detector

    return detectors
