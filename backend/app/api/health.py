from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying application status and database connectivity."""
    db_status = "error"
    pgvector_status = "unavailable"
    version = ""
    try:
        # Check standard DB connectivity
        db.execute(text("SELECT 1;"))
        db_status = "connected"

        # Try fetching version
        try:
            result = db.execute(text("SELECT version();")).fetchone()
            if result:
                version = result[0]
        except Exception:
            try:
                result = db.execute(text("SELECT sqlite_version();")).fetchone()
                if result:
                    version = f"SQLite {result[0]}"
            except Exception:
                version = "unknown"

        # Check pgvector readiness
        try:
            vector_res = db.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            ).fetchone()
            if vector_res:
                pgvector_status = "ready"
        except Exception:
            pgvector_status = "unavailable"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "version": version,
            "pgvector": pgvector_status,
        },
    }
