# Scheduler API Contract

This document defines the REST API contract for the **Scheduler API** in the Smart Course Scheduler system. 

## Base URL
`/api/v1`

---

## 1. Generate Schedule

**Endpoint:** `POST /scheduler/generate`

**Description:** 
Generates an optimized course schedule for a student. It fetches the course catalog data from the **Course API** and student preferences from the **Student API**, builds a conflict-free schedule, runs it through the **AI Assistant API** for analysis, saves it to the database, and returns the final schedule with AI insights to the frontend.

### Request

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer <token>` (if authentication is added later)

**Body:**
```json
{
  "student_id": "uuid-string-of-the-student",
  "term": "Fall 2026",
  "selected_course_ids": [
    "CS-3410",
    "CS-3500",
    "MATH-2310"
  ]
}
```

### Response

**Success (200 OK):**
```json
{
  "schedule_id": "uuid-string-of-the-generated-schedule",
  "student_id": "uuid-string-of-the-student",
  "term": "Fall 2026",
  "status": "success",
  "ai_insights": {
    "summary": "This schedule is well-balanced with a moderate workload.",
    "warnings": [],
    "suggestions": [
      "Your Tuesday is slightly overloaded. Try swapping CS-3500 to a Wednesday section if available."
    ]
  },
  "weekly_schedule": {
    "Monday": [
      {
        "course_id": "CS-3410",
        "title": "Computer Systems",
        "start_time": "10:00",
        "end_time": "11:15",
        "location": "Building A, Room 101"
      }
    ],
    "Tuesday": [
      {
        "course_id": "MATH-2310",
        "title": "Linear Algebra",
        "start_time": "09:00",
        "end_time": "10:15",
        "location": "Building B, Room 204"
      },
      {
        "course_id": "CS-3500",
        "title": "Software Engineering",
        "start_time": "13:00",
        "end_time": "14:15",
        "location": "Building C, Room 301"
      }
    ],
    "Wednesday": [
      {
        "course_id": "CS-3410",
        "title": "Computer Systems",
        "start_time": "10:00",
        "end_time": "11:15",
        "location": "Building A, Room 101"
      }
    ],
    "Thursday": [
      {
        "course_id": "MATH-2310",
        "title": "Linear Algebra",
        "start_time": "09:00",
        "end_time": "10:15",
        "location": "Building B, Room 204"
      },
      {
        "course_id": "CS-3500",
        "title": "Software Engineering",
        "start_time": "13:00",
        "end_time": "14:15",
        "location": "Building C, Room 301"
      }
    ],
    "Friday": []
  },
  "total_credits": 10,
  "created_at": "2026-09-04T17:21:07Z"
}
```

**Client Error (400 Bad Request):**
```json
{
  "error": "InvalidRequest",
  "message": "student_id and selected_course_ids are required."
}
```

**Conflict Error (409 Conflict):**
```json
{
  "error": "ScheduleConflict",
  "message": "Could not generate a valid schedule. CS-3410 and MATH-2310 have mandatory overlapping timeslots."
}
```

---

## 2. Get Schedule by ID

**Endpoint:** `GET /scheduler/{schedule_id}`

**Description:** 
Retrieves a previously generated schedule from the PostgreSQL database using its unique identifier.

### Request

**Path Parameters:**
- `schedule_id` (string): The UUID of the schedule.

### Response

**Success (200 OK):**
*Returns the exact same JSON structure as the `POST /scheduler/generate` success response.*

**Not Found (404 Not Found):**
```json
{
  "error": "NotFound",
  "message": "Schedule with ID {schedule_id} not found."
}
```

---

## 3. Get Student Schedules

**Endpoint:** `GET /scheduler/student/{student_id}`

**Description:** 
Retrieves all schedules previously generated and saved for a specific student.

### Request

**Path Parameters:**
- `student_id` (string): The UUID of the student.

### Response

**Success (200 OK):**
```json
{
  "student_id": "uuid-string-of-the-student",
  "schedules": [
    {
      "schedule_id": "uuid-string",
      "term": "Fall 2026",
      "total_credits": 10,
      "created_at": "2026-09-04T17:21:07Z"
    }
  ]
}
```
