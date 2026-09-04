from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from typing import Dict, Any, List

from src.schemas import GenerateScheduleRequest
from src.models import Schedule
from src.clients import get_student_profile, get_courses_data, analyze_schedule_with_ai

def _times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    # Lexicographical comparison works perfectly for HH:MM format (24-hour)
    return max(start1, start2) < min(end1, end2)

async def create_optimized_schedule(db: Session, request: GenerateScheduleRequest) -> Dict[str, Any]:
    # 1. Fetch external data (Student profile & Course details)
    try:
        student_profile = await get_student_profile(request.student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to fetch student profile.")
    
    courses_data = await get_courses_data(request.selected_course_ids)
    if not courses_data:
        raise HTTPException(status_code=400, detail="Could not fetch any of the requested courses from Course API.")

    # 2. Build schedule (Greedy algorithm with conflict detection)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    weekly_schedule = {day: [] for day in days}
    total_credits = 0
    
    for course in courses_data:
        course_id = course.get("course_id")
        title = course.get("title")
        credits = course.get("credits", 0)
        timeslots = course.get("timeslots", [])
        
        # We assume a fixed list of timeslots per course for this MVP
        for ts in timeslots:
            day = ts.get("day")
            if day not in weekly_schedule:
                continue
                
            start = ts.get("start_time")
            end = ts.get("end_time")
            location = ts.get("location")
            
            # Conflict check
            for existing_class in weekly_schedule[day]:
                if _times_overlap(start, end, existing_class["start_time"], existing_class["end_time"]):
                    raise HTTPException(
                        status_code=409, 
                        detail=f"Schedule Conflict: {course_id} overlaps with {existing_class['course_id']} on {day} at {start}-{end}."
                    )
            
            # No conflict, add to schedule
            weekly_schedule[day].append({
                "course_id": course_id,
                "title": title,
                "start_time": start,
                "end_time": end,
                "location": location
            })
            
        total_credits += credits

    # 3. Call AI Assistant for smart feedback
    try:
        # Pass the constructed layout and student preferences to the AI
        ai_insights = await analyze_schedule_with_ai(student_profile, weekly_schedule)
    except Exception:
        # Fallback if AI fails (don't block the user from getting their schedule)
        ai_insights = {
            "summary": "AI Assistant unavailable.",
            "warnings": [],
            "suggestions": []
        }

    # 4. Save to Database
    db_schedule = Schedule(
        student_id=request.student_id,
        term=request.term,
        status="optimized",
        ai_insights=ai_insights,
        weekly_schedule=weekly_schedule,
        total_credits=total_credits
    )
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    # 5. Construct and return dictionary matching the ScheduleResponse schema
    return {
        "schedule_id": db_schedule.schedule_id,
        "student_id": db_schedule.student_id,
        "term": db_schedule.term,
        "status": db_schedule.status,
        "ai_insights": db_schedule.ai_insights,
        "weekly_schedule": db_schedule.weekly_schedule,
        "total_credits": db_schedule.total_credits,
        "created_at": db_schedule.created_at
    }

def get_schedule_by_id(db: Session, schedule_id: str):
    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail=f"Schedule {schedule_id} not found.")
    
    # Return as dict matching ScheduleResponse
    return {
        "schedule_id": schedule.schedule_id,
        "student_id": schedule.student_id,
        "term": schedule.term,
        "status": schedule.status,
        "ai_insights": schedule.ai_insights,
        "weekly_schedule": schedule.weekly_schedule,
        "total_credits": schedule.total_credits,
        "created_at": schedule.created_at
    }

def get_schedules_for_student(db: Session, student_id: str):
    schedules = db.query(Schedule).filter(Schedule.student_id == student_id).all()
    # Format according to StudentSchedulesResponse
    return {
        "student_id": student_id,
        "schedules": [
            {
                "schedule_id": s.schedule_id,
                "term": s.term,
                "total_credits": s.total_credits,
                "created_at": s.created_at
            }
            for s in schedules
        ]
    }
