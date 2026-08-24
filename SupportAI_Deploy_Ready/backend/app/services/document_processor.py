import re
from typing import List
import io

from app.services.web_crawler import crawl_website


# ─── TEXT EXTRACTION ─────────────────────────────────────────────────────────

def extract_text_from_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore")


def extract_text_from_pdf(content: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


# ─── CHUNKING ────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return []

    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())

    return chunks


# ─── FILE PROCESSING ─────────────────────────────────────────────────────────

def process_file(filename: str, content: bytes) -> List[str]:
    filename_lower = filename.lower()

    if filename_lower.endswith(".txt"):
        text = extract_text_from_txt(content)
    elif filename_lower.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    else:
        raise ValueError("Unsupported file type. Only PDF and TXT are supported.")

    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text content found in the file.")

    return chunks


# ─── WEB SCRAPING ────────────────────────────────────────────────────────────

async def process_url(url: str, crawl: bool = False) -> List[str]:
    """Crawl a website and return usable text chunks for indexing."""
    documents = []

    if crawl:
        documents = await crawl_website(url, max_pages=10, max_depth=2)
    else:
        documents = await crawl_website(url, max_pages=5, max_depth=1)

    if not documents:
        raise ValueError("No content could be scraped from the URL.")

    results: List[str] = []
    for document in documents:
        text = document.text.strip()
        if not text:
            continue
        results.extend(chunk_text(text, chunk_size=500, overlap=50))

    if not results:
        raise ValueError("No usable text content found in the scraped website.")

    return results