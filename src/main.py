from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.routers import scheduler
from src.database import engine, Base

# Create database tables on startup (in production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Any additional startup logic (like establishing shared HTTP connections) could go here
    yield
    # Shutdown logic goes here

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Scheduler API",
    version="1.0.0",
    description="Orchestrates schedule generation.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes with the API v1 prefix
app.include_router(scheduler.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """Simple health check endpoint for Kubernetes probes."""
    return {"status": "ok"}
