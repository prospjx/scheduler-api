from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.clients import (
    analyze_schedule_with_ai,
    fetch_single_course,
    get_courses_data,
    get_student_profile,
)


@pytest.mark.asyncio
async def test_get_student_profile_success():
    mock_data = {"student_id": "123", "name": "Alice"}
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = httpx.Response(
            200, json=mock_data, request=httpx.Request("GET", "http://test")
        )
        mock_get.return_value = mock_response

        result = await get_student_profile("123")
        assert result == mock_data


@pytest.mark.asyncio
async def test_get_student_profile_error():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = httpx.Response(404, request=httpx.Request("GET", "http://test"))
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await get_student_profile("nonexistent")


@pytest.mark.asyncio
async def test_fetch_single_course_found():
    mock_course = {"course_id": "CS-101", "title": "Intro"}
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200, json=mock_course, request=httpx.Request("GET", "http://test")
    )

    result = await fetch_single_course(mock_client, "CS-101")
    assert result == mock_course


@pytest.mark.asyncio
async def test_fetch_single_course_not_found():
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        404, request=httpx.Request("GET", "http://test")
    )

    result = await fetch_single_course(mock_client, "UNKNOWN")
    assert result is None


@pytest.mark.asyncio
async def test_get_courses_data():
    course1 = {"course_id": "CS-101"}
    with patch("src.clients.fetch_single_course", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = lambda client, cid: (
            course1 if cid == "CS-101" else None
        )

        results = await get_courses_data(["CS-101", "MISSING"])
        assert len(results) == 1
        assert results[0]["course_id"] == "CS-101"


@pytest.mark.asyncio
async def test_analyze_schedule_with_ai():
    mock_ai_result = {"summary": "Optimal schedule", "warnings": [], "suggestions": []}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            200, json=mock_ai_result, request=httpx.Request("POST", "http://test")
        )

        result = await analyze_schedule_with_ai({"student_id": "1"}, {"Monday": []})
        assert result == mock_ai_result
