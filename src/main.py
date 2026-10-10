import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from src.database import Base, engine
from src.routers import scheduler

# Create database tables on startup (in production, use Alembic migrations instead)
Base.metadata.create_all(bind=engine)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "handler", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "handler"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Any additional startup logic (like establishing shared HTTP connections) could go here
    yield
    # Shutdown logic goes here


app = FastAPI(
    title="Scheduler API",
    version="1.0.0",
    description="Orchestrates schedule generation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
    except Exception:
        status_code = "500"
        raise
    finally:
        duration = time.time() - start_time
        path = request.url.path
        REQUEST_COUNT.labels(
            method=request.method, handler=path, status=status_code
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, handler=path).observe(duration)
    return response


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Register the routes with the API v1 prefix
app.include_router(scheduler.router, prefix="/api/v1")
app.include_router(scheduler.proxy_router, prefix="/api/v1")



@app.get("/health")
def health_check():
    """Simple health check endpoint for Kubernetes probes."""
    return {"status": "ok"}
