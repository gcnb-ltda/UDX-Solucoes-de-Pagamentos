import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.backoffice import router as backoffice_router
from app.routes.companies import router as companies_router
from app.routes.health import router as health_router
from app.routes.onboarding import router as onboarding_router
from app.routes.payments import router as payments_router
from app.routes.pix import router as pix_router
from app.routes.pix_charges import router as pix_charges_router
from app.routes.provider_webhooks import router as provider_webhooks_router
from app.routes.reconciliation import router as reconciliation_router
from app.routes.users import router as users_router

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("udx.http")

production = settings.app_env.lower() == "production"
app = FastAPI(
    title="UDX Solucoes de Pagamentos API",
    version="0.4.0",
    description="API da UDX Solucoes de Pagamentos.",
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
)


@app.middleware("http")
async def request_context_and_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            json.dumps(
                {
                    "event": "http.error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                }
            )
        )
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        json.dumps(
            {
                "event": "http.request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    if production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(health_router)
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(payments_router, prefix=settings.api_v1_prefix)
app.include_router(pix_router, prefix=settings.api_v1_prefix)
app.include_router(pix_charges_router, prefix=settings.api_v1_prefix)
app.include_router(provider_webhooks_router, prefix=settings.api_v1_prefix)
app.include_router(backoffice_router, prefix=settings.api_v1_prefix)
app.include_router(reconciliation_router, prefix=settings.api_v1_prefix)
