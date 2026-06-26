from abc import ABC, abstractmethod

from services.vision.geometry import calculate_angle


class BaseExercise(ABC):
    def __init__(self):
        self.reps = 0
        self.stage = None

    def calculate_angle(self, a, b, c):
        return calculate_angle(a, b, c)

    def get_point(self, landmarks, idx):
        p = landmarks[idx]

        return (p.x, p.y)

    def landmarks_visible(self, landmarks, indices, min_visibility=0.65):
        return all(landmarks[idx].visibility >= min_visibility for idx in indices)

    def midpoint(self, landmarks, first_idx, second_idx):
        first = landmarks[first_idx]
        second = landmarks[second_idx]

        return ((first.x + second.x) / 2, (first.y + second.y) / 2)

    @abstractmethod
    def process(self, landmarks):
        pass

    @abstractmethod
    def reset(self):
        pass
