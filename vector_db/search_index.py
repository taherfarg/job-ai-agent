from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
import os
from config import VECTOR_INDEX_FILE, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

try:
    model = SentenceTransformer(EMBEDDING_MODEL)
except Exception as e:
    logger.error(f"Failed to load sentence-transformer model: {e}")
    model = None

def get_job_match_score(job_description: str) -> float:
    """
    Returns a similarity score between 0 and 100 for a job description against the CV index.
    Using FAISS L2 distance where lower is more similar.
    """
    if not os.path.exists(VECTOR_INDEX_FILE) or not model:
        logger.warning(f"FAISS index not found at {VECTOR_INDEX_FILE} or model not loaded. Score calculation failed.")
        return 0.0

    try:
        index = faiss.read_index(str(VECTOR_INDEX_FILE))
        job_embedding = model.encode([job_description])
        
        # Ensure it's 2D float32 array
        query_vector = np.array(job_embedding, dtype=np.float32)
        
        # search the index, k=1
        distances, indices = index.search(query_vector, k=1)
        
        distance = distances[0][0]
        logger.debug(f"FAISS L2 Distance: {distance}")
        
        # L2 Distance conversion heuristics:
        # Sentence-transformers 'all-MiniLM-L6-v2' outputs normalized embeddings if scaled, but default is raw.
        # usually distances are in range [0, 2] if embeddings are normalized, or larger.
        # Simple heuristic mapping to [0-100]
        score = max(0.0, 100.0 - (distance * 10))  # Tunable parameter based on real distances
        
        # Clamp to 100 maximum
        return min(100.0, round(score, 2))
    except Exception as e:
        logger.error(f"Error matching job in vector DB: {e}")
        return 0.0
