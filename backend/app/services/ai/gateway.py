from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.memory import lookup, save
from app.services.rag import retrieve
from .providers import get_provider

async def ask(db: Session, company_id: int, question: str, use_rag=True, memory_first=True, context=""):
    if memory_first and settings.MEMORY_MODE:
        hit = lookup(db, company_id, question, context)
        if hit:
            return hit.answer, "memory", "memory", 0

    chunks = retrieve(db, company_id, question, settings.MAX_CONTEXT_CHUNKS) if use_rag else []
    rag_context = "\n\n---\n\n".join(c.content for c in chunks)

    prompt = f"""
Pergunta:
{question}

Contexto fornecido pelo sistema:
{context}

Contexto recuperado dos documentos:
{rag_context or "(nenhum documento relevante encontrado)"}

Regras:
- Responda em português.
- Não invente informações ausentes.
- Diferencie claramente fato encontrado no contexto de sugestão.
- Seja objetivo e útil para uma oficina mecânica.
""".strip()

    if not settings.LLM_ENABLED:
        answer = (
            "Modo local: nenhuma LLM foi chamada. "
            + ("Encontrei contexto relevante nos documentos." if chunks else
               "Não encontrei contexto suficiente nos documentos.")
        )
        source = "local-rag"
        provider = "disabled"
    else:
        provider = get_provider()
        answer = await provider.generate(prompt)
        source = "rag+llm" if chunks else "llm"

    if settings.MEMORY_MODE:
        save(db, company_id, question, answer, context)

    return answer, source, getattr(provider, "name", "disabled"), len(chunks)
