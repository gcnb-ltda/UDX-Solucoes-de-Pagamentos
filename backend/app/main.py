from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.backoffice import router as backoffice_router
from app.routes.companies import router as companies_router
from app.routes.health import router as health_router
from app.routes.onboarding import router as onboarding_router
from app.routes.payments import router as payments_router
from app.routes.pix import router as pix_router
from app.routes.users import router as users_router

app = FastAPI(title="UDX Solucoes de Pagamentos API", version="0.3.0", description="API do MVP da UDX Solucoes de Pagamentos.")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    if settings.app_env.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(health_router)
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(payments_router, prefix=settings.api_v1_prefix)
app.include_router(pix_router, prefix=settings.api_v1_prefix)
app.include_router(backoffice_router, prefix=settings.api_v1_prefix)
