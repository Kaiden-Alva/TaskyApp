from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from backend.api.v1 import user, task_api
from backend.core.config import config
from backend.core.logging import setup_logging
from backend.db.schema import Base, engine, SessionLocal

setup_logging()

# Initialize database schema
Base.metadata.create_all(bind=engine)

# Initialize database with seed data (idempotent)
try:
    from backend.db.init_db import init_database
    init_database()
except Exception as e:
    print(f"⚠️  Database initialization failed: {e}")
    print("   Continuing anyway - database may need manual initialization")

app = FastAPI(title=config.app_name, version=config.app_version)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to monitor database connectivity"""
    try:
        # Test database connection
        from backend.db.schema import SessionLocal
        from sqlalchemy import text
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        finally:
            session.close()
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# Register routes
app.include_router(user.router, prefix="/api/v1", tags=["users"])
app.include_router(task_api.router, prefix="/api/v1", tags=["tasks"])

if __name__ == "__main__":
    if config.use_cli:
        # Run CLI
        from backend.services.orchestrator import Orchestrator
        from backend.services.cli import CLI
        if config.use_db:
            from backend.db.schema import SessionLocal
            db_session = SessionLocal()
            orchestrator = Orchestrator(db_session, config)
        else:
            orchestrator = Orchestrator(config=config)
        cli = CLI(orchestrator)
        cli.run_console_cycle()

    else:
        # Run FastAPI app with Uvicorn
        import uvicorn
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=config.debug)