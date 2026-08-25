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

async def process_url(url: str, crawl: bool = True) -> List[str]:
    """Crawl multiple website pages and return text chunks for indexing."""

    print(f"[SCRAPER] Starting crawl: {url}")

    # Always crawl multiple internal pages
    documents = await crawl_website(
        url,
        max_pages=30,
        max_depth=4
    )

    print(f"[SCRAPER] Pages crawled: {len(documents)}")

    if not documents:
        raise ValueError("No content could be scraped from the URL.")

    results: List[str] = []
    seen = set()

    for document in documents:
        text = document.text.strip()

        if not text:
            continue

        print(
            f"[SCRAPER] Page: {document.url} | "
            f"Characters: {len(text)}"
        )

        # Add page information to improve chatbot answers
        page_text = (
            f"Page: {document.title}\n"
            f"URL: {document.url}\n\n"
            f"{text}"
        )

        page_chunks = chunk_text(
            page_text,
            chunk_size=350,
            overlap=60
        )

        for chunk in page_chunks:
            # Avoid duplicate chunks
            if chunk not in seen:
                seen.add(chunk)
                results.append(chunk)

    print(f"[SCRAPER] Total chunks created: {len(results)}")

    if not results:
        raise ValueError(
            "No usable text content found in the scraped website."
        )

    return results
