from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router
from app.api.auth_routes import auth_router
from app.api.customer_routes import customer_router
from app.api.appointment_routes import appointment_router
from app.api.stock_routes import stock_router
from app.api.work_order_routes import work_order_router
from app.api.notification_routes import notification_router
from app.api.report_routes import report_router
from app.api.finance_routes import finance_router
from app.api.cash_routes import cash_router
from app.api.supplier_routes import supplier_router
from app.api.purchase_order_routes import purchase_order_router
from app.api.audit_routes import audit_router
from app.api.lgpd_routes import lgpd_router
from app.api.retention_routes import retention_router
from app.events.handlers import register_handlers

register_handlers()

# Em produção, a documentação interativa (/docs, /redoc, /openapi.json) fica
# desativada por padrão: ela expõe toda a superfície da API publicamente.
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Gestão de oficina com RAG, OCR, memória e múltiplos provedores de LLM.",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(appointment_router, prefix="/api")
app.include_router(stock_router, prefix="/api")
app.include_router(work_order_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(cash_router, prefix="/api")
app.include_router(supplier_router, prefix="/api")
app.include_router(purchase_order_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(lgpd_router, prefix="/api")
app.include_router(retention_router, prefix="/api")
app.include_router(api_router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}

@app.get("/api/ready")
def ready():
    return {"status": "ready"}
