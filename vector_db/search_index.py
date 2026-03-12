"""
search_index.py
───────────────
Uses the pre-built FAISS index (from build_index.py) to compute semantic
similarity scores between each scraped job description and the candidate CV.

This pre-filters jobs BEFORE sending them to the LLM, saving tokens and time.
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
from config import VECTOR_INDEX_FILE, VECTOR_DIMENSION, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def score_jobs_against_cv(jobs: list[dict]) -> list[dict]:
    """
    Compute cosine similarity between each job description and the CV embedding.

    Adds a `semantic_score` field (float 0.0–1.0) to each job dict and returns
    the list sorted by score descending.

    Args:
        jobs: List of job dicts with at least a `description` key.

    Returns:
        Same list with `semantic_score` added and sorted best-first.
    """
    if not jobs:
        return jobs

    if not VECTOR_INDEX_FILE.exists():
        logger.warning("FAISS index not found. Skipping semantic scoring.")
        for job in jobs:
            job["semantic_score"] = 0.5  # neutral score when index missing
        return jobs

    try:
        model = _get_model()
        index = faiss.read_index(str(VECTOR_INDEX_FILE))

        # Get CV embedding stored in the index
        cv_vec_ptr = faiss.rev_swig_ptr(index.get_xb(), index.ntotal * VECTOR_DIMENSION)
        cv_vec = np.array(cv_vec_ptr, dtype=np.float32).reshape(index.ntotal, VECTOR_DIMENSION)
        cv_norm = cv_vec / (np.linalg.norm(cv_vec, axis=1, keepdims=True) + 1e-8)

        descriptions = [job.get("description", job.get("title", "")) for job in jobs]
        job_embeddings = model.encode(descriptions, show_progress_bar=False).astype(np.float32)
        job_norms = job_embeddings / (np.linalg.norm(job_embeddings, axis=1, keepdims=True) + 1e-8)

        # Cosine similarity = dot product of L2-normalised vectors
        scores = (job_norms @ cv_norm.T).flatten()

        for job, score in zip(jobs, scores):
            job["semantic_score"] = float(round(max(0.0, min(1.0, score)), 4))

        jobs_sorted = sorted(jobs, key=lambda j: j["semantic_score"], reverse=True)
        logger.info(
            f"Semantic scoring complete. Top score: {jobs_sorted[0]['semantic_score']:.3f} "
            f"({jobs_sorted[0]['title']})"
        )
        return jobs_sorted

    except Exception as e:
        logger.error(f"Error during semantic scoring: {e}")
        for job in jobs:
            job["semantic_score"] = 0.5
        return jobs


# Legacy helper: single-job L2 distance based score (kept for compatibility)
def get_job_match_score(job_description: str) -> float:
    """Returns a 0-100 score using L2 distance (legacy function)."""
    if not VECTOR_INDEX_FILE.exists():
        return 0.0
    try:
        model = _get_model()
        index = faiss.read_index(str(VECTOR_INDEX_FILE))
        query_vector = model.encode([job_description]).astype(np.float32)
        distances, _ = index.search(query_vector, k=1)
        distance = distances[0][0]
        return float(min(100.0, max(0.0, round(100.0 - (distance * 10), 2))))
    except Exception as e:
        logger.error(f"Error in get_job_match_score: {e}")
        return 0.0
