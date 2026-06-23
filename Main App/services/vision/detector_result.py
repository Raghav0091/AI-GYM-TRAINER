from dataclasses import asdict, dataclass, field


@dataclass
class DetectorResult:
    exercise: str
    reps: int = 0
    stage: str = "setup"
    form_score: int = 0
    issue: str | None = None
    pose_detected: bool = False
    confidence: float = 0.0
    hold_seconds: float = 0.0
    sets_completed: int = 0
    current_set_reps: int = 0
    camera_status: str = "waiting"
    debug: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def default_detector_result(exercise_name):
    return DetectorResult(exercise=exercise_name).to_dict()
