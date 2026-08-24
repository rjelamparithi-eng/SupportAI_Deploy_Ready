import os
from typing import List

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:120b-cloud")

UNANSWERED_SENTINEL = "[[UNANSWERED]]"


def _ollama_headers() -> dict:
    if OLLAMA_API_KEY:
        return {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    return {}


def generate_response(company_name: str, context_chunks: List[str], user_message: str) -> str:
    if not context_chunks:
        return f"I'm sorry, I don't have that information. Please contact the business directly. {UNANSWERED_SENTINEL}"

    context = "\n\n".join(context_chunks)

    system_prompt = f"""You are a friendly and helpful customer support assistant for {company_name}.

You have been given context extracted from the company's website/documents below.
Your job is to answer the customer's question using that context.

Rules:
- ALWAYS attempt an answer first using the closest available information in the context, even if it's not a perfect match.
- If the answer is clearly in the context, answer it directly and confidently.
- If the answer is only partially in the context, or spread across multiple parts of the context, combine what you have into the best possible answer.
- If the context has related information, use it to give a helpful response rather than refusing.
- Only respond with the exact text below if the context has absolutely NOTHING related to the question:
  CANNOT_ANSWER: I'm sorry, I couldn't find an answer to that. Please contact us directly for more help.
- Keep answers short, friendly and clear.
- Do not mention that you are using context or chunks.

Context from {company_name}:
{context}"""

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        headers=_ollama_headers(),
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    raw = data["message"]["content"].strip()

    if raw.startswith("CANNOT_ANSWER:"):
        clean_msg = raw[len("CANNOT_ANSWER:"):].strip()
        return f"{clean_msg} {UNANSWERED_SENTINEL}"

    return raw
