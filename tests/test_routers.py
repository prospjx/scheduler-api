from unittest.mock import AsyncMock, patch

from src.models import Schedule


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_schedule_by_id_endpoint_success(client, db_session):
    schedule = Schedule(
        schedule_id="sched-abc-123",
        student_id="student-99",
        term="Fall 2026",
        status="optimized",
        ai_insights={"summary": "Looks good", "warnings": [], "suggestions": []},
        weekly_schedule={"Monday": []},
        total_credits=4,
    )
    db_session.add(schedule)
    db_session.commit()

    response = client.get("/api/v1/scheduler/sched-abc-123")
    assert response.status_code == 200
    data = response.json()
    assert data["schedule_id"] == "sched-abc-123"
    assert data["student_id"] == "student-99"
    assert data["term"] == "Fall 2026"
    assert data["total_credits"] == 4


def test_get_schedule_by_id_endpoint_not_found(client):
    response = client.get("/api/v1/scheduler/unknown-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule unknown-id not found."


def test_get_student_schedules_endpoint(client, db_session):
    s1 = Schedule(
        schedule_id="s1",
        student_id="student-bob",
        term="Fall 2026",
        status="optimized",
        ai_insights={},
        weekly_schedule={},
        total_credits=12,
    )
    db_session.add(s1)
    db_session.commit()

    response = client.get("/api/v1/scheduler/student/student-bob")
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "student-bob"
    assert len(data["schedules"]) == 1
    assert data["schedules"][0]["schedule_id"] == "s1"


def test_generate_schedule_endpoint_success(client):
    payload = {
        "student_id": "std-42",
        "term": "Fall 2026",
        "selected_course_ids": ["CS-101"],
    }

    mock_profile = {"student_id": "std-42", "major": "CS"}
    mock_courses = [
        {
            "course_id": "CS-101",
            "title": "CS 101",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:15",
                    "location": "Room 1",
                }
            ],
        }
    ]
    mock_ai = {
        "summary": "Great schedule.",
        "warnings": [],
        "suggestions": [],
    }

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_p, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_c, patch(
        "src.services.analyze_schedule_with_ai", new_callable=AsyncMock
    ) as mock_a:

        mock_p.return_value = mock_profile
        mock_c.return_value = mock_courses
        mock_a.return_value = mock_ai

        response = client.post("/api/v1/scheduler/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "std-42"
        assert data["term"] == "Fall 2026"
        assert data["total_credits"] == 3
        assert len(data["weekly_schedule"]["Monday"]) == 1
        assert data["weekly_schedule"]["Monday"][0]["course_id"] == "CS-101"


def test_generate_schedule_endpoint_validation_error(client):
    # Missing required selected_course_ids field
    payload = {
        "student_id": "std-42",
        "term": "Fall 2026",
    }
    response = client.post("/api/v1/scheduler/generate", json=payload)
    assert response.status_code == 422


def test_generate_schedule_endpoint_conflict_error(client):
    payload = {
        "student_id": "std-42",
        "term": "Fall 2026",
        "selected_course_ids": ["CS-101", "CS-102"],
    }

    mock_profile = {"student_id": "std-42"}
    mock_courses = [
        {
            "course_id": "CS-101",
            "title": "CS 1",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "location": "Room 1",
                }
            ],
        },
        {
            "course_id": "CS-102",
            "title": "CS 2",
            "credits": 3,
            "timeslots": [
                {
                    "day": "Monday",
                    "start_time": "09:30",
                    "end_time": "10:30",
                    "location": "Room 2",
                }
            ],
        },
    ]

    with patch(
        "src.services.get_student_profile", new_callable=AsyncMock
    ) as mock_p, patch(
        "src.services.get_courses_data", new_callable=AsyncMock
    ) as mock_c:

        mock_p.return_value = mock_profile
        mock_c.return_value = mock_courses

        response = client.post("/api/v1/scheduler/generate", json=payload)
        assert response.status_code == 409
        assert "Schedule Conflict" in response.json()["detail"]
