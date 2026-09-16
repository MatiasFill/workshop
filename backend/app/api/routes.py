from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_tenant_db, require_permission
from app.core.rate_limit import rate_limit
from app.core.sessions import SessionData
from app.models import rag
from app.schemas.ai import AskRequest, AskResponse, MemoryCreate
from app.services.ai.gateway import ask
from app.services.ocr import extract_image_text
from app.services.rag import ingest

api_router = APIRouter()

# A partir da FASE 1, estes endpoints usam autenticação de usuário real
# (sessão via cookie + Redis) e autorização por permissão (RBAC), em vez da
# chave de API interna usada como medida-ponte antes disso. O contexto de
# empresa (company_id) nunca vem do corpo da requisição — vem sempre da
# sessão autenticada, resolvida por get_tenant_db/require_permission.


@api_router.post(
    "/ai/ask",
    response_model=AskResponse,
    dependencies=[Depends(rate_limit(
        "ai_ask", settings.RATE_LIMIT_AI_ASK_MAX, settings.RATE_LIMIT_AI_ASK_WINDOW_SECONDS
    ))],
)
async def ai_ask(
    payload: AskRequest,
    user: SessionData = Depends(require_permission("ai.ask")),
    db: Session = Depends(get_tenant_db),
):
    answer, source, provider, chunks = await ask(
        db,
        user.company_id,
        payload.question,
        payload.use_rag,
        payload.memory_first,
        payload.context,
    )
    return AskResponse(answer=answer, source=source, provider=provider, chunks_used=chunks)


@api_router.post("/ai/memory")
def create_memory(
    payload: MemoryCreate,
    user: SessionData = Depends(require_permission("ai.memory.manage")),
    db: Session = Depends(get_tenant_db),
):
    from app.services.memory import save

    item = save(db, user.company_id, payload.question, payload.answer, payload.context)
    return {"id": item.id, "status": "saved"}


@api_router.post(
    "/rag/ingest",
    dependencies=[Depends(rate_limit(
        "rag_ingest", settings.RATE_LIMIT_RAG_INGEST_MAX, settings.RATE_LIMIT_RAG_INGEST_WINDOW_SECONDS
    ))],
)
async def rag_ingest(
    file: UploadFile = File(...),
    user: SessionData = Depends(require_permission("rag.ingest")),
    db: Session = Depends(get_tenant_db),
):
    filename = file.filename or "upload"
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in settings.rag_allowed_extensions:
        raise HTTPException(
            415,
            f"Extensão '.{extension}' não permitida. Extensões aceitas: "
            f"{', '.join(sorted(settings.rag_allowed_extensions))}.",
        )

    data = await file.read()
    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(413, f"Arquivo excede o limite configurado de {settings.UPLOAD_MAX_MB}MB.")

    mime = file.content_type or ""
    if mime.startswith("image/") or extension in {"png", "jpg", "jpeg"}:
        text = extract_image_text(data)
        doc, count = ingest(db, user.company_id, filename, "text/plain", text.encode())
    else:
        doc, count = ingest(db, user.company_id, filename, mime, data)
    return {"document_id": doc.id, "filename": doc.filename, "chunks": count}


@api_router.get("/rag/documents")
def rag_documents(
    user: SessionData = Depends(require_permission("rag.read")),
    db: Session = Depends(get_tenant_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    rows = (
        db.query(rag.Document)
        .filter(rag.Document.company_id == user.company_id)
        .order_by(rag.Document.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {"id": x.id, "filename": x.filename, "mime_type": x.mime_type, "created_at": x.created_at}
        for x in rows
    ]
