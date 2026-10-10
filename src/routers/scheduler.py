import httpx
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from src.clients import AI_ASSISTANT_API_URL, COURSE_API_URL, STUDENT_API_URL
from src.database import get_db
from src.schemas import (
    GenerateScheduleRequest,
    ScheduleResponse,
    StudentSchedulesResponse,
)
from src.services import (
    create_optimized_schedule,
    get_schedule_by_id,
    get_schedules_for_student,
)

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])
proxy_router = APIRouter(tags=["Gateway Proxy"])


@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: GenerateScheduleRequest, db: Session = Depends(get_db)
):
    """Generates an optimized course schedule for a student using AI insights."""
    return await create_optimized_schedule(db, request)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Retrieves a previously generated schedule by its ID."""
    return get_schedule_by_id(db, schedule_id)


@router.get("/student/{student_id}", response_model=StudentSchedulesResponse)
def get_student_schedules(student_id: str, db: Session = Depends(get_db)):
    """Retrieves all schedules for a specific student."""
    return get_schedules_for_student(db, student_id)


# Gateway Reverse-Proxy endpoints so CloudFront's single /api/* origin serves all frontend calls
@proxy_router.api_route("/courses{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_courses(request: Request, path: str):
    target_url = f"{COURSE_API_URL}/courses{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        rp = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=dict(request.query_params),
        )
    return Response(
        content=rp.content,
        status_code=rp.status_code,
        media_type=rp.headers.get("content-type"),
    )


@proxy_router.api_route(
    "/students{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def proxy_students(request: Request, path: str):
    target_url = f"{STUDENT_API_URL}/students{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        rp = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=dict(request.query_params),
        )
    return Response(
        content=rp.content,
        status_code=rp.status_code,
        media_type=rp.headers.get("content-type"),
    )


@proxy_router.api_route("/analyze{path:path}", methods=["GET", "POST"])
async def proxy_analyze(request: Request, path: str):
    target_url = f"{AI_ASSISTANT_API_URL}/analyze{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=60.0) as client:
        rp = await client.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            content=body,
            params=dict(request.query_params),
        )
    return Response(
        content=rp.content,
        status_code=rp.status_code,
        media_type=rp.headers.get("content-type"),
    )
