from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
from config import VECTOR_INDEX_FILE, VECTOR_DIMENSION, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Load Model once globally if needed, though lazy loading is also fine.
model = SentenceTransformer(EMBEDDING_MODEL)

def build_vector_index(cv_text: str):
    logger.info("Building FAISS vector index from CV...")
    if not cv_text:
        logger.error("CV text is empty. Cannot build index.")
        return False
        
    try:
        embedding = model.encode([cv_text])
        index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        # We need float32 for FAISS
        index.add(np.array(embedding, dtype=np.float32))
        
        # Save index to disk
        faiss.write_index(index, str(VECTOR_INDEX_FILE))
        logger.info(f"FAISS index saved successfully at {VECTOR_INDEX_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error building FAISS index: {e}")
        return False
