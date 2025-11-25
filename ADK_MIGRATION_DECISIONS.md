# ADK Migration - Key Decisions Needed

## Status
✅ ADK installed and verified (v1.19.0)  
✅ Requirements.txt updated  
⏳ Awaiting decisions on migration approach

## Key Decisions Required

### 1. Migration Strategy: Incremental vs. Complete Rewrite

**Option A: Incremental Migration (Recommended)**
- Keep existing agents working alongside ADK agents
- Migrate one agent at a time (e.g., start with Revenue Agent)
- Maintain backward compatibility during transition
- **Pros**: Lower risk, can test incrementally, rollback easier
- **Cons**: Temporary code duplication, longer timeline

**Option B: Complete Rewrite**
- Migrate all agents to ADK simultaneously
- Replace entire orchestrator with ADK workflow agents
- **Pros**: Cleaner final codebase, faster overall
- **Cons**: Higher risk, longer period without working system

**Question**: Which approach do you prefer?

---

### 2. Agent Type Selection

For each agent, which ADK agent type should we use?

**Revenue/Product/Support Agents:**
- **Option A**: `LlmAgent` - Simple LLM-driven agents
- **Option B**: `WorkflowAgent` - More complex workflows with multiple steps
- **Option C**: Custom agent extending ADK base classes

**Synthesizer Agent:**
- **Option A**: `LlmAgent` with tool calling for web search
- **Option B**: `WorkflowAgent` with sequential steps
- **Option C**: Custom agent

**Governance/Evaluation Agents:**
- **Option A**: Custom agents (not LLM-driven, rule-based)
- **Option B**: `LlmAgent` for evaluation reasoning
- **Option C**: ADK evaluation framework

**Question**: What's your preference for each agent type?

---

### 3. Orchestration: ADK Workflow Agents vs. Custom Orchestrator

**Current**: Custom `OrchestratorAgent` using `asyncio.gather` for parallel execution

**Option A**: Use ADK `ParallelAgent` for analytical agents
```python
from google.adk import ParallelAgent

analytical_agents = ParallelAgent(
    agents=[revenue_agent, product_agent, support_agent]
)
```

**Option B**: Use ADK `SequentialAgent` for full workflow
```python
from google.adk import SequentialAgent

workflow = SequentialAgent(
    agents=[
        parallel_analytical_agents,
        synthesizer_agent,
        governance_agent,
        evaluation_agent
    ]
)
```

**Option C**: Keep custom orchestrator but use ADK agents internally

**Question**: Should we replace the custom orchestrator with ADK workflow agents?

---

### 4. Session Management

**Current**: Custom SQLite-based session management via `CacheManager`

**Option A**: Migrate to ADK `SessionService`
- Use `InMemorySessionService` for development
- Use `DatabaseSessionService` for production (requires DB migration)

**Option B**: Keep custom session management, integrate with ADK agents

**Question**: Should we migrate to ADK session management?

---

### 5. Caching Strategy

**Current**: Multi-level caching:
- Prompt cache (SQLite)
- Agent response cache (SQLite)
- Custom cache key generation with data_hash

**Option A**: Use ADK context caching
- ADK provides built-in context caching
- May need to adapt cache key strategy

**Option B**: Keep custom caching, integrate with ADK agents
- More control over cache keys
- Maintain existing cache performance

**Question**: Should we migrate to ADK caching or keep custom caching?

---

### 6. WebSocket/Real-time Updates

**Current**: Custom WebSocket implementation in FastAPI route

**Option A**: Use ADK bidi-streaming
- ADK supports WebSocket/bidi-streaming natively
- May require API route changes

**Option B**: Keep custom WebSocket, emit ADK events
- Less refactoring needed
- Maintain existing frontend integration

**Question**: Should we migrate to ADK bidi-streaming?

---

### 7. FastAPI Integration

**Current**: Custom FastAPI routes (`/api/v1/analysis/trigger`, WebSocket endpoint)

**Option A**: Use ADK API Server
- ADK provides FastAPI integration
- May require route restructuring

**Option B**: Keep custom FastAPI routes, use ADK agents internally
- Minimal changes to existing API
- Easier migration path

**Question**: Should we use ADK API Server or keep custom routes?

---

### 8. Google Sheets Integration

**Current**: Custom `GoogleSheetsClient` using `gspread`

**Option A**: Migrate to ADK MCP tools
- ADK supports MCP (Model Context Protocol) for Google Sheets
- More standardized approach

**Option B**: Keep custom Google Sheets client
- Already working, less migration effort
- Can integrate as ADK custom tool

**Question**: Should we migrate to ADK MCP tools for Google Sheets?

---

### 9. HITL (Human-in-the-Loop) Integration

**Current**: Custom `HITLManager` with SQLite storage

**Option A**: Integrate with ADK callbacks/events
- Use ADK event system for HITL escalations
- May need custom callback implementation

**Option B**: Keep custom HITL, trigger from ADK agents
- Less refactoring
- Maintain existing HITL workflow

**Question**: How should we integrate HITL with ADK?

---

### 10. Testing Strategy

**Question**: Should we:
- A) Migrate existing tests to work with ADK agents?
- B) Create new ADK-specific tests alongside existing tests?
- C) Keep existing tests, add ADK integration tests?

---

## Recommended Approach (Pending Your Approval)

Based on ADK capabilities, I recommend:

1. **Incremental Migration** (Option A) - Start with Revenue Agent
2. **LlmAgent** for analytical agents (Revenue/Product/Support)
3. **ADK ParallelAgent** for orchestrating analytical agents
4. **ADK SequentialAgent** for full workflow (analytical → synthesizer → governance → evaluation)
5. **ADK SessionService** for session management
6. **Keep custom caching** initially, evaluate ADK caching later
7. **ADK bidi-streaming** for WebSocket updates
8. **Keep custom FastAPI routes** initially, evaluate ADK API Server later
9. **Keep custom Google Sheets client** as ADK custom tool
10. **Integrate HITL** via ADK callbacks/events

**Please review and let me know your preferences for each decision point.**

