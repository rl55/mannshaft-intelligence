-- ============================================================================
-- SaaS BI Agent System - SQLite Database Schema
-- Purpose: Caching, Observability, Governance Tracking
-- Version: 1.0
-- ============================================================================

-- ============================================================================
-- CACHE TABLES (Performance Optimization)
-- ============================================================================

-- Prompt-level caching: Store Gemini API responses for reuse
CREATE TABLE IF NOT EXISTS prompt_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_hash TEXT UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    model TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_saved INTEGER DEFAULT 0,  -- Cumulative savings on cache hits
    hit_count INTEGER DEFAULT 0,     -- Number of times this cache entry was reused
    last_accessed DATETIME,
    ttl_hours INTEGER DEFAULT 168    -- Time-to-live: 7 days default
);

CREATE INDEX IF NOT EXISTS idx_prompt_hash ON prompt_cache(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_timestamp ON prompt_cache(timestamp);
CREATE INDEX IF NOT EXISTS idx_last_accessed ON prompt_cache(last_accessed);

-- Agent-level response caching: Store complete agent execution results
CREATE TABLE IF NOT EXISTS agent_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL,        -- 'revenue', 'product', 'support', etc.
    context_hash TEXT NOT NULL,      -- Hash of input context (data + parameters)
    request_params TEXT,             -- JSON of request parameters
    response TEXT NOT NULL,          -- Full agent response
    confidence_score REAL,           -- Agent's confidence in response
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT 0,
    last_accessed DATETIME,
    ttl_hours INTEGER DEFAULT 24     -- Shorter TTL for agent responses
);

CREATE INDEX IF NOT EXISTS idx_agent_context ON agent_responses(agent_type, context_hash);
CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON agent_responses(timestamp);

-- ============================================================================
-- OBSERVABILITY TABLES (Tracing & Monitoring)
-- ============================================================================

-- Execution traces: Track every agent invocation
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    parent_trace_id TEXT,            -- For nested agent calls
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    duration_ms INTEGER,
    status TEXT CHECK(status IN ('success', 'error', 'timeout', 'cancelled')),
    error_message TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached_tokens INTEGER DEFAULT 0,
    metadata TEXT                    -- JSON for additional context
);

CREATE INDEX IF NOT EXISTS idx_trace_id ON traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_session_id ON traces(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_type ON traces(agent_type);
CREATE INDEX IF NOT EXISTS idx_start_time ON traces(start_time);

-- Error logs: Centralized error tracking
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT,
    agent_type TEXT,
    error_type TEXT,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context TEXT,                    -- JSON with relevant context
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_agent ON error_logs(agent_type);
CREATE INDEX IF NOT EXISTS idx_error_severity ON error_logs(severity);

-- Performance metrics: Aggregate statistics
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    agent_type TEXT,
    session_id TEXT,
    dimensions TEXT                  -- JSON for additional grouping
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics(agent_type);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

-- ============================================================================
-- GOVERNANCE TABLES (Guardrails & HITL)
-- ============================================================================

-- Guardrail violations: Track all guardrail triggers
CREATE TABLE IF NOT EXISTS guardrail_violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    rule_type TEXT NOT NULL,         -- 'hard', 'adaptive'
    rule_name TEXT NOT NULL,
    violation_severity TEXT CHECK(violation_severity IN ('low', 'medium', 'high', 'critical')),
    violation_details TEXT,          -- JSON with specifics
    action_taken TEXT,               -- 'blocked', 'escalated', 'modified', 'allowed'
    human_review_required BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_violation_timestamp ON guardrail_violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_violation_agent ON guardrail_violations(agent_type);
CREATE INDEX IF NOT EXISTS idx_violation_severity ON guardrail_violations(violation_severity);

-- HITL requests: Track human-in-the-loop escalations
CREATE TABLE IF NOT EXISTS hitl_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT UNIQUE NOT NULL,
    trace_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    reason TEXT NOT NULL,            -- Why escalated
    context TEXT NOT NULL,           -- Full context for human
    proposed_action TEXT,            -- Agent's tentative response
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'modified', 'timeout')),
    human_decision TEXT,
    human_feedback TEXT,
    resolution_time_minutes INTEGER,
    resolved_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_hitl_status ON hitl_requests(status);
CREATE INDEX IF NOT EXISTS idx_hitl_timestamp ON hitl_requests(timestamp);

-- Adaptive rule learning: Track rule adjustments over time
CREATE TABLE IF NOT EXISTS adaptive_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    rule_definition TEXT NOT NULL,   -- JSON rule specification
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    false_positive_count INTEGER DEFAULT 0,
    confidence_threshold REAL DEFAULT 0.7,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_adaptive_rule_name ON adaptive_rules(rule_name);
CREATE INDEX IF NOT EXISTS idx_adaptive_active ON adaptive_rules(is_active);

-- ============================================================================
-- SESSION MANAGEMENT
-- ============================================================================

-- Sessions: Track user analysis sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    session_type TEXT,               -- 'weekly_review', 'ad_hoc', 'investigation'
    total_agents_invoked INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cached_tokens INTEGER DEFAULT 0,
    hitl_escalations INTEGER DEFAULT 0,
    guardrail_violations INTEGER DEFAULT 0,
    final_status TEXT CHECK(final_status IN ('completed', 'incomplete', 'error'))
);

CREATE INDEX IF NOT EXISTS idx_session_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_time ON sessions(start_time);

-- ============================================================================
-- EVALUATION & QUALITY CONTROL
-- ============================================================================

-- Evaluation results: Track response quality
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Quality metrics
    factual_grounding_score REAL,    -- 0-1: How well grounded in data
    relevance_score REAL,            -- 0-1: Response relevance
    completeness_score REAL,         -- 0-1: Answer completeness
    coherence_score REAL,            -- 0-1: Logical coherence
    
    -- Validation checks
    data_citations_present BOOLEAN,
    confidence_calibrated BOOLEAN,
    anomalies_flagged BOOLEAN,
    
    -- Overall assessment
    overall_quality TEXT CHECK(overall_quality IN ('excellent', 'good', 'acceptable', 'poor')),
    requires_review BOOLEAN DEFAULT 0,
    review_reason TEXT,
    
    evaluator_agent TEXT,            -- Which agent did evaluation
    evaluation_time_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_eval_trace ON evaluations(trace_id);
CREATE INDEX IF NOT EXISTS idx_eval_quality ON evaluations(overall_quality);
CREATE INDEX IF NOT EXISTS idx_eval_review ON evaluations(requires_review);

-- ============================================================================
-- DATA FRESHNESS TRACKING
-- ============================================================================

-- Track when source data was last updated
CREATE TABLE IF NOT EXISTS data_freshness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source TEXT NOT NULL,       -- 'google_sheets', 'api', etc.
    source_identifier TEXT,          -- Sheet ID, API endpoint, etc.
    last_sync DATETIME DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    checksum TEXT,                   -- Hash to detect changes
    is_stale BOOLEAN DEFAULT 0,
    stale_threshold_hours INTEGER DEFAULT 24
);

CREATE INDEX IF NOT EXISTS idx_freshness_source ON data_freshness(data_source);
CREATE INDEX IF NOT EXISTS idx_freshness_stale ON data_freshness(is_stale);

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- Cache performance view
CREATE VIEW IF NOT EXISTS v_cache_performance AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_entries,
    SUM(hit_count) as total_hits,
    SUM(tokens_saved) as tokens_saved,
    AVG(hit_count) as avg_hits_per_entry,
    SUM(CASE WHEN hit_count > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as hit_rate_percent
FROM prompt_cache
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Agent performance view
CREATE VIEW IF NOT EXISTS v_agent_performance AS
SELECT 
    agent_type,
    COUNT(*) as total_invocations,
    AVG(duration_ms) as avg_duration_ms,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cached_tokens) as total_cached_tokens,
    SUM(cached_tokens) * 100.0 / NULLIF(SUM(input_tokens), 0) as cache_efficiency_percent
FROM traces
GROUP BY agent_type
ORDER BY total_invocations DESC;

-- Guardrail effectiveness view
CREATE VIEW IF NOT EXISTS v_guardrail_effectiveness AS
SELECT 
    rule_name,
    COUNT(*) as total_triggers,
    SUM(CASE WHEN action_taken = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
    SUM(CASE WHEN action_taken = 'escalated' THEN 1 ELSE 0 END) as escalated_count,
    SUM(CASE WHEN human_review_required = 1 THEN 1 ELSE 0 END) as human_reviews,
    AVG(CASE WHEN violation_severity = 'critical' THEN 4 
             WHEN violation_severity = 'high' THEN 3
             WHEN violation_severity = 'medium' THEN 2 
             ELSE 1 END) as avg_severity_score
FROM guardrail_violations
GROUP BY rule_name
ORDER BY total_triggers DESC;

-- HITL performance view
CREATE VIEW IF NOT EXISTS v_hitl_performance AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
    SUM(CASE WHEN status = 'modified' THEN 1 ELSE 0 END) as modified,
    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeouts,
    AVG(resolution_time_minutes) as avg_resolution_time,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as still_pending
FROM hitl_requests
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Session efficiency view
CREATE VIEW IF NOT EXISTS v_session_efficiency AS
SELECT 
    session_id,
    session_type,
    start_time,
    CAST((julianday(end_time) - julianday(start_time)) * 24 * 60 AS INTEGER) as duration_minutes,
    total_agents_invoked,
    total_tokens_used,
    total_cached_tokens,
    total_cached_tokens * 100.0 / NULLIF(total_tokens_used, 0) as cache_efficiency_percent,
    hitl_escalations,
    guardrail_violations,
    final_status
FROM sessions
WHERE end_time IS NOT NULL
ORDER BY start_time DESC;

-- ============================================================================
-- CLEANUP PROCEDURES (As SQL Comments for Manual Execution)
-- ============================================================================

-- To delete expired cache entries:
-- DELETE FROM prompt_cache WHERE datetime(last_accessed, '+' || ttl_hours || ' hours') < datetime('now');
-- DELETE FROM agent_responses WHERE datetime(last_accessed, '+' || ttl_hours || ' hours') < datetime('now');

-- To archive old traces (keep last 30 days):
-- DELETE FROM traces WHERE datetime(start_time, '+30 days') < datetime('now');

-- To clear resolved HITL requests (keep last 7 days):
-- DELETE FROM hitl_requests WHERE status != 'pending' AND datetime(resolved_at, '+7 days') < datetime('now');

-- ============================================================================
-- INITIALIZATION COMPLETE
-- ============================================================================
