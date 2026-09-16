import re
from pathlib import Path
import fitz
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.rag import Document, Chunk

def extract_text(filename: str, mime_type: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or mime_type == "application/pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(page.get_text() for page in doc).strip()
    try:
        return data.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""

def chunk_text(text: str, size: int = 900, overlap: int = 120):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks

def ingest(db: Session, company_id: int, filename: str, mime_type: str, data: bytes):
    content = extract_text(filename, mime_type, data)
    doc = Document(company_id=company_id, filename=filename, mime_type=mime_type, content=content)
    db.add(doc)
    db.flush()
    parts = chunk_text(content)
    for part in parts:
        db.add(Chunk(company_id=company_id, document_id=doc.id, content=part))
    db.commit()
    return doc, len(parts)

def retrieve(db: Session, company_id: int, question: str, limit: int = 6):
    terms = {x for x in re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", question.lower())}
    rows = db.scalars(select(Chunk).where(Chunk.company_id == company_id)).all()
    scored = []
    for row in rows:
        words = set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", row.content.lower()))
        score = len(terms & words)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:limit]]
