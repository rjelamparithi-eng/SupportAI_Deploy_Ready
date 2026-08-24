# SupportAI - Deployment Guide

## Target architecture

- Frontend: Vercel
- Backend: Render
- Database: MongoDB Atlas
- Vector DB: Chroma Cloud
- Chat model: Ollama Cloud
- Embeddings: Nomic hosted Embedding API

The code remains compatible with local development. If cloud credentials are absent, it falls back to local MongoDB / Ollama / Chroma where applicable.

## 1. GitHub preparation

This deploy-ready copy intentionally excludes `.env`, `node_modules`, `venv`, local Chroma data, and `.git` history.

Create a NEW GitHub repository and upload/push this folder.

## 2. MongoDB Atlas

Create an Atlas cluster and database user. Add network access for the Render backend, then copy the SRV connection string.

Render environment variable:

`MONGODB_URL=mongodb+srv://...`

Keep:

`DATABASE_NAME=ai_support_saas`

## 3. Chroma Cloud

Create a Chroma Cloud database and obtain:

- `CHROMA_API_KEY`
- `CHROMA_TENANT`
- `CHROMA_DATABASE`

Because hosted Chroma starts as a new vector database, train/upload your business document again after deployment.

## 4. Nomic embeddings

Create a Nomic API key and add:

- `NOMIC_API_KEY`
- `NOMIC_EMBED_MODEL=nomic-embed-text-v1.5`

The online deployment uses Nomic's hosted embedding endpoint instead of trying to run `nomic-embed-text` inside the Render instance.

## 5. Ollama Cloud

Create an Ollama API key and set on Render:

- `OLLAMA_BASE_URL=https://ollama.com`
- `OLLAMA_API_KEY=...`
- `LLM_MODEL=gpt-oss:120b`

Do not use `gpt-oss:120b-cloud` with the direct ollama.com API; that name is used by the local Ollama client when it offloads a cloud model.

## 6. Render backend

Easiest: create a Web Service from the repo.

Settings if configuring manually:

- Root Directory: `backend`
- Runtime: Python
- Python: `3.11.11`
- Build Command: `pip install -r requirements.txt && python -m playwright install chromium`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Required Render secrets/variables:

- `MONGODB_URL`
- `DATABASE_NAME=ai_support_saas`
- `SECRET_KEY` (long random string)
- `OLLAMA_BASE_URL=https://ollama.com`
- `OLLAMA_API_KEY`
- `LLM_MODEL=gpt-oss:120b`
- `NOMIC_API_KEY`
- `NOMIC_EMBED_MODEL=nomic-embed-text-v1.5`
- `CHROMA_API_KEY`
- `CHROMA_TENANT`
- `CHROMA_DATABASE`
- `CORS_ORIGINS` (set after Vercel URL is known)
- `APP_FRONTEND_URL` (set after Vercel URL is known)

Optional SMTP variables are in `backend/.env.example`.

After deployment, verify:

- `https://YOUR-RENDER-URL.onrender.com/health`
- `https://YOUR-RENDER-URL.onrender.com/docs`

## 7. Vercel frontend

Import the same GitHub repo in Vercel.

Set:

- Root Directory: `frontend`
- Framework: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

Add environment variable:

`VITE_API_URL=https://YOUR-RENDER-URL.onrender.com`

Deploy.

`frontend/vercel.json` is included so React Router routes such as `/dashboard` and `/chatbot/...` keep working on refresh.

## 8. Final Render CORS values

After Vercel gives the production URL, update Render:

`CORS_ORIGINS=https://YOUR-PROJECT.vercel.app`

`APP_FRONTEND_URL=https://YOUR-PROJECT.vercel.app`

Then redeploy/restart the backend if needed.

## 9. Retrain chatbot

Your old local `backend/chroma_data` was not copied to the cloud. Log in to SupportAI and upload the source PDF/TXT or train from URL again. This creates embeddings in Chroma Cloud.

## 10. Final test

1. Register/login.
2. Create business.
3. Train from PDF/TXT first (simpler test).
4. Open public chatbot URL.
5. Ask a question contained in the document.
6. Check Dashboard analytics.
7. Then test website crawling.

## Notes

- Render Free web services can spin down after inactivity, so the first request after an idle period can be slow.
- Render's normal filesystem is ephemeral. That is why this deployment uses Chroma Cloud instead of the local `chroma_data` folder.
- Keep all API keys only in Render environment variables, not in GitHub or Vercel frontend variables.
