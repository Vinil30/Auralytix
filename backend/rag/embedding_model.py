#Instead of loading the embedding model again and again, we are just loading it once through this file and reusing it.

import os

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

_embedding_model = None

