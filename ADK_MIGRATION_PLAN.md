# ADK Migration Plan

## Current Status

**Date**: 2025-01-27  
**Branch**: `migrate-to-adk`  
**Baseline**: Current codebase committed to `main` and `dev` branches

## Why Migrate to ADK?

The current implementation uses direct Gemini API calls (`google.generativeai`) with custom orchestration via Python's `asyncio`. However, [Google ADK](https://google.github.io/adk-docs/) provides:

✅ **Built-in orchestration** - Sequential, Parallel, and Loop workflow agents  
✅ **Session management** - Built-in session lifecycle and state management  
✅ **Multi-agent coordination** - Native support for agent hierarchies  
✅ **Tool ecosystem** - Pre-built tools, custom functions, MCP integration  
✅ **Caching** - Context caching and compression  
✅ **WebSocket support** - Bidi-streaming for real-time updates  
✅ **FastAPI integration** - API Server component  
✅ **Deployment ready** - Agent Engine, Cloud Run, GKE support  
✅ **Observability** - Built-in logging, tracing, evaluation  
✅ **Safety & Security** - Built-in patterns and best practices

## Migration Strategy

### Phase 1: Setup & Dependencies
- [ ] Install ADK: `pip install google-adk`
- [ ] Review ADK documentation: https://google.github.io/adk-docs/
- [ ] Identify ADK equivalents for current components

### Phase 2: Agent Migration
- [ ] **Revenue Agent** → ADK `LlmAgent` or `WorkflowAgent`
- [ ] **Product Agent** → ADK `LlmAgent` or `WorkflowAgent`
- [ ] **Support Agent** → ADK `LlmAgent` or `WorkflowAgent`
- [ ] **Synthesizer Agent** → ADK `LlmAgent` with tool calling
- [ ] **Governance Agent** → ADK custom agent with guardrails
- [ ] **Evaluation Agent** → ADK evaluation framework

### Phase 3: Orchestration Migration
- [ ] Replace custom `OrchestratorAgent` with ADK `ParallelAgent` for analytical agents
- [ ] Use ADK `SequentialAgent` for Synthesizer → Governance → Evaluation flow
- [ ] Migrate session management to ADK `SessionService`
- [ ] Replace custom WebSocket events with ADK bidi-streaming

### Phase 4: Integration Migration
- [ ] Replace `GeminiClient` with ADK's built-in Gemini integration
- [ ] Migrate Google Sheets integration to ADK MCP tools
- [ ] Replace custom caching with ADK context caching
- [ ] Migrate FastAPI routes to ADK API Server

### Phase 5: Governance & HITL
- [ ] Migrate guardrails to ADK safety patterns
- [ ] Integrate HITL with ADK callbacks/events
- [ ] Migrate evaluation to ADK evaluation framework

### Phase 6: Testing & Validation
- [ ] Ensure all existing tests pass
- [ ] Verify WebSocket real-time updates work
- [ ] Validate cache performance
- [ ] Test HITL workflow
- [ ] Performance benchmarking

## Key ADK Components to Use

### Agents
- `LlmAgent` - For LLM-driven agents (Revenue, Product, Support, Synthesizer)
- `ParallelAgent` - For parallel execution of analytical agents
- `SequentialAgent` - For sequential workflow (Synthesizer → Governance → Evaluation)
- `WorkflowAgent` - For complex workflows

### Tools
- MCP tools for Google Sheets integration
- Custom function tools for data processing
- Gemini API tools (Computer use, etc.)

### Runtime
- `SessionService` - For session lifecycle management
- `Context` - For context management and caching
- Bidi-streaming - For WebSocket real-time updates
- API Server - For FastAPI integration

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Python API Reference](https://google.github.io/adk-docs/reference/python/)
- [Multi-Agent Systems Guide](https://google.github.io/adk-docs/agents/multi-agent-systems/)
- [Workflow Agents](https://google.github.io/adk-docs/agents/workflow-agents/)
- [Bidi-streaming Guide](https://google.github.io/adk-docs/components/bidi-streaming/)

## Notes

- Current implementation is fully functional and baseline is preserved in `main` and `dev`
- Migration can be done incrementally without breaking existing functionality
- ADK provides better long-term maintainability and alignment with Google's recommended patterns

