"""Measure latency of each phase of the RAG pipeline."""
import time
import requests

BASE = "http://127.0.0.1:8000"

# 1. End-to-end /ask
t = time.time()
r = requests.post(f"{BASE}/ask", json={"question": "Hi", "session_id": "latency-test"})
total = time.time() - t
print(f"[1] Total /ask time: {total:.2f}s  (status {r.status_code})")
print(f"    Answer: {r.json().get('answer', '')[:120]}")

# 2. Local retrieval only (no LLM) — time the vectorstore search
t = time.time()
from chatbot import build_vectorstore
vs = build_vectorstore()
build_time = time.time() - t
print(f"\n[2] build_vectorstore() time: {build_time:.2f}s")

t = time.time()
retriever = vs.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10})
docs = retriever.invoke("Hi")
retrieval_time = time.time() - t
print(f"[3] Retrieval (MMR k=4 fetch_k=10) time: {retrieval_time:.2f}s  ({len(docs)} docs)")

# 3. LLM only — time a direct Groq call
t = time.time()
from chatbot import build_llm, PRIMARY_MODEL
llm = build_llm(PRIMARY_MODEL)
resp = llm.invoke("Say 'hi' in one word.")
llm_time = time.time() - t
print(f"\n[4] LLM ({PRIMARY_MODEL}) single call time: {llm_time:.2f}s")
print(f"    Response: {resp.content[:80]}")