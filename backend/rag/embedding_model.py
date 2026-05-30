#Instead of loading the embedding model again and again, we are just loading it once through this file and reusing it.

import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

from sentence_transformers import SentenceTransformer
_embedding_model = None
def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )
        print("[INFO] Embedding model loaded successfully.")
    return _embedding_model
