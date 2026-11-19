"""API router assembly."""

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.business import router as business_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.investments import router as investments_router
from app.api.routes.nudges import router as nudges_router
from app.api.routes.scams import router as scams_router
from app.api.routes.system import router as system_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.tax import router as tax_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.dues import router as dues_router

api_router = APIRouter()

# Root-level health endpoint (unversioned, per contract section 15).
api_router.include_router(health_router)

# Versioned routes under /api/v1.
api_router.include_router(auth_router, prefix="/api/v1")
api_router.include_router(transactions_router, prefix="/api/v1")
api_router.include_router(ingestion_router, prefix="/api/v1")
api_router.include_router(dues_router, prefix="/api/v1")
api_router.include_router(subscriptions_router, prefix="/api/v1")
api_router.include_router(nudges_router, prefix="/api/v1")
api_router.include_router(scams_router, prefix="/api/v1")
api_router.include_router(tax_router, prefix="/api/v1")
api_router.include_router(business_router, prefix="/api/v1")
api_router.include_router(investments_router, prefix="/api/v1")
api_router.include_router(dashboard_router, prefix="/api/v1")
api_router.include_router(system_router, prefix="/api/v1")
