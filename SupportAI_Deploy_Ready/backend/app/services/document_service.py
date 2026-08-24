import io
import PyPDF2
from typing import List


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_txt(content: bytes) -> str:
    """Extract text from a TXT file."""
    return content.decode("utf-8", errors="ignore").strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def process_file(filename: str, content: bytes) -> List[str]:
    """Process uploaded file and return text chunks."""
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif filename_lower.endswith(".txt"):
        text = extract_text_from_txt(content)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    if not text:
        raise ValueError("No text could be extracted from the file")

    return chunk_text(text)
