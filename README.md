# Scheduler Engine & Gateway Microservice (`schedulerapi`)

The central orchestration microservice for the **Smart Course Scheduler (SCS)** platform. It generates conflict-free, optimized class schedules using a constraint-satisfaction backtracking algorithm and serves as the **API Gateway** proxy for CloudFront frontend integration.

---

## Architecture & Gateway Pattern

In the production Kubernetes cluster, `schedulerapi` is exposed via a dedicated Classic Load Balancer (`LoadBalancer` service) mapped to CloudFront's `/api/*` cache behavior. It reverse-proxies requests to internal cluster services:

```mermaid
graph LR
    CF["CloudFront CDN (/api/*)"] --> ELB["AWS Classic ELB"]
    ELB --> SCH["Scheduler API (Gateway)"]
    SCH -->|"Internal ClusterIP:8001"| C["Course API"]
    SCH -->|"Internal ClusterIP:8002"| S["Student API"]
    SCH -->|"Internal ClusterIP:8003"| AI["AI Assistant API"]
```

---

## Features

- **Backtracking CSP Scheduler**:
  - Validates time slot overlaps across multi-day meetings.
  - Ensures semester credit limits (min/max) are respected.
  - Enforces prerequisite criteria against the student's historical transcript.
- **Unified Gateway Routing**:
  - `/api/v1/courses/*` $\rightarrow$ proxied to `courseapi-service:8001`
  - `/api/v1/students/*` $\rightarrow$ proxied to `studentapi-service:8002`
  - `/api/v1/analyze/*` $\rightarrow$ proxied to `ai-assistant-api-service:8003` (with 60-second read timeout for LLM synthesis)
- **Observability**: Exposes `/metrics` for Prometheus scraping (request counters, latency histograms).

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/scheduler/generate` | Generates an optimized course schedule for a student. |
| `GET` | `/api/v1/scheduler/{schedule_id}` | Retrieves a previously calculated schedule. |
| `GET` | `/api/v1/scheduler/student/{student_id}` | Lists all saved schedules for a student. |
| `ANY` | `/api/v1/courses/{path}` | Gateway reverse-proxy to Course API. |
| `ANY` | `/api/v1/students/{path}` | Gateway reverse-proxy to Student API. |
| `ANY` | `/api/v1/analyze/{path}` | Gateway reverse-proxy to AI Assistant API. |
| `GET` | `/metrics` | Prometheus metrics scrape target. |
| `GET` | `/health` | Kubernetes health check probe. |

---

## Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/scheduler_db` | PostgreSQL database connection string. |
| `COURSE_API_URL` | `http://courseapi-service:8001/api/v1` | Internal Course API service address. |
| `STUDENT_API_URL` | `http://studentapi-service:8002/api/v1` | Internal Student API service address. |
| `AI_ASSISTANT_API_URL` | `http://ai-assistant-api-service:8003/api/v1` | Internal AI Assistant API address. |
| `PORT` | `8000` | HTTP listen port. |
| `HOST` | `0.0.0.0` | Host bind address. |

---

## Local Development

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running Tests
```bash
pytest tests/ -v
```

---

## Deployment

Packaged as a Helm chart inside `gitops/charts/schedulerapi`:
```bash
docker build -t ghcr.io/prospjx/scheduler-api:latest .
helm upgrade --install schedulerapi ../gitops/charts/schedulerapi
```
