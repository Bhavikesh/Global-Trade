from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.organizations import router as organizations_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
)

# CORS configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["Health"])
app.include_router(users_router, prefix=f"{settings.API_V1_PREFIX}/v1")
app.include_router(organizations_router, prefix=f"{settings.API_V1_PREFIX}/v1")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
        "health": f"{settings.API_V1_PREFIX}/health",
    }
