import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import logging

from config import get_settings

logger = logging.getLogger("uvicorn")
settings = get_settings()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes cosine similarity between two 1D vector embeddings.
    Returns a score between 0.0 (completely different) and 1.0 (identical).
    """
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def embed_text(text: str, model: Any) -> List[float]:
    """
    Generates a normalized vector embedding for a given text string.
    """
    if model is None:
        raise ValueError("Embedding model is not loaded in app_state.")
    
    # Generate embedding using sentence-transformers
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def is_duplicate(
    new_question_text: str,
    existing_questions: List[Dict[str, Any]],
    model: Any = None,
    new_embedding: Optional[List[float]] = None,
    threshold: float = settings.DEDUP_THRESHOLD
) -> Tuple[bool, Optional[Dict[str, Any]], float]:
    """
    Checks if a candidate question is a duplicate against comparison sets:
    1. Current plan questions
    2. Past candidate Q&A history
    3. Rejected questions list

    Returns:
        (is_dup: bool, closest_match: Dict or None, highest_score: float)
    """
    if not existing_questions:
        return False, None, 0.0

    # 1. Embed new question text if embedding is not pre-computed
    if new_embedding is None:
        if model is None:
            logger.warning("No model provided to is_duplicate, skipping vector embedding.")
            return False, None, 0.0
        new_embedding = embed_text(new_question_text, model)

    max_sim = 0.0
    closest_match = None

    # 2. Iterate through all comparison questions
    for item in existing_questions:
        # Extract existing embedding or generate on the fly
        item_embedding = item.get("embedding")
        if item_embedding is None and "question" in item:
            if model is not None:
                item_embedding = embed_text(item["question"], model)
                item["embedding"] = item_embedding  # Cache vector

        if item_embedding:
            sim = cosine_similarity(new_embedding, item_embedding)
            if sim > max_sim:
                max_sim = sim
                closest_match = item

    # 3. Compare highest score against threshold
    is_dup = max_sim >= threshold
    return is_dup, closest_match, round(max_sim, 4)


def batch_embed_questions(questions: List[Dict[str, Any]], model: Any) -> List[Dict[str, Any]]:
    """
    Utility function to batch encode multiple questions efficiently.
    Avoids re-encoding questions that already have embeddings attached.
    """
    texts_to_embed = []
    indices_to_update = []

    for idx, q in enumerate(questions):
        if not q.get("embedding") and q.get("question"):
            texts_to_embed.append(q["question"])
            indices_to_update.append(idx)

    if texts_to_embed and model is not None:
        embeddings = model.encode(texts_to_embed, convert_to_numpy=True)
        for i, idx in enumerate(indices_to_update):
            questions[idx]["embedding"] = embeddings[i].tolist()

    return questions