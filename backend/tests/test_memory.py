from app.db.session import Base, engine, SessionLocal
from app.services.memory import save, lookup
from app.models.company import Company

def test_memory_roundtrip():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        company = Company(name="Empresa Teste")
        db.add(company)
        db.flush()
        save(db, company.id, "teste oficina", "resposta local", "")
        item = lookup(db, company.id, "teste oficina", "")
        assert item is not None
        assert item.answer == "resposta local"
    finally:
        db.close()

def test_memory_is_isolated_by_company():
    """Confirma que uma empresa não recebe cache gravado por outra."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        company_a = Company(name="Empresa A")
        company_b = Company(name="Empresa B")
        db.add_all([company_a, company_b])
        db.flush()
        save(db, company_a.id, "qual a marca do carro?", "Fiat", "")
        assert lookup(db, company_b.id, "qual a marca do carro?", "") is None
        assert lookup(db, company_a.id, "qual a marca do carro?", "") is not None
    finally:
        db.close()
