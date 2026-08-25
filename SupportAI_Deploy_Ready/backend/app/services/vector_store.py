import os
from typing import List

import chromadb
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL") or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")

# Hosted embedding option. This preserves the Nomic embedding family when
# deploying online, because Ollama Cloud currently doesn't expose cloud
# embedding models.
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY", "")
NOMIC_EMBED_MODEL = os.getenv("NOMIC_EMBED_MODEL", "nomic-embed-text-v1.5")

# Chroma Cloud when credentials are configured; otherwise local persistent Chroma.
if os.getenv("CHROMA_API_KEY"):
    chroma_client = chromadb.CloudClient(
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
        api_key=os.getenv("CHROMA_API_KEY"),
    )
else:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection():
    return chroma_client.get_or_create_collection(
        name="business_docs"
    )


def _ollama_headers() -> dict:
    if OLLAMA_API_KEY:
        return {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
    return {}


def _nomic_embeddings(
    texts: List[str],
    task_type: str
) -> List[List[float]]:

    all_embeddings: List[List[float]] = []

    # Send only a few chunks per request
    batch_size = 8

    print(
        f"[EMBED] Total texts: {len(texts)} | "
        f"Batch size: {batch_size}"
    )

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i + batch_size]

        print(
            f"[EMBED] Processing "
            f"{i + 1}-{min(i + batch_size, len(texts))} "
            f"of {len(texts)}"
        )

        response = requests.post(
            "https://api-atlas.nomic.ai/v1/embedding/text",
            headers={
                "Authorization": f"Bearer {NOMIC_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": NOMIC_EMBED_MODEL,
                "texts": batch,
                "task_type": task_type,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        if "embeddings" not in data:
            raise ValueError(
                f"Unexpected Nomic embedding "
                f"response format: {data}"
            )

        all_embeddings.extend(
            data["embeddings"]
        )

    print(
        f"[EMBED] Completed: "
        f"{len(all_embeddings)} embeddings"
    )

    return all_embeddings


def _ollama_embeddings(texts: List[str]) -> List[List[float]]:
    embeddings: List[List[float]] = []
    for text in texts:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            headers=_ollama_headers(),
            json={"model": EMBED_MODEL, "input": text},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        if "embeddings" in data and data["embeddings"]:
            embeddings.append(data["embeddings"][0])
        elif "embedding" in data:
            embeddings.append(data["embedding"])
        else:
            raise ValueError(f"Unexpected Ollama embed response format: {data}")
    return embeddings


def get_embeddings(texts: List[str], task_type: str = "search_document") -> List[List[float]]:
    if NOMIC_API_KEY:
        return _nomic_embeddings(texts, task_type)
    return _ollama_embeddings(texts)


def index_chunks(business_id: str, chunks: List[str]):
    collection = get_collection()
    embeddings = get_embeddings(chunks, task_type="search_document")
    ids = [f"{business_id}_{i}_{abs(hash(chunk)) % 10**8}" for i, chunk in enumerate(chunks)]

    try:
        existing = collection.get(where={
            "$and": [
                {"business_id": {"$eq": business_id}},
                {"chunk_type": {"$eq": "document"}},
            ]
        })
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        try:
            existing = collection.get(where={"business_id": business_id})
            doc_ids = [id_ for id_ in existing["ids"] if not id_.startswith(f"{business_id}_admin_")]
            if doc_ids:
                collection.delete(ids=doc_ids)
        except Exception:
            pass

    # Add to Chroma in smaller batches
        chroma_batch_size = 50
        
        metadatas = [
            {
                "business_id": business_id,
                "chunk_type": "document"
            }
            for _ in chunks
        ]
        
        for i in range(
            0,
            len(chunks),
            chroma_batch_size
        ):
        
            end = i + chroma_batch_size
        
            print(
                f"[CHROMA] Indexing "
                f"{i + 1}-"
                f"{min(end, len(chunks))} "
                f"of {len(chunks)}"
            )
        
            collection.add(
                documents=chunks[i:end],
                embeddings=embeddings[i:end],
                ids=ids[i:end],
                metadatas=metadatas[i:end],
            )


def index_admin_answer(business_id: str, question: str, qa_text: str):
    collection = get_collection()
    embedding = get_embeddings([qa_text], task_type="search_document")[0]
    chunk_id = f"{business_id}_admin_{abs(hash(question)) % 10**10}"

    try:
        collection.upsert(
            documents=[qa_text],
            embeddings=[embedding],
            ids=[chunk_id],
            metadatas=[{"business_id": business_id, "chunk_type": "admin_answer"}],
        )
    except Exception as e:
        raise RuntimeError(f"ChromaDB upsert failed: {e}")


def query_chunks(
    business_id: str,
    query: str,
    n_results: int = 12
) -> List[str]:

    collection = get_collection()

    print(
        f"[RETRIEVAL] Business ID: {business_id}"
    )
    print(
        f"[RETRIEVAL] Question: {query}"
    )

    # Check how many chunks exist for this business
    try:
        stored = collection.get(
            where={"business_id": business_id}
        )

        print(
            f"[RETRIEVAL] Stored chunks: "
            f"{len(stored.get('ids', []))}"
        )

    except Exception as e:
        print(
            f"[RETRIEVAL] Count error: {e}"
        )

    # Create search-query embedding
    query_embedding = get_embeddings(
        [query],
        task_type="search_query"
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"business_id": business_id},
        include=[
            "documents",
            "distances",
            "metadatas"
        ],
    )

    documents = (
        results.get("documents", [[]])[0]
        if results.get("documents")
        else []
    )

    distances = (
        results.get("distances", [[]])[0]
        if results.get("distances")
        else []
    )

    metadatas = (
        results.get("metadatas", [[]])[0]
        if results.get("metadatas")
        else []
    )

    print(
        f"[RETRIEVAL] Results returned: "
        f"{len(documents)}"
    )

    for i, document in enumerate(documents):

        distance = (
            distances[i]
            if i < len(distances)
            else "?"
        )

        metadata = (
            metadatas[i]
            if i < len(metadatas)
            else {}
        )

        print(
            f"[RETRIEVAL] RESULT {i + 1} "
            f"| Distance={distance} "
            f"| Metadata={metadata}"
        )

        print(
            f"[RETRIEVAL] TEXT: "
            f"{document[:500]}"
        )

    return documents
