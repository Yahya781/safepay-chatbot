"""Build-step helper: download the embedding model so cold starts don't fetch it."""
from sentence_transformers import SentenceTransformer

SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model cached.")
