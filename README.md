# safepay-chatbot

SafePay Assistant — a RAG chatbot (FastAPI + Groq + ChromaDB) with an embeddable widget.

## Run locally
```
pip install -r requirements.txt
echo GROQ_API_KEY=your_key > .env
uvicorn main:app --reload
```
The first run builds the vector index in `chroma_db/`. After editing any `*_knowledge.txt`, rebuild it with `python build_index.py`.

Open http://localhost:8000 (chat UI), `/demo.html` (widget demo), `/health`.

## Deploy on Render
1. Push this repo to GitHub.
2. Render Dashboard → **New → Blueprint** → select the repo (uses `render.yaml`).
   (Build step runs `build_index.py`, so the index is ready before the service starts; runs on the 512 MB `starter` plan.)
3. When prompted, set `GROQ_API_KEY`.
4. After the first deploy, `https://<service-name>.onrender.com/health` returns `{"status":"ok"}`.
5. Embed on any site: `<script src="https://<service-name>.onrender.com/widget.js" async></script>`
   (if your URL differs from `safepay-chatbot.onrender.com`, update the URLs in `demo.html`).
