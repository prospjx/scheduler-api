import os
import httpx
import asyncio
from typing import Dict, Any, List

# In EKS, these URLs would resolve via Kubernetes internal service names (e.g., http://course-api.default.svc.cluster.local)
COURSE_API_URL = os.getenv("COURSE_API_URL", "http://localhost:8001/api/v1")
STUDENT_API_URL = os.getenv("STUDENT_API_URL", "http://localhost:8002/api/v1")
AI_ASSISTANT_API_URL = os.getenv("AI_ASSISTANT_API_URL", "http://localhost:8003/api/v1")

async def get_student_profile(student_id: str) -> Dict[str, Any]:
    """Fetches the student profile and preferences from the Student API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STUDENT_API_URL}/students/{student_id}")
        # Let errors bubble up to be handled by the route or service layer
        response.raise_for_status()
        return response.json()

async def fetch_single_course(client: httpx.AsyncClient, course_id: str) -> Dict[str, Any]:
    response = await client.get(f"{COURSE_API_URL}/courses/{course_id}")
    if response.status_code == 200:
        return response.json()
    return None

async def get_courses_data(course_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetches data for multiple courses from the Course API concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_single_course(client, cid) for cid in course_ids]
        results = await asyncio.gather(*tasks)
        # Filter out None values for courses that weren't found
        return [course for course in results if course is not None]

async def analyze_schedule_with_ai(student_profile: Dict[str, Any], schedule: Dict[str, Any]) -> Dict[str, Any]:
    """Sends the proposed schedule to the AI Assistant API for smart feedback and insights."""
    payload = {
        "student_profile": student_profile,
        "schedule": schedule
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        # We increase the timeout here since LLM generation can sometimes take a few seconds
        response = await client.post(f"{AI_ASSISTANT_API_URL}/analyze", json=payload)
        response.raise_for_status()
        return response.json()
