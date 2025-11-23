# FastAPI REST API Documentation

## Overview

Comprehensive REST API for the SaaS BI Agent system with async request handling, background tasks, WebSocket support, and comprehensive monitoring.

## Base URL

```
http://localhost:8000
```

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### Analysis Endpoints

#### POST `/api/v1/analysis/trigger`

Trigger a new analysis.

**Request Body:**
```json
{
  "week_number": 25,
  "analysis_type": "comprehensive",
  "user_id": "user-123",
  "agent_types": ["revenue", "product", "support"]
}
```

**Response:**
```json
{
  "session_id": "session-uuid",
  "status": "queued",
  "progress": 0,
  "estimated_time_remaining_seconds": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/analysis/{session_id}`

Get analysis result by session ID.

**Response:**
```json
{
  "session_id": "session-uuid",
  "week_number": 25,
  "report": {...},
  "quality_score": 0.92,
  "execution_time_ms": 5000,
  "cache_efficiency": 0.75,
  "agents_executed": ["revenue", "product", "support"],
  "hitl_escalations": 0,
  "guardrail_violations": 0,
  "generated_at": "2024-01-01T00:00:00Z",
  "metadata": {...}
}
```

#### GET `/api/v1/analysis/{session_id}/status`

Get analysis status and progress.

**Response:**
```json
{
  "session_id": "session-uuid",
  "status": "running",
  "progress": 45,
  "current_step": "Executing analytical agents",
  "estimated_time_remaining_seconds": 30,
  "error_message": null,
  "result": null
}
```

#### WebSocket `/api/v1/analysis/{session_id}/ws`

Real-time updates for analysis progress.

**Events:**
- `analysis_started`: Analysis has started
- `progress_update`: Progress update with step information
- `agent_started`: Agent execution started
- `agent_completed`: Agent execution completed
- `guardrail_check`: Guardrail check performed
- `evaluation_complete`: Evaluation completed
- `analysis_completed`: Analysis completed with result
- `analysis_failed`: Analysis failed with error

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/session-uuid/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event);
  console.log('Data:', data);
};
```

### Session Endpoints

#### GET `/api/v1/sessions`

Get list of sessions.

**Query Parameters:**
- `limit` (int, default: 100): Maximum number of sessions
- `offset` (int, default: 0): Offset for pagination

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-uuid",
      "session_type": "weekly_analysis_comprehensive",
      "user_id": "user-123",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "ended_at": "2024-01-01T00:05:00Z"
    }
  ],
  "total": 100
}
```

#### GET `/api/v1/sessions/{session_id}`

Get session by ID.

**Response:**
```json
{
  "session_id": "session-uuid",
  "session_type": "weekly_analysis_comprehensive",
  "user_id": "user-123",
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "ended_at": "2024-01-01T00:05:00Z"
}
```

#### POST `/api/v1/sessions`

Create a new session.

**Request Body:**
```json
{
  "session_type": "ad_hoc",
  "user_id": "user-123"
}
```

#### DELETE `/api/v1/sessions/{session_id}`

Delete a session.

### Cache Endpoints

#### GET `/api/v1/cache/stats`

Get cache performance statistics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
{
  "prompt_cache_hits": 1500,
  "prompt_cache_misses": 500,
  "agent_cache_hits": 800,
  "agent_cache_misses": 200,
  "total_tokens_saved": 50000,
  "cache_hit_rate": 0.75,
  "period_days": 7
}
```

#### GET `/api/v1/cache/performance`

Get cache performance metrics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
{
  "average_cache_hit_time_ms": 50.0,
  "average_cache_miss_time_ms": 2000.0,
  "cache_efficiency": 0.75,
  "total_requests": 3000,
  "period_days": 7
}
```

#### DELETE `/api/v1/cache/clear`

Clear all cache entries.

### Monitoring Endpoints

#### GET `/api/v1/monitoring/agents`

Get agent performance statistics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
[
  {
    "agent_type": "revenue",
    "total_executions": 100,
    "average_execution_time_ms": 1500.0,
    "success_rate": 0.95,
    "average_confidence": 0.88
  }
]
```

#### GET `/api/v1/monitoring/guardrails`

Get guardrail effectiveness statistics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
{
  "total_checks": 500,
  "violations": 25,
  "blocks": 5,
  "escalations": 10,
  "violation_rate": 0.05,
  "period_days": 7
}
```

#### GET `/api/v1/monitoring/hitl`

Get HITL performance statistics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
{
  "pending": 2,
  "approved": 50,
  "rejected": 5,
  "modified": 3,
  "average_resolution_time_minutes": 15.5,
  "period_days": 7
}
```

#### GET `/api/v1/monitoring/gemini-usage`

Get Gemini API usage statistics.

**Query Parameters:**
- `days` (int, default: 7): Number of days to look back

**Response:**
```json
{
  "total_requests": 1000,
  "total_tokens_input": 500000,
  "total_tokens_output": 200000,
  "cached_requests": 750,
  "tokens_saved": 300000,
  "average_tokens_per_request": 700.0,
  "period_days": 7
}
```

### HITL Endpoints

#### GET `/api/v1/hitl/pending`

Get pending HITL requests.

**Query Parameters:**
- `limit` (int, default: 10): Maximum number of requests

**Response:**
```json
[
  {
    "request_id": "hitl-uuid",
    "session_id": "session-uuid",
    "escalation_reason": "High-risk guardrail violations",
    "risk_score": 0.85,
    "created_at": "2024-01-01T00:00:00Z",
    "review_url": "https://app.example.com/review/session-uuid"
  }
]
```

#### POST `/api/v1/hitl/{escalation_id}/resolve`

Resolve a HITL escalation.

**Request Body:**
```json
{
  "decision": "approved",
  "feedback": "Looks good, approved",
  "modifications": null,
  "human_reviewer": "user-456"
}
```

**Response:**
```json
{
  "message": "HITL request hitl-uuid resolved",
  "decision": "approved",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Features

### Async Request Handling

All endpoints are async and use FastAPI's async capabilities for optimal performance.

### Background Tasks

Long-running analyses are executed in background tasks:
- Analysis is queued immediately
- Status can be checked via `/status` endpoint
- WebSocket provides real-time updates

### WebSocket Support

Real-time progress updates via WebSocket:
- Subscribe to session-specific updates
- Receive events as analysis progresses
- Automatic reconnection handling

### CORS Middleware

CORS middleware configured for frontend integration:
- Configurable origins
- Credentials support
- All methods and headers allowed

### Request Validation

All requests validated with Pydantic:
- Type checking
- Field validation
- Clear error messages

### Error Handling

Comprehensive error handling:
- HTTP status codes
- Detailed error messages
- Error logging

### API Documentation

Automatic API documentation:
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- OpenAPI schema at `/openapi.json`

## Usage Examples

### Trigger Analysis

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/analysis/trigger',
    json={
        'week_number': 25,
        'analysis_type': 'comprehensive',
        'user_id': 'user-123'
    }
)

session_id = response.json()['session_id']
```

### Check Status

```python
response = requests.get(
    f'http://localhost:8000/api/v1/analysis/{session_id}/status'
)

status = response.json()
print(f"Status: {status['status']}, Progress: {status['progress']}%")
```

### Get Result

```python
response = requests.get(
    f'http://localhost:8000/api/v1/analysis/{session_id}'
)

result = response.json()
print(f"Quality Score: {result['quality_score']}")
```

### WebSocket Client

```python
import asyncio
import websockets
import json

async def listen_to_updates(session_id):
    uri = f'ws://localhost:8000/api/v1/analysis/{session_id}/ws'
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Event: {data['event']}")
            if data['event'] == 'analysis_completed':
                break

asyncio.run(listen_to_updates('session-uuid'))
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

Common status codes:
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

Currently no rate limiting implemented. In production, add rate limiting middleware.

## Authentication

Currently no authentication implemented. In production, add authentication middleware (JWT, OAuth, etc.).

## Running the API

```bash
# Development
uvicorn api.main:app --reload

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Variables

- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_CREDENTIALS_PATH`: Path to Google service account JSON
- `HITL_MODE`: `demo` or `production` (for HITL auto-approval)

