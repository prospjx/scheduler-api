from datetime import datetime

from pydantic import BaseModel


class GenerateScheduleRequest(BaseModel):
    student_id: str
    term: str
    selected_course_ids: list[str]


class AIInsights(BaseModel):
    summary: str
    warnings: list[str]
    suggestions: list[str]


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
    weekly_schedule: dict[str, list[CourseSchedule]]
    total_credits: int
    created_at: datetime


class ScheduleSummary(BaseModel):
    schedule_id: str
    term: str
    total_credits: int
    created_at: datetime


class StudentSchedulesResponse(BaseModel):
    student_id: str
    schedules: list[ScheduleSummary]
