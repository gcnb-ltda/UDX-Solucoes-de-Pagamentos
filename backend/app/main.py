from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.health import router as health_router
from app.routes.payments import router as payments_router

app = FastAPI(
    title="UDX Solucoes de Pagamentos API",
    version="0.1.0",
    description="API inicial do MVP da UDX Solucoes de Pagamentos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(payments_router, prefix="/api/v1")
