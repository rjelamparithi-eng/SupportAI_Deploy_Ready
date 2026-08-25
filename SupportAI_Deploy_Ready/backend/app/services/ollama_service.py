import os
from typing import List

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL") or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")


def _headers() -> dict:
    if OLLAMA_API_KEY:
        return {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    return {}


async def get_embeddings(text: str) -> List[float]:
    """Generate embeddings using a local Ollama embedding model."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            headers=_headers(),
            json={"model": EMBED_MODEL, "input": text},
        )
        response.raise_for_status()
        data = response.json()
        if "embeddings" in data and data["embeddings"]:
            return data["embeddings"][0]
        if "embedding" in data:
            return data["embedding"]
        raise ValueError("Unexpected Ollama embed response format")


async def generate_response(prompt: str, context: str, company_name: str) -> str:
    """Generate a response using Ollama local or direct Ollama Cloud API."""
    system_prompt = f"""
    You are the official AI information assistant for {company_name}.
    
    STRICT RULES:
    
    1. Answer ONLY from the provided CONTEXT.
    2. Do NOT use your general knowledge.
    3. Do NOT guess or invent missing information.
    4. Do NOT invent:
       - phone numbers
       - email addresses
       - URLs
       - statistics
       - names
       - dates
       - fees
       - placement numbers
       - student counts
       - faculty counts
    5. If the context contains only partial information,
       clearly say that only partial information is available.
    6. If the requested information is not present in the context,
       respond:
    
       "I'm sorry, I couldn't find that information in the available
       {company_name} data."
    
    7. If the context contains a relevant official URL,
       you may provide that URL.
    8. Never claim that information is "regularly updated",
       "officially confirmed", or "provided on request"
       unless the context explicitly says so.
    9. Keep the answer clear and concise.
    """

    full_prompt = f"""Context:
{context}

Question: {prompt}

Answer:"""

    llm_model = os.getenv("LLM_MODEL", "gpt-oss:120b-cloud")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            headers=_headers(),
            json={
                "model": llm_model,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["response"].strip()
