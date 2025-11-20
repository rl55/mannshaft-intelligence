# SaaS BI Agent System

Production-grade SaaS BI Agent system backend built with Python, FastAPI, and Google Gemini.

## Project Structure

```
saas-bi-agent/
├── agents/              # Agent implementations
├── governance/           # Guardrails, evaluation, HITL
├── cache/               # Cache management
├── api/                 # FastAPI application
├── integrations/       # External integrations (Google Sheets, Gemini)
├── utils/              # Configuration and logging
├── tests/              # Test suite
├── data/               # SQLite database location
├── config.yaml         # Configuration file
└── requirements.txt    # Python dependencies
```

## Features

- **Multi-Agent System**: Specialized agents for revenue, product, support analysis
- **Caching**: Multi-level caching (prompt-level and agent-level) for performance
- **Observability**: Distributed tracing, metrics, and error logging
- **Governance**: Guardrails, evaluation, and human-in-the-loop (HITL) management
- **REST API**: FastAPI-based REST API for agent interactions
- **Google Integration**: Gemini API and Google Sheets (MCP) integration

## Requirements

- Python 3.11+
- See `requirements.txt` for dependencies

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file with:
     ```
     GEMINI_API_KEY=your_gemini_api_key
     GOOGLE_CREDENTIALS_PATH=path/to/service_account.json
     ```
5. Configure `config.yaml` as needed

## Running the Application

Start the FastAPI server:

```bash
python -m api.main
```

Or using uvicorn directly:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

Edit `config.yaml` to configure:
- API settings (host, port, CORS)
- Database path
- Gemini API settings
- Google Sheets credentials
- Cache TTL settings
- Logging configuration

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/analysis/` - Single agent analysis
- `POST /api/v1/analysis/multi` - Multi-agent analysis
- `POST /api/v1/sessions/` - Create session
- `POST /api/v1/sessions/{session_id}/end` - End session
- `GET /api/v1/cache/stats` - Cache statistics
- `POST /api/v1/cache/cleanup` - Cleanup expired cache
- `GET /api/v1/monitoring/agent-performance` - Agent performance metrics
- `GET /api/v1/monitoring/guardrail-effectiveness` - Guardrail metrics
- `GET /api/v1/monitoring/hitl-performance` - HITL performance metrics

## Development

The project uses:
- **FastAPI** for the REST API
- **SQLAlchemy** patterns (currently using raw SQLite via cache_manager)
- **Pydantic** for data validation
- **Google Generative AI SDK** for Gemini integration
- **asyncio** for concurrent agent execution

## License

See LICENSE file for details.

