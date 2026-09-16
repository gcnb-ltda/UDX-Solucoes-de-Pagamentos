from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.companies import router as companies_router
from app.routes.health import router as health_router
from app.routes.onboarding import router as onboarding_router
from app.routes.payments import router as payments_router
from app.routes.users import router as users_router

app = FastAPI(
    title="UDX Solucoes de Pagamentos API",
    version="0.2.0",
    description="API do MVP da UDX Solucoes de Pagamentos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(payments_router, prefix=settings.api_v1_prefix)
