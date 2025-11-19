# SaaS BI Agent System

Production-grade multi-agent business intelligence platform powered by Google Gemini, featuring intelligent caching, distributed tracing, governance, and human-in-the-loop capabilities.

## Overview

The SaaS BI Agent System is a sophisticated agentic framework designed to analyze SaaS business data across multiple dimensions:

- **Revenue Analysis**: MRR, churn, ARPU, growth trends
- **Product Analytics**: Feature usage, adoption, engagement
- **Support Intelligence**: Ticket analysis, customer sentiment
- **Synthesis**: Cross-domain insights and recommendations

### Key Features

✅ **Multi-Agent Architecture** - Specialized agents coordinated by an orchestrator
✅ **Intelligent Caching** - Dual-layer caching (prompt + agent response)
✅ **Distributed Tracing** - Complete observability and performance tracking
✅ **Governance & Guardrails** - Hard and adaptive safety rules
✅ **Human-in-the-Loop** - Automated escalation for edge cases
✅ **Quality Evaluation** - Automated response assessment
✅ **Production-Ready** - FastAPI, structured logging, configuration management

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API                         │
│                    (analysis, sessions, cache)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator   │
                    │     Agent       │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐      ┌──────▼──────┐     ┌─────▼─────┐
    │ Revenue │      │   Product   │     │  Support  │
    │  Agent  │      │    Agent    │     │   Agent   │
    └────┬────┘      └──────┬──────┘     └─────┬─────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            │
                     ┌──────▼──────┐
                     │ Synthesizer │
                     │    Agent    │
                     └──────┬──────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼─────┐    ┌──────▼──────┐    ┌─────▼──────┐
    │  Cache   │    │ Governance  │    │ Observ-    │
    │ Manager  │    │ & Guardrails│    │ ability    │
    └──────────┘    └─────────────┘    └────────────┘
```

## Project Structure

```
saas-bi-agent/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py      # Abstract base class
│   ├── orchestrator.py    # Core orchestrator (TODO)
│   ├── revenue_agent.py   # Revenue analysis (TODO)
│   ├── product_agent.py   # Product analytics (TODO)
│   ├── support_agent.py   # Support intelligence (TODO)
│   └── synthesizer_agent.py # Synthesis agent (TODO)
│
├── governance/            # Governance & guardrails (TODO)
│   ├── __init__.py
│   ├── guardrails.py
│   ├── evaluation.py
│   └── hitl_manager.py
│
├── cache/                 # Caching system
│   ├── __init__.py
│   └── cache_manager.py   # ✓ Implemented
│
├── api/                   # FastAPI application
│   ├── __init__.py
│   ├── main.py           # ✓ FastAPI app
│   ├── routes/           # ✓ API routes
│   │   ├── analysis.py
│   │   ├── sessions.py
│   │   ├── cache.py
│   │   └── monitoring.py
│   └── models/           # ✓ Request/Response models
│       ├── requests.py
│       └── responses.py
│
├── integrations/          # External integrations (TODO)
│   ├── __init__.py
│   ├── google_sheets.py
│   └── gemini_client.py
│
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── config.py         # ✓ Configuration management
│   └── logger.py         # ✓ Structured logging
│
├── tests/                 # Tests (TODO)
├── data/                  # Database & data
│   └── schema.sql        # ✓ Database schema
├── config.yaml           # ✓ Configuration file
├── requirements.txt      # ✓ Python dependencies
└── README.md            # ✓ This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with Gemini API access
- (Optional) Google Sheets API credentials for data integration

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd saas-bi-agent
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure the system**:

Edit `config.yaml` to set your preferences:
```yaml
gemini:
  model: "gemini-2.0-flash-exp"

database:
  path: "data/agent_cache.db"

api:
  host: "0.0.0.0"
  port: 8000
```

5. **Set environment variables** (optional):
```bash
export GEMINI_API_KEY="your-api-key-here"
export AGENT_GEMINI_MODEL="gemini-2.0-flash-exp"
```

6. **Run the API server**:
```bash
cd saas-bi-agent
python -m api.main
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### 1. Create an Analysis Session

```bash
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "weekly_review",
    "user_id": "user-123"
  }'
```

### 2. Run Revenue Analysis

```bash
curl -X POST http://localhost:8000/analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "revenue",
    "data": {
      "period": "2025-Q4",
      "mrr": 1250000,
      "churn_rate": 3.2,
      "arpu": 127
    },
    "context": {
      "analysis_type": "comprehensive"
    }
  }'
```

### 3. Check Cache Statistics

```bash
curl http://localhost:8000/cache/stats?days=7
```

### 4. Health Check

```bash
curl http://localhost:8000/monitoring/health
```

## Configuration

### Environment Variables

Override configuration with environment variables using the `AGENT_` prefix:

```bash
AGENT_GEMINI_MODEL=gemini-2.0-flash-exp
AGENT_DATABASE_PATH=/custom/path/db.sqlite
AGENT_API_PORT=8080
```

### Configuration File

The `config.yaml` file supports:
- Application settings
- API configuration
- Database settings
- Cache parameters
- Gemini API configuration
- Agent settings
- Governance rules
- Observability options
- Logging configuration

See `config.yaml` for full documentation.

## Development

### Running Tests

```bash
pytest tests/ -v --cov=.
```

### Code Quality

```bash
# Format code
black saas-bi-agent/

# Sort imports
isort saas-bi-agent/

# Type checking
mypy saas-bi-agent/

# Linting
flake8 saas-bi-agent/
```

### Project Status

**✓ Completed Components:**
- [x] Project structure
- [x] Configuration system
- [x] Structured logging
- [x] Cache manager with SQLite
- [x] Base agent abstract class
- [x] FastAPI application skeleton
- [x] API routes (placeholder implementations)
- [x] Request/Response models
- [x] Database schema

**🚧 TODO - Next Steps:**
1. Implement Gemini client wrapper
2. Implement specialized agents:
   - Revenue Agent
   - Product Agent
   - Support Agent
   - Synthesizer Agent
3. Implement Orchestrator
4. Implement Governance system:
   - Guardrails
   - Evaluation
   - HITL Manager
5. Implement Google Sheets integration
6. Add comprehensive tests
7. Add example scripts and notebooks
8. Production deployment guides

## Database Schema

The system uses SQLite with a comprehensive schema supporting:

- **Caching**: Prompt-level and agent-level response caching
- **Tracing**: Distributed execution traces
- **Metrics**: Performance and usage metrics
- **Errors**: Centralized error logging
- **Guardrails**: Violation tracking
- **HITL**: Human-in-the-loop request management
- **Evaluation**: Quality assessment tracking
- **Sessions**: User session management

See `data/schema.sql` for complete schema definition.

## Observability

### Structured Logging

All logs are structured (JSON or text) with trace context:

```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info_ctx("User action", user_id="123", action="create_analysis")
```

### Distributed Tracing

Every request gets a unique trace ID for end-to-end tracking:

```python
trace_id = cache.start_trace(agent_type="revenue", session_id=session_id)
# ... perform work ...
cache.end_trace(trace_id, status="success", input_tokens=500, output_tokens=1500)
```

### Metrics

Performance metrics are automatically collected:
- Agent execution time
- Cache hit rates
- Token usage
- Error rates

## Architecture Patterns

### Base Agent Pattern

All agents extend `BaseAgent` which provides:
- Automatic caching
- Tracing integration
- Error handling
- Confidence scoring
- Configuration management

```python
from agents.base_agent import BaseAgent

class RevenueAgent(BaseAgent):
    def _generate_analysis(self, data, context, trace_id):
        # Implement analysis logic
        pass

    def _build_prompt(self, data, context):
        # Build LLM prompt
        pass

    def _calculate_confidence(self, data, result, context):
        # Calculate confidence score
        pass
```

### Cache Strategy

1. **Check agent-level cache** - Full response caching
2. **Check prompt-level cache** - LLM response caching
3. **Generate new response** - Call Gemini API
4. **Cache results** - Store for future use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Google Gemini](https://ai.google.dev/) - Advanced AI models
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [SQLite](https://www.sqlite.org/) - Embedded database

---

**Status**: 🚧 Initial skeleton complete - Ready for agent implementation

**Next**: Implement Gemini client and specialized agents
