import math
import re
from typing import List, Dict, Any


def tokenize(text: str) -> List[str]:
    """Tokenizes text into words and n-grams for semantic representation."""
    clean = re.sub(r'[^\w\s]', '', text.lower())
    words = clean.split()
    # Add bigrams
    bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words)-1)]
    return words + bigrams


def compute_text_embedding(text: str, dim: int = 128) -> List[float]:
    """
    Computes a deterministic, lightweight semantic hash vector of fixed dimension.
    Provides sub-millisecond similarity scoring without requiring heavy GPU models or external APIs.
    """
    vec = [0.0] * dim
    tokens = tokenize(text)
    if not tokens:
        return vec

    for token in tokens:
        # Stable murmur-like hash projection
        h = 0
        for char in token:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        idx = h % dim
        # Assign sign based on higher bits
        sign = 1.0 if ((h >> 8) & 1) == 1 else -1.0
        vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-9:
        vec = [round(x / norm, 5) for x in vec]
    return vec


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two unit vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(-1.0, min(1.0, dot))
