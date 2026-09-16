from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Oficina AI"
    CORS_ORIGINS: str = "http://localhost:5173"
    DATABASE_URL: str = "sqlite:///./data/dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_ENABLED: bool = False
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    MEMORY_MODE: bool = True
    MEMORY_TTL_SECONDS: int = 604800
    MAX_CONTEXT_CHUNKS: int = 6
    UPLOAD_MAX_MB: int = 15

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AI_ASK_MAX: int = 20
    RATE_LIMIT_AI_ASK_WINDOW_SECONDS: int = 60
    RATE_LIMIT_RAG_INGEST_MAX: int = 10
    RATE_LIMIT_RAG_INGEST_WINDOW_SECONDS: int = 60

    # Documentos permitidos em /api/rag/ingest (mime type -> extensões aceitas)
    RAG_ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,txt"

    # FASE 1 — autenticação por sessão (cookie + Redis) e RBAC
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_TTL_SECONDS: int = 60 * 60 * 8  # 8 horas
    SESSION_COOKIE_SECURE: bool = False  # HTTPS deve ser habilitado explicitamente em produção
    PASSWORD_HASH_ITERATIONS: int = 600_000

    # Seed do usuário administrador inicial (ver app/db/seed.py). Vazio = não semeia.
    SEED_COMPANY_NAME: str = ""
    SEED_ADMIN_EMAIL: str = ""
    SEED_ADMIN_PASSWORD: str = ""

    # FASE 4/5 — notificações (comprovante de OS e alerta de revisão).
    # Sem essas credenciais configuradas, o envio é apenas marcado como
    # SKIPPED no log (ver app/services/notifications.py) — nunca quebra a
    # requisição que disparou o envio (ex.: fechar uma OS).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@oficina.local"
    SMTP_USE_TLS: bool = True

    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_FROM_NUMBER: str = ""

    # Quantos dias antes do vencimento da próxima revisão o lembrete é disparado.
    REVISION_REMINDER_DAYS_AHEAD: int = 7

    # FASE 10 — retenção de dados (LGPD, princípio de minimização, art. 6º VII).
    # NotificationLog é puramente operacional (log de tentativa de envio) e
    # carrega customer_id — sem valor de guarda legal, então tem uma janela
    # curta. Clientes inativos há muitos anos e sem financeiro em aberto são
    # candidatos a anonimização automática (ver app/services/retention.py).
    RETENTION_NOTIFICATION_LOGS_DAYS: int = 180
    RETENTION_INACTIVE_CUSTOMER_YEARS: int = 5

    # O README instrui a criar o .env na raiz do projeto e iniciar o backend
    # a partir de backend/. Também aceitamos um .env local ao backend.
    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", PROJECT_ROOT / ".env"),
        extra="ignore",
    )

    @property
    def cors_origins(self):
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    @property
    def rag_allowed_extensions(self):
        return {x.strip().lower() for x in self.RAG_ALLOWED_EXTENSIONS.split(",") if x.strip()}

    @property
    def is_production(self):
        return self.APP_ENV.lower() in {"production", "prod"}

    @property
    def notifications_enabled_email(self):
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    @property
    def notifications_enabled_whatsapp(self):
        return bool(self.WHATSAPP_API_URL and self.WHATSAPP_API_TOKEN)

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
