from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class GenerateScheduleRequest(BaseModel):
    student_id: str
    term: str
    selected_course_ids: List[str]

class AIInsights(BaseModel):
    summary: str
    warnings: List[str]
    suggestions: List[str]

class CourseSchedule(BaseModel):
    course_id: str
    title: str
    start_time: str
    end_time: str
    location: str

class ScheduleResponse(BaseModel):
    schedule_id: str
    student_id: str
    term: str
    status: str
    ai_insights: AIInsights
    weekly_schedule: Dict[str, List[CourseSchedule]]
    total_credits: int
    created_at: datetime

class ScheduleSummary(BaseModel):
    schedule_id: str
    term: str
    total_credits: int
    created_at: datetime

class StudentSchedulesResponse(BaseModel):
    student_id: str
    schedules: List[ScheduleSummary]
