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


def index_chunks(
    business_id: str,
    chunks: List[str]
):
    collection = get_collection()

    business_id = str(business_id)

    print(
        f"[CHROMA] Starting indexing | "
        f"Business={business_id} | "
        f"Chunks={len(chunks)}"
    )

    if not chunks:
        raise ValueError(
            "No chunks received for indexing."
        )

    # STEP 1: Create embeddings
    embeddings = get_embeddings(
        chunks,
        task_type="search_document"
    )

    print(
        f"[CHROMA] Embeddings created: "
        f"{len(embeddings)}"
    )

    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embedding count mismatch. "
            f"Chunks={len(chunks)}, "
            f"Embeddings={len(embeddings)}"
        )

    # STEP 2: Delete old document chunks
    try:
        old = collection.get(
            where={
                "$and": [
                    {
                        "business_id": {
                            "$eq": business_id
                        }
                    },
                    {
                        "chunk_type": {
                            "$eq": "document"
                        }
                    }
                ]
            }
        )

        old_ids = old.get("ids", [])

        if old_ids:
            print(
                f"[CHROMA] Deleting "
                f"{len(old_ids)} old chunks"
            )

            collection.delete(
                ids=old_ids
            )

    except Exception as e:
        print(
            f"[CHROMA] Old-data cleanup warning: {e}"
        )

    # STEP 3: Prepare IDs and metadata
    ids = []

    metadatas = []

    for i, chunk in enumerate(chunks):

        chunk_id = (
            f"{business_id}_doc_"
            f"{i}_{abs(hash(chunk)) % 10**8}"
        )

        ids.append(chunk_id)

        metadatas.append(
            {
                "business_id": business_id,
                "chunk_type": "document"
            }
        )

    # STEP 4: Store in smaller batches
    batch_size = 50

    for start in range(
        0,
        len(chunks),
        batch_size
    ):

        end = min(
            start + batch_size,
            len(chunks)
        )

        print(
            f"[CHROMA] Saving "
            f"{start + 1}-{end} "
            f"of {len(chunks)}"
        )

        collection.upsert(
            ids=ids[start:end],
            documents=chunks[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    # STEP 5: Verify immediately
    verify = collection.get(
        where={
            "business_id": business_id
        }
    )

    stored_count = len(
        verify.get("ids", [])
    )

    print(
        f"[CHROMA] VERIFY STORED CHUNKS: "
        f"{stored_count}"
    )

    if stored_count == 0:
        raise RuntimeError(
            "Chroma indexing failed: "
            "0 chunks found after upsert."
        )

    print(
        "[CHROMA] INDEXING SUCCESS ✅"
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
