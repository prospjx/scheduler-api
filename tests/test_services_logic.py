from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.models import Schedule
from src.schemas import GenerateScheduleRequest
from src.services import (
    create_optimized_schedule,
    get_schedule_by_id,
    get_schedules_for_student,
)


@pytest.mark.asyncio
async def test_create_optimized_schedule_success(db_session):
    student_id = "student-123"
    request = GenerateScheduleRequest(
        student_id=student_id,
        term="Fall 2026",
        selected_course_ids=["CS-101", "MATH-201"],
    )

    mock_profile = {"student_id": student_id, "major": "CS"}
    mock_courses = [
        {
            "course_id": "CS-101",
            "title": "Intro to CS",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:15",
                    "location": "Room 101",
                }
            ],
        },
        {
            "course_id": "MATH-201",
            "title": "Calculus",
            "credits": 4,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "11:00",
                    "end_time": "12:15",
                    "location": "Room 202",
                }
            ],
        },
    ]
    mock_ai = {
        "summary": "Great schedule balance.",
        "warnings": [],
        "suggestions": ["Add a lunch break"],
    }

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_get_profile, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_get_courses, patch(
        "src.services.analyze_schedule_with_ai", new_callable=AsyncMock
    ) as mock_analyze_ai:

        mock_get_profile.return_value = mock_profile
        mock_get_courses.return_value = mock_courses
        mock_analyze_ai.return_value = mock_ai

        result = await create_optimized_schedule(db_session, request)

        assert result["student_id"] == student_id
        assert result["term"] == "Fall 2026"
        assert result["status"] == "optimized"
        assert result["total_credits"] == 7
        assert result["ai_insights"] == mock_ai
        assert len(result["weekly_schedule"]["Monday"]) == 2
        assert result["schedule_id"] is not None


@pytest.mark.asyncio
async def test_create_optimized_schedule_conflict(db_session):
    student_id = "student-123"
    request = GenerateScheduleRequest(
        student_id=student_id,
        term="Fall 2026",
        selected_course_ids=["CS-101", "CS-102"],
    )

    mock_profile = {"student_id": student_id}
    mock_courses = [
        {
            "course_id": "CS-101",
            "title": "Intro to CS",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "10:00",
                    "end_time": "11:15",
                    "location": "Room 101",
                }
            ],
        },
        {
            "course_id": "CS-102",
            "title": "Data Structures",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "10:30",
                    "end_time": "11:45",
                    "location": "Room 102",
                }
            ],
        },
    ]

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_get_profile, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_get_courses:

        mock_get_profile.return_value = mock_profile
        mock_get_courses.return_value = mock_courses

        with pytest.raises(HTTPException) as exc_info:
            await create_optimized_schedule(db_session, request)

        assert exc_info.value.status_code == 409
        assert "Schedule Conflict" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_optimized_schedule_student_profile_failure(db_session):
    request = GenerateScheduleRequest(
        student_id="non-existent",
        term="Fall 2026",
        selected_course_ids=["CS-101"],
    )

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_get_profile:
        mock_get_profile.side_effect = Exception("Service unavailable")

        with pytest.raises(HTTPException) as exc_info:
            await create_optimized_schedule(db_session, request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Failed to fetch student profile."


@pytest.mark.asyncio
async def test_create_optimized_schedule_courses_not_found(db_session):
    request = GenerateScheduleRequest(
        student_id="student-1",
        term="Fall 2026",
        selected_course_ids=["INVALID-COURSE"],
    )

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_get_profile, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_get_courses:

        mock_get_profile.return_value = {"student_id": "student-1"}
        mock_get_courses.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            await create_optimized_schedule(db_session, request)

        assert exc_info.value.status_code == 400
        assert "Could not fetch any of the requested courses" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_optimized_schedule_ai_fallback(db_session):
    request = GenerateScheduleRequest(
        student_id="student-1",
        term="Fall 2026",
        selected_course_ids=["CS-101"],
    )

    mock_courses = [
        {
            "course_id": "CS-101",
            "title": "Intro to CS",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "location": "Room 101",
                }
            ],
        }
    ]

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_get_profile, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_get_courses, patch(
        "src.services.analyze_schedule_with_ai", new_callable=AsyncMock
    ) as mock_ai:

        mock_get_profile.return_value = {"student_id": "student-1"}
        mock_get_courses.return_value = mock_courses
        mock_ai.side_effect = Exception("AI Timeout")

        result = await create_optimized_schedule(db_session, request)
        assert result["status"] == "optimized"
        assert result["ai_insights"]["summary"] == "AI Assistant unavailable."


def test_get_schedule_by_id_success(db_session):
    schedule = Schedule(
        schedule_id="test-sched-1",
        student_id="student-abc",
        term="Fall 2026",
        status="optimized",
        ai_insights={"summary": "OK", "warnings": [], "suggestions": []},
        weekly_schedule={"Monday": []},
        total_credits=3,
    )
    db_session.add(schedule)
    db_session.commit()

    retrieved = get_schedule_by_id(db_session, "test-sched-1")
    assert retrieved["schedule_id"] == "test-sched-1"
    assert retrieved["student_id"] == "student-abc"
    assert retrieved["total_credits"] == 3


def test_get_schedule_by_id_not_found(db_session):
    with pytest.raises(HTTPException) as exc_info:
        get_schedule_by_id(db_session, "nonexistent-id")
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


def test_get_schedules_for_student(db_session):
    s1 = Schedule(
        schedule_id="sched-1",
        student_id="student-xyz",
        term="Fall 2026",
        status="optimized",
        ai_insights={},
        weekly_schedule={},
        total_credits=12,
    )
    s2 = Schedule(
        schedule_id="sched-2",
        student_id="student-xyz",
        term="Spring 2027",
        status="optimized",
        ai_insights={},
        weekly_schedule={},
        total_credits=15,
    )
    s3 = Schedule(
        schedule_id="sched-3",
        student_id="student-other",
        term="Fall 2026",
        status="optimized",
        ai_insights={},
        weekly_schedule={},
        total_credits=9,
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    res = get_schedules_for_student(db_session, "student-xyz")
    assert res["student_id"] == "student-xyz"
    assert len(res["schedules"]) == 2
    sched_ids = [s["schedule_id"] for s in res["schedules"]]
    assert "sched-1" in sched_ids
    assert "sched-2" in sched_ids
