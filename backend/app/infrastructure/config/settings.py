from functools import lru_cache
import logging
from urllib.parse import quote_plus

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ORIGEN_LOCAL = "http://localhost:5173"
ORIGEN_PAGES = "https://agro-asistente.pages.dev"
PATRON_DESPLIEGUE_PAGES = "https://*.agro-asistente.pages.dev"
REGEX_DESPLIEGUE_PAGES = r"^https://[A-Za-z0-9-]+\.agro-asistente\.pages\.dev$"
JWT_DEFAULT_SECRET = "change-me-in-local-env-do-not-use-in-production"
HOSTS_SENAMHI_PERMITIDOS = frozenset({"wis.senamhi.gob.pe"})
HOSTS_OLLAMA_PERMITIDOS = frozenset({"127.0.0.1", "localhost"})

_logger = logging.getLogger("agro.security")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "agro-asistente"
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "agro_asistente"

    jwt_secret: str = JWT_DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120
    # None = enforce solo en production. true/false fuerza el comportamiento.
    jwt_secret_enforce: bool | None = None

    knowledge_dir: str = "../knowledge"

    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "agro_knowledge_pmv1"

    rag_top_k: int = 3
    rag_min_similarity: float = 0.12
    chunk_size: int = 500

    embedding_provider: str = "local"
    embedding_dimension: int = 128
    embedding_api_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""

    generation_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:1.5b"
    ollama_timeout_seconds: int = 90

    senamhi_wis2_base_url: str = "https://wis.senamhi.gob.pe/oapi"
    senamhi_wis2_collection: str = "urn:wmo:md:pe-senamhi:synop-hourly"
    senamhi_wis2_timeout_seconds: int = 20

    cors_origins: str = "http://localhost:5173"

    clasificador_margen_minimo: float = 0.17
    clasificador_modelo_ruta: str = ""

    # --- Controles OWASP (defaults compatibles con PMV1 / demos) ---
    force_openapi: bool = False
    health_detailed: bool | None = None
    rate_limit_enabled: bool = True
    rate_limit_login_max: int = 10
    rate_limit_login_window_seconds: int = 300
    rate_limit_register_max: int = 5
    rate_limit_register_window_seconds: int = 3600
    rate_limit_query_max: int = 30
    rate_limit_query_window_seconds: int = 60
    password_policy: str = "basic"
    knowledge_mutation_policy: str = "open"
    knowledge_curator_emails: str = ""
    weather_require_auth: bool = False
    # None = enforce solo en production (compat local/docker).
    url_allowlist_enforce: bool | None = None
    prompt_hardening: bool = True
    model_integrity_check: bool = True
    security_log_enabled: bool = True

    # Cookie HttpOnly opcional (compat: default false; Bearer sigue válido).
    auth_cookie_enabled: bool = False
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"

    # Cola async para indexación / consultas largas.
    async_jobs_enabled: bool = True

    @field_validator("clasificador_margen_minimo")
    @classmethod
    def validar_margen_clasificador(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError(
                "CLASIFICADOR_MARGEN_MINIMO debe estar entre 0 y 1. "
                "El valor predeterminado es 0.17 y no se sustituye en silencio."
            )
        return value

    @field_validator("password_policy")
    @classmethod
    def validar_password_policy(cls, value: str) -> str:
        limpio = (value or "basic").strip().lower()
        if limpio not in {"basic", "strong"}:
            raise ValueError("PASSWORD_POLICY debe ser 'basic' o 'strong'.")
        return limpio

    @field_validator("knowledge_mutation_policy")
    @classmethod
    def validar_knowledge_policy(cls, value: str) -> str:
        limpio = (value or "open").strip().lower()
        if limpio not in {"open", "curators_only"}:
            raise ValueError(
                "KNOWLEDGE_MUTATION_POLICY debe ser 'open' o 'curators_only'."
            )
        return limpio

    @field_validator("auth_cookie_samesite")
    @classmethod
    def validar_samesite(cls, value: str) -> str:
        limpio = (value or "lax").strip().lower()
        if limpio not in {"lax", "strict", "none"}:
            raise ValueError("AUTH_COOKIE_SAMESITE debe ser lax|strict|none.")
        return limpio

    @model_validator(mode="after")
    def validar_secreto_jwt_y_urls(self) -> "Settings":
        enforce = self.jwt_secret_enforce
        if enforce is None:
            enforce = self.es_produccion
        secreto = (self.jwt_secret or "").strip()
        debil = (
            not secreto
            or secreto == JWT_DEFAULT_SECRET
            or len(secreto) < 32
        )
        if enforce and debil:
            raise ValueError(
                "JWT_SECRET debe definirse con al menos 32 caracteres y no puede "
                "usar el valor por defecto en producción. "
                "Genera uno con: openssl rand -hex 32. "
                "Rollback de emergencia: JWT_SECRET_ENFORCE=false"
            )
        if debil and not enforce:
            _logger.warning(
                "JWT_SECRET débil o por defecto en APP_ENV=%s. "
                "No uses este valor fuera de desarrollo local.",
                self.app_env,
            )
        enforce_urls = self.url_allowlist_enforce
        if enforce_urls is None:
            enforce_urls = self.es_produccion
        if enforce_urls:
            _validar_url_permitida(
                self.senamhi_wis2_base_url,
                HOSTS_SENAMHI_PERMITIDOS,
                "SENAMHI_WIS2_BASE_URL",
            )
            _validar_url_permitida(
                self.ollama_base_url,
                HOSTS_OLLAMA_PERMITIDOS,
                "OLLAMA_BASE_URL",
                esquemas_extra={"http"},
            )
        return self

    @property
    def es_produccion(self) -> bool:
        return (self.app_env or "").strip().lower() == "production"

    @property
    def openapi_habilitado(self) -> bool:
        if self.force_openapi:
            return True
        return not self.es_produccion

    @property
    def health_incluye_detalle(self) -> bool:
        if self.health_detailed is not None:
            return self.health_detailed
        return not self.es_produccion

    @property
    def curator_email_set(self) -> set[str]:
        emails: set[str] = set()
        for parte in (self.knowledge_curator_emails or "").split(","):
            limpio = parte.strip().lower()
            if limpio:
                emails.add(limpio)
        return emails

    @property
    def cors_origin_list(self) -> list[str]:
        """Orígenes exactos. Un asterisco suelto no entra; el dominio de Pages sí."""
        origins: list[str] = []
        for origin in self.cors_origins.split(","):
            limpio = origin.strip().rstrip("/")
            if not limpio or limpio == PATRON_DESPLIEGUE_PAGES:
                continue
            if "*" in limpio:
                continue
            if limpio not in origins:
                origins.append(limpio)
        if not origins:
            origins.append(ORIGEN_LOCAL)
        if ORIGEN_PAGES not in origins:
            origins.append(ORIGEN_PAGES)
        return origins

    @property
    def cors_origin_regex(self) -> str:
        """Un solo nivel bajo agro-asistente.pages.dev, solo por HTTPS."""
        return REGEX_DESPLIEGUE_PAGES

    @property
    def mysql_url(self) -> str:
        user = quote_plus((self.mysql_user or "").strip())
        password = quote_plus(self.mysql_password) if self.mysql_password else ""
        host = (self.mysql_host or "localhost").strip()
        database = (self.mysql_database or "").strip()
        if password:
            auth = f"{user}:{password}"
        else:
            auth = user
        return (
            f"mysql+pymysql://{auth}@{host}:{self.mysql_port}/"
            f"{database}?charset=utf8mb4"
        )


def _validar_url_permitida(
    url: str,
    hosts: frozenset[str],
    nombre: str,
    esquemas_extra: set[str] | None = None,
) -> None:
    from urllib.parse import urlparse

    bruto = (url or "").strip()
    if not bruto:
        raise ValueError(f"{nombre} no puede estar vacío.")
    partes = urlparse(bruto)
    esquemas = {"https"} | (esquemas_extra or set())
    if partes.scheme not in esquemas:
        raise ValueError(f"{nombre} debe usar un esquema permitido: {sorted(esquemas)}")
    host = (partes.hostname or "").lower()
    if host not in hosts:
        raise ValueError(
            f"{nombre} apunta a un host no permitido ({host or 'sin-host'}). "
            f"Permitidos: {sorted(hosts)}. "
            "Rollback: URL_ALLOWLIST_ENFORCE=false"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
