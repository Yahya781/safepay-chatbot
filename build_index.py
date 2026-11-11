"""Build step: download the embedding model and build the vector index once,
so the web service only has to load it at startup.

Run after editing any *_knowledge.txt file:  python build_index.py
"""
from chatbot import build_vectorstore

build_vectorstore(rebuild=True)
print("Index built.")
