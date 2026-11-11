"""Benchmark models with a realistic RAG-sized prompt."""
import os, time
from dotenv import load_dotenv
load_dotenv()
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Realistic RAG prompt: system + context + question
system = "You are the SafePay Assistant. Answer based only on context. Be concise."
context = ("SafePay is a Pakistani payment gateway. It supports credit/debit cards, "
           "wallets (Easypaisa, JazzCash), and Raast. Pricing: cards 2.9% + Rs 30, "
           "wallets 1.5%, Raast 1.5%. Payment orchestration routes transactions "
           "across providers using an AI-powered rules engine.") * 3
question = "What is SafePay's pricing for wallets and Raast?"

candidates = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

for model in candidates:
    try:
        t = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0.2,
            max_tokens=200,
        )
        dt = time.time() - t
        text = resp.choices[0].message.content
        print(f"{model:30s} -> {dt:6.2f}s  | {text[:80]}")
    except Exception as e:
        print(f"{model:30s} -> ERROR: {e}")