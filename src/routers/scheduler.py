from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.schemas import GenerateScheduleRequest, ScheduleResponse, StudentSchedulesResponse
from src.services import create_optimized_schedule, get_schedule_by_id, get_schedules_for_student

router = APIRouter(
    prefix="/scheduler",
    tags=["Scheduler"]
)

@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(request: GenerateScheduleRequest, db: Session = Depends(get_db)):
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
