import numpy as np
from typing import List

class Noiser:
    def __init__(self, noise_std_dev: float = 0.05):
        self.noise_std_dev = noise_std_dev

    def apply_noise(self, probabilities: List[float]) -> List[float]:
        noise = np.random.normal(1, self.noise_std_dev, len(probabilities))
        noisy_probabilities = np.array(probabilities) * noise
        normalized_probabilities = noisy_probabilities / np.sum(noisy_probabilities)
        return normalized_probabilities