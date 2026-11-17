"""Deterministic external model doubles; these do not model semantic quality."""

import hashlib
from types import SimpleNamespace

import numpy as np


class FakeSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings=True):
        single = isinstance(texts, str)
        items = [texts] if single else texts
        vectors = []
        for text in items:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = np.array([value + 1 for value in digest[:8]], dtype=float)
            if normalize_embeddings:
                vector /= np.linalg.norm(vector)
            vectors.append(vector)
        result = np.array(vectors)
        return result[0] if single else result


class FakeCrossEncoder:
    def __init__(self, model_name):
        self.model_name = model_name

    def predict(self, pairs):
        # Equal scores preserve incoming order. No relevance claim is possible.
        return np.zeros(len(pairs))


class FakeGenerativeModel:
    def __init__(self, model_name="test-model"):
        self.model_name = model_name
        self.prompts = []

    def generate_content(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(text="Mock answer for isolated tests.")
