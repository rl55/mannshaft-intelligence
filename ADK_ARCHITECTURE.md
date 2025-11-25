# ADK Migration Architecture

## Decisions Summary

✅ **Migration Strategy**: Option B - Complete Rewrite  
✅ **Session Management**: ADK SessionService with SQLite sync  
✅ **Caching**: ADK context caching (extensible via plugins)  
✅ **WebSocket**: ADK bidi-streaming  
✅ **FastAPI**: ADK API Server  
✅ **Google Sheets**: ADK MCP tools  
✅ **HITL**: ADK callbacks/events  
✅ **Testing**: New ADK-specific tests alongside existing

## Architecture Hierarchy

```
SequentialAgent (Main Orchestrator)
│
├── ParallelAgent (Analytical Coordinator)
│   ├── RevenueAgent (LlmAgent)
│   ├── ProductAgent (LlmAgent)
│   └── SupportAgent (LlmAgent)
│
├── SynthesizerAgent (LlmAgent with tool calling)
│
├── GovernanceAgent (Custom Agent - rule-based)
│
└── EvaluationAgent (Custom Agent - rule-based)
```

## Implementation Plan

### Phase 1: Foundation Setup ✅
- [x] Install ADK
- [x] Update requirements.txt
- [x] Document decisions

### Phase 2: Core Infrastructure
- [ ] Set up ADK SessionService with SQLite sync
- [ ] Configure ADK context caching
- [ ] Set up ADK API Server
- [ ] Configure ADK bidi-streaming

### Phase 3: Agent Migration
- [ ] Migrate RevenueAgent to ADK LlmAgent
- [ ] Migrate ProductAgent to ADK LlmAgent
- [ ] Migrate SupportAgent to ADK LlmAgent
- [ ] Create ParallelAgent coordinator for analytical agents
- [ ] Migrate SynthesizerAgent to ADK LlmAgent with tools
- [ ] Migrate GovernanceAgent to ADK Custom Agent
- [ ] Migrate EvaluationAgent to ADK Custom Agent

### Phase 4: Orchestration
- [ ] Create SequentialAgent for full workflow
- [ ] Integrate HITL via ADK callbacks/events
- [ ] Set up ADK event handling for WebSocket

### Phase 5: Integration
- [ ] Migrate Google Sheets to ADK MCP tools
- [ ] Integrate ADK API Server with FastAPI
- [ ] Set up ADK bidi-streaming endpoints

### Phase 6: Testing
- [ ] Create ADK-specific test suite
- [ ] Integration tests for full workflow
- [ ] Performance benchmarking

## Key ADK Components

### Session Management
- Use `DatabaseSessionService` with SQLite backend
- Sync with existing SQLite database schema

### Caching
- Use ADK context caching for prompt caching
- Extend via plugins if needed for agent-level caching

### Tools
- Google Sheets via MCP tools
- Web search tool for Synthesizer
- Custom tools for governance/evaluation

### Events & Callbacks
- Use ADK event system for HITL escalations
- Callbacks for governance checks
- Event streaming for WebSocket updates

