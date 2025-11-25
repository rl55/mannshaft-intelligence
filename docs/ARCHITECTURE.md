# System Architecture: ADK-Based Multi-Agent Platform

## Overview

Mannshaft Intelligence is built on **Google Agent Development Kit (ADK)**, providing a production-ready, scalable multi-agent system for SaaS business intelligence analysis.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  - Dashboard, Analysis View, Reports, HITL, Monitoring      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              ADK API Server (FastAPI)                        │
│  - Unified FastAPI app (adk_unified_main.py)                │
│  - ADK endpoints: /adk/agents, /adk/sessions                │
│  - Custom routes: /api/v1/analysis, /api/v1/sessions, etc.   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         ADK App (adk_app.py)                                 │
│  - App(name="saas_bi_agent_adk")                            │
│  - ContextCacheConfig (compression enabled)                 │
│  - Root Agent: SequentialAgent (Main Orchestrator)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│    ADK SequentialAgent (Main Orchestrator)                   │
│    Coordinates end-to-end workflow                          │
└───────┬─────────────────────────────────────────────────────┘
        │
        ├──→ ADK ParallelAgent (Analytical Coordinator)
        │    │
        │    ├──→ RevenueAgent (ADK LlmAgent)
        │    │    - MRR Analysis
        │    │    - Churn Analysis
        │    │    - ARPU Segmentation
        │    │    - Tools: fetch_revenue_data_from_sheets
        │    │
        │    ├──→ ProductAgent (ADK LlmAgent)
        │    │    - DAU/WAU/MAU Analysis
        │    │    - Feature Adoption
        │    │    - User Engagement
        │    │    - Tools: fetch_product_data_from_sheets
        │    │
        │    └──→ SupportAgent (ADK LlmAgent)
        │         - Ticket Volume Analysis
        │         - CSAT/NPS Tracking
        │         - Escalation Patterns
        │         - Tools: fetch_support_data_from_sheets
        │
        ├──→ SynthesizerAgent (ADK LlmAgent with tools)
        │    - Cross-functional Correlation
        │    - Root Cause Analysis
        │    - Strategic Recommendations
        │    - Tools: web_search, aggregate_risk_flags
        │
        ├──→ GovernanceAgent (ADK BaseAgent)
        │    - PII Detection
        │    - Hard Guardrails
        │    - Adaptive Guardrails
        │    - HITL Escalation
        │
        └──→ EvaluationAgent (ADK LlmAgent)
             - Quality Scoring
             - Factual Grounding
             - Completeness Check
             - Regeneration Decision
```

---

## Component Details

### 1. ADK API Server (`adk_unified_main.py`)

**Purpose**: Unified FastAPI application combining ADK API Server with custom routes.

**Key Features**:
- ADK agent endpoints (`/adk/*`)
- Custom API routes (`/api/v1/*`)
- WebSocket support for real-time updates
- CORS middleware
- Health check endpoints

**Entry Point**: `uvicorn adk_unified_main:app --host 0.0.0.0 --port 8000`

### 2. ADK App (`adk_app.py`)

**Purpose**: ADK application configuration exported for API Server discovery.

**Configuration**:
```python
app = App(
    name="saas_bi_agent_adk",
    root_agent=create_main_orchestrator(),  # SequentialAgent
    context_cache_config=ContextCacheConfig()  # Enabled with compression
)
```

**Exports**: `app`, `root_agent` (for ADK API Server discovery)

### 3. Main Orchestrator (`adk_agents/orchestrator.py`)

**Type**: `ADK SequentialAgent`

**Responsibilities**:
- Coordinates end-to-end analysis workflow
- Manages agent execution order
- Handles WebSocket event emission
- Integrates with HITL manager

**Sub-Agents**:
1. `ParallelAgent` (Analytical Coordinator)
2. `SynthesizerAgent`
3. `GovernanceAgent`
4. `EvaluationAgent`

### 4. Analytical Coordinator (`adk_agents/analytical_coordinator.py`)

**Type**: `ADK ParallelAgent`

**Purpose**: Runs Revenue, Product, and Support agents concurrently.

**Sub-Agents**:
- `RevenueAgent` (LlmAgent)
- `ProductAgent` (LlmAgent)
- `SupportAgent` (LlmAgent)

### 5. Analytical Agents

#### Revenue Agent (`adk_agents/revenue_agent.py`)
- **Type**: `ADK LlmAgent`
- **Model**: Gemini 2.5 Flash Lite
- **Tools**: `fetch_revenue_data_from_sheets` (ADK FunctionTool)
- **Output**: Structured JSON with MRR, churn, ARPU analysis

#### Product Agent (`adk_agents/product_agent.py`)
- **Type**: `ADK LlmAgent`
- **Model**: Gemini 2.5 Flash Lite
- **Tools**: `fetch_product_data_from_sheets` (ADK FunctionTool)
- **Output**: Structured JSON with DAU/WAU/MAU, feature adoption analysis

#### Support Agent (`adk_agents/support_agent.py`)
- **Type**: `ADK LlmAgent`
- **Model**: Gemini 2.5 Flash Lite
- **Tools**: `fetch_support_data_from_sheets` (ADK FunctionTool)
- **Output**: Structured JSON with ticket volume, CSAT/NPS analysis

### 6. Synthesizer Agent (`adk_agents/synthesizer_agent.py`)

**Type**: `ADK LlmAgent` with tool calling

**Tools**:
- `web_search` - External validation
- `aggregate_risk_flags` - Risk aggregation

**Purpose**: Cross-correlates insights from analytical agents and generates strategic recommendations.

### 7. Governance Agent (`adk_agents/governance_agent.py`)

**Type**: `ADK BaseAgent` (custom agent wrapper)

**Purpose**: Validates outputs against guardrails (PII detection, cost limits, quality thresholds).

**Integration**: Wraps existing `GuardrailAgent` logic for ADK compatibility.

### 8. Evaluation Agent (`adk_agents/evaluation_agent.py`)

**Type**: `ADK LlmAgent`

**Purpose**: Evaluates analysis quality, factual grounding, and completeness.

**Output**: Quality score, evaluation details, regeneration decision.

---

## Data Flow

### 1. Analysis Request Flow

```
User → Frontend → POST /api/v1/analysis/trigger
    → Background Task → ADK Runner
    → SequentialAgent (Main Orchestrator)
    → ParallelAgent (Analytical Coordinator)
    → RevenueAgent, ProductAgent, SupportAgent (concurrent)
    → SynthesizerAgent
    → GovernanceAgent
    → EvaluationAgent
    → Save Results → WebSocket Events → Frontend
```

### 2. WebSocket Event Flow

```
ADK Agent Execution
    → Event Emitter (in orchestrator)
    → WebSocket Buffer (if no connection)
    → WebSocket Connection (when available)
    → Frontend Real-Time Updates
```

### 3. Data Fetching Flow

```
ADK Agent (e.g., RevenueAgent)
    → Calls ADK FunctionTool: fetch_revenue_data_from_sheets
    → GoogleSheetsIntegration.read_revenue_data()
    → Google Sheets API
    → Returns data_points → Agent Analysis → Structured Output
```

---

## ADK Integration Points

### 1. Session Management

**ADK Component**: `DatabaseSessionService` (SQLite sync)

**Location**: `adk_setup.py`

**Configuration**:
```python
session_service = DatabaseSessionService(
    db_url=f"sqlite:///{db_path}"
)
```

### 2. Context Caching

**ADK Component**: `ContextCacheConfig`

**Location**: `adk_app.py`

**Configuration**:
```python
context_cache_config = ContextCacheConfig()
# Provides built-in context compression
```

### 3. Agent Tools

**ADK Component**: `FunctionTool`

**Location**: `adk_tools/google_sheets_tools.py`

**Tools**:
- `fetch_revenue_data_from_sheets`
- `fetch_product_data_from_sheets`
- `fetch_support_data_from_sheets`

### 4. API Server

**ADK Component**: `get_fast_api_app()`

**Location**: `adk_unified_main.py`

**Integration**: Combines ADK API Server with custom FastAPI routes.

---

## Deployment Architecture

### Cloud Run Deployment

```
┌─────────────────────────────────────────┐
│         Cloud Run Container             │
│  ┌───────────────────────────────────┐ │
│  │   ADK API Server (FastAPI)         │ │
│  │   - Port: 8080                     │ │
│  │   - Memory: 4GB                     │ │
│  │   - CPU: 2 vCPU                    │ │
│  └───────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               ├──→ Cloud SQL (PostgreSQL)
               │    - Sessions
               │    - Cache
               │
               ├──→ Secret Manager
               │    - Gemini API Key
               │    - Google Credentials
               │
               └──→ Google Sheets API
                    - Revenue Data
                    - Product Data
                    - Support Data
```

### Vertex AI Deployment

```
┌─────────────────────────────────────────┐
│      Vertex AI Agent Engine              │
│  ┌───────────────────────────────────┐ │
│  │   ADK App (adk_app.py)            │ │
│  │   - SequentialAgent                │ │
│  │   - Context Caching                │ │
│  └───────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
               └──→ Same integrations as Cloud Run
```

---

## Key ADK Features Used

1. **SequentialAgent**: Main orchestrator for workflow coordination
2. **ParallelAgent**: Concurrent execution of analytical agents
3. **LlmAgent**: LLM-powered agents (Revenue, Product, Support, Synthesizer, Evaluation)
4. **BaseAgent**: Custom agent wrapper (Governance)
5. **FunctionTool**: Google Sheets integration tools
6. **ContextCacheConfig**: Built-in context caching and compression
7. **DatabaseSessionService**: Persistent session management
8. **API Server**: Unified FastAPI application with ADK endpoints

---

## Migration from Legacy Code

### What Changed

- **Before**: Custom `OrchestratorAgent` using `asyncio.gather()`
- **After**: ADK `SequentialAgent` with `ParallelAgent` sub-agent

- **Before**: Direct Gemini API calls via `google.generativeai`
- **After**: ADK `LlmAgent` handles LLM calls internally

- **Before**: Custom WebSocket event emission
- **After**: ADK bidi-streaming (with custom WebSocket wrapper)

- **Before**: Custom caching logic
- **After**: ADK context caching with compression

- **Before**: Custom session management
- **After**: ADK `DatabaseSessionService`

### What Stayed the Same

- Google Sheets integration logic (wrapped as ADK FunctionTools)
- Guardrails logic (wrapped in ADK BaseAgent)
- HITL manager (integrated with ADK events)
- Database schema (SQLite for sessions/cache)
- Frontend (no changes needed)

---

## Benefits of ADK Architecture

1. **Production-Ready**: Built-in orchestration, session management, caching
2. **Scalable**: Designed for enterprise workloads
3. **Observable**: Built-in tracing and logging
4. **Deployable**: Ready for Cloud Run and Vertex AI
5. **Maintainable**: Standard ADK patterns, less custom code
6. **Cost-Effective**: Built-in caching and compression

---

## Future Enhancements

1. **ADK Agent Registry**: Register agents for discovery
2. **ADK Evaluation Framework**: Use ADK's built-in evaluation
3. **ADK Monitoring**: Integrate with ADK observability tools
4. **ADK Workflow Agents**: Use LoopAgent for regeneration loops
5. **ADK MCP Server**: Native MCP server for Google Sheets

---

## References

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Agents Guide](https://google.github.io/adk-docs/agents/)
- [ADK API Server](https://google.github.io/adk-docs/runtime/)
- [ADK Deployment](https://google.github.io/adk-docs/deployment/)

