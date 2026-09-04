from sqlalchemy import Column, String, Integer, DateTime, JSON
import uuid
from datetime import datetime
from src.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    schedule_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String, index=True, nullable=False)
    term = Column(String, nullable=False)
    status = Column(String, nullable=False)
    
    # We store the AI insights and the complex weekly schedule as JSON blobs
    # to avoid creating overly normalized tables for a microservice.
    ai_insights = Column(JSON, nullable=True)
    weekly_schedule = Column(JSON, nullable=False)
    
    total_credits = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
