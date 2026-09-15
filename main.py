"""
SafePay Assistant API — FastAPI backend.

Endpoints:
  GET  /              → Full-page Chat UI (index.html)
  GET  /widget.js     → Embeddable widget script
  GET  /widget.html   → Widget chat panel (loaded in iframe)
  GET  /demo.html     → Demo page showing how to embed the widget
  POST /ask           → { question } → { answer, sources }
  GET  /health        → health check
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from chatbot import (
    build_qa_chain,
    build_vectorstore,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
)
import asyncio
import functools
import os

app = FastAPI(title="SafePay Assistant API", version="2.0")
qa_chain = None
fallback_chain = None
vectorstore = None

# In-memory conversation history, keyed by session_id.
# Each entry is a list of (user_message, assistant_message) tuples.
# We keep only the last MAX_TURNS turns so the prompt stays bounded.
sessions = {}
MAX_TURNS = 4

# Allow the widget to call the API from any client website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_qa_chain():
    """Build the QA chains lazily so importing the module is cheap.

    The vector store is built once and shared by both the primary and
    fallback chains, so we only embed the knowledge base a single time.
    """
    global qa_chain, fallback_chain, vectorstore
    if qa_chain is None:
        print("Building QA chains (first request)...")
        vectorstore = build_vectorstore()
        qa_chain = build_qa_chain(vectorstore=vectorstore, model_name=PRIMARY_MODEL)
        fallback_chain = build_qa_chain(vectorstore=vectorstore, model_name=FALLBACK_MODEL)
        print("QA chains ready.")
    return qa_chain, fallback_chain


class Question(BaseModel):
    question: str
    session_id: str = "default"


@app.get("/health")
def health():
    return {"status": "ok", "chain_loaded": qa_chain is not None}


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = "index.html"
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(index_path, encoding="utf-8") as f:
        return f.read()


@app.get("/widget.js")
def widget_js():
    js_path = "widget.js"
    if not os.path.exists(js_path):
        raise HTTPException(status_code=404, detail="widget.js not found")
    return FileResponse(js_path, media_type="application/javascript")


@app.get("/widget.html", response_class=HTMLResponse)
def widget_html():
    html_path = "widget.html"
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="widget.html not found")
    with open(html_path, encoding="utf-8") as f:
        return f.read()


@app.get("/demo.html", response_class=HTMLResponse)
def demo_html():
    html_path = "demo.html"
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="demo.html not found")
    with open(html_path, encoding="utf-8") as f:
        return f.read()


@app.post("/ask")
async def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Load this session's history (list of (user, assistant) tuples)
    chat_history = sessions.get(q.session_id, [])

    primary, fallback = get_qa_chain()
    payload = {"question": q.question, "chat_history": chat_history}

    try:
        result = await asyncio.to_thread(primary.invoke, payload)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Primary model ({PRIMARY_MODEL}) failed: {e}. Retrying with fallback ({FALLBACK_MODEL})...")
        try:
            result = await asyncio.to_thread(fallback.invoke, payload)
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Query failed: {e2}")

    answer = result["answer"]

    # Store the new turn and trim to the last MAX_TURNS
    history = sessions.get(q.session_id, [])
    history.append((q.question, answer))
    sessions[q.session_id] = history[-MAX_TURNS:]

    # Extract source snippets for citations
    sources = []
    if "source_documents" in result:
        for doc in result["source_documents"]:
            snippet = doc.page_content.strip().replace("\n", " ")
            if len(snippet) > 150:
                snippet = snippet[:147] + "..."
            sources.append(snippet)

    return {"answer": answer, "sources": sources}
