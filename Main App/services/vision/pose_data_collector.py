import json
import time
from pathlib import Path


class PoseDataCollector:
    def __init__(self, output_dir=None, min_interval_seconds=0.5):
        app_root = Path(__file__).resolve().parents[2]
        self.output_dir = Path(output_dir) if output_dir else app_root / "data" / "pose_samples"
        self.min_interval_seconds = min_interval_seconds
        self.last_saved_at = 0.0

    def save_sample(self, sample):
        now = time.time()
        if now - self.last_saved_at < self.min_interval_seconds:
            return False

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"pose_samples_{time.strftime('%Y%m%d')}.jsonl"

        row = {
            "timestamp": now,
            **(sample or {}),
        }

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

        self.last_saved_at = now
        return True
