"""
SaaS BI Agent - Cache Manager
Handles all SQLite database interactions for caching, observability, and governance
"""

import sqlite3
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import uuid


class CacheManager:
    """
    Comprehensive cache and observability manager for SaaS BI Agent system.
    
    Features:
    - Prompt-level caching (Gemini API responses)
    - Agent-level caching (complete agent responses)
    - Distributed tracing
    - Error logging
    - Performance metrics
    - Guardrail violation tracking
    - HITL request management
    - Evaluation tracking
    """
    
    def __init__(self, db_path: str = "data/agent_cache.db", schema_path: Optional[str] = None):
        """
        Initialize the cache manager.
        
        Args:
            db_path: Path to SQLite database file
            schema_path: Optional path to schema.sql file for initialization
        """
        self.db_path = db_path
        # Update schema path to point to data/schema.sql
        self.schema_path = schema_path or str(Path(__file__).parent.parent / "data" / "schema.sql")
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Connection pool for thread safety
        self.conn = None
    
    def _init_database(self):
        """Initialize database with schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if database is already initialized
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_cache'")
        if cursor.fetchone() is None:
            # Database is new, run schema
            if Path(self.schema_path).exists():
                with open(self.schema_path, 'r') as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
                print(f"✓ Database initialized with schema from {self.schema_path}")
            else:
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        conn.commit()
        conn.close()
    
    def connect(self):
        """Establish database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # =========================================================================
    # PROMPT CACHING
    # =========================================================================
    
    @staticmethod
    def _hash_prompt(prompt: str, model: str) -> str:
        """Generate hash for prompt + model combination."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached_prompt(self, prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached prompt response if available and not expired.
        
        Args:
            prompt: The prompt text
            model: Model identifier
            
        Returns:
            Cached response dict or None if not found/expired
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        prompt_hash = self._hash_prompt(prompt, model)
        
        cursor.execute("""
            SELECT * FROM prompt_cache 
            WHERE prompt_hash = ? 
            AND datetime(last_accessed, '+' || ttl_hours || ' hours') > datetime('now')
        """, (prompt_hash,))
        
        row = cursor.fetchone()
        if row:
            # Update hit count and last accessed
            cursor.execute("""
                UPDATE prompt_cache 
                SET hit_count = hit_count + 1,
                    tokens_saved = tokens_saved + ?,
                    last_accessed = datetime('now')
                WHERE prompt_hash = ?
            """, (row['tokens_input'], prompt_hash))
            conn.commit()
            
            return dict(row)
        
        return None
    
    def cache_prompt(self, prompt: str, response: str, model: str, 
                     tokens_input: int, tokens_output: int, ttl_hours: int = 168) -> int:
        """
        Cache a prompt and its response.
        
        Args:
            prompt: The prompt text
            response: The model response
            model: Model identifier
            tokens_input: Input token count
            tokens_output: Output token count
            ttl_hours: Time-to-live in hours (default: 7 days)
            
        Returns:
            ID of cached entry
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        prompt_hash = self._hash_prompt(prompt, model)
        
        cursor.execute("""
            INSERT OR REPLACE INTO prompt_cache 
            (prompt_hash, prompt, response, model, tokens_input, tokens_output, 
             ttl_hours, last_accessed, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (prompt_hash, prompt, response, model, tokens_input, tokens_output, ttl_hours))
        
        conn.commit()
        return cursor.lastrowid
    
    # =========================================================================
    # AGENT RESPONSE CACHING
    # =========================================================================
    
    @staticmethod
    def _hash_context(agent_type: str, context: Dict[str, Any]) -> str:
        """Generate hash for agent context."""
        content = f"{agent_type}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached_agent_response(self, agent_type: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached agent response if available and not expired.
        
        Args:
            agent_type: Type of agent (e.g., 'revenue', 'product')
            context: Context dictionary (data + parameters)
            
        Returns:
            Cached response dict or None if not found/expired
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        context_hash = self._hash_context(agent_type, context)
        
        cursor.execute("""
            SELECT * FROM agent_responses 
            WHERE agent_type = ? AND context_hash = ?
            AND datetime(last_accessed, '+' || ttl_hours || ' hours') > datetime('now')
        """, (agent_type, context_hash))
        
        row = cursor.fetchone()
        if row:
            # Update last accessed
            cursor.execute("""
                UPDATE agent_responses 
                SET last_accessed = datetime('now'),
                    cache_hit = 1
                WHERE id = ?
            """, (row['id'],))
            conn.commit()
            
            return dict(row)
        
        return None
    
    def cache_agent_response(self, agent_type: str, context: Dict[str, Any], 
                           response: str, confidence_score: float,
                           execution_time_ms: int, ttl_hours: int = 24) -> int:
        """
        Cache an agent response.
        
        Args:
            agent_type: Type of agent
            context: Context dictionary
            response: Agent response text
            confidence_score: Agent's confidence (0-1)
            execution_time_ms: Execution time in milliseconds
            ttl_hours: Time-to-live in hours (default: 24 hours)
            
        Returns:
            ID of cached entry
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        context_hash = self._hash_context(agent_type, context)
        
        cursor.execute("""
            INSERT OR REPLACE INTO agent_responses 
            (agent_type, context_hash, request_params, response, confidence_score,
             execution_time_ms, ttl_hours, last_accessed, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (agent_type, context_hash, json.dumps(context), response, 
              confidence_score, execution_time_ms, ttl_hours))
        
        conn.commit()
        return cursor.lastrowid
    
    # =========================================================================
    # TRACING
    # =========================================================================
    
    def start_trace(self, agent_type: str, session_id: str, 
                   parent_trace_id: Optional[str] = None) -> str:
        """
        Start a new execution trace.
        
        Args:
            agent_type: Type of agent
            session_id: Session identifier
            parent_trace_id: Optional parent trace for nested calls
            
        Returns:
            Trace ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        trace_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO traces 
            (trace_id, session_id, agent_type, parent_trace_id, start_time)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (trace_id, session_id, agent_type, parent_trace_id))
        
        conn.commit()
        return trace_id
    
    def end_trace(self, trace_id: str, status: str, 
                 input_tokens: int = 0, output_tokens: int = 0,
                 cached_tokens: int = 0, error_message: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Complete an execution trace.
        
        Args:
            trace_id: Trace identifier
            status: 'success', 'error', 'timeout', or 'cancelled'
            input_tokens: Input token count
            output_tokens: Output token count
            cached_tokens: Cached token count
            error_message: Optional error message if status is 'error'
            metadata: Optional metadata dict
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Calculate duration
        cursor.execute("SELECT start_time FROM traces WHERE trace_id = ?", (trace_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row['start_time'])
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            cursor.execute("""
                UPDATE traces 
                SET end_time = datetime('now'),
                    duration_ms = ?,
                    status = ?,
                    error_message = ?,
                    input_tokens = ?,
                    output_tokens = ?,
                    cached_tokens = ?,
                    metadata = ?
                WHERE trace_id = ?
            """, (duration_ms, status, error_message, input_tokens, output_tokens,
                  cached_tokens, json.dumps(metadata) if metadata else None, trace_id))
            
            conn.commit()
    
    # =========================================================================
    # ERROR LOGGING
    # =========================================================================
    
    def log_error(self, agent_type: str, error_type: str, error_message: str,
                 stack_trace: Optional[str] = None, trace_id: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None, severity: str = 'medium'):
        """
        Log an error.
        
        Args:
            agent_type: Type of agent
            error_type: Error classification
            error_message: Error description
            stack_trace: Optional stack trace
            trace_id: Optional associated trace
            context: Optional context dict
            severity: 'low', 'medium', 'high', or 'critical'
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO error_logs 
            (trace_id, agent_type, error_type, error_message, stack_trace, context, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, agent_type, error_type, error_message, stack_trace,
              json.dumps(context) if context else None, severity))
        
        conn.commit()
    
    # =========================================================================
    # METRICS
    # =========================================================================
    
    def record_metric(self, metric_name: str, metric_value: float,
                     agent_type: Optional[str] = None, session_id: Optional[str] = None,
                     dimensions: Optional[Dict[str, Any]] = None):
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            agent_type: Optional agent type
            session_id: Optional session ID
            dimensions: Optional additional dimensions
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO metrics (metric_name, metric_value, agent_type, session_id, dimensions)
            VALUES (?, ?, ?, ?, ?)
        """, (metric_name, metric_value, agent_type, session_id,
              json.dumps(dimensions) if dimensions else None))
        
        conn.commit()
    
    # =========================================================================
    # GUARDRAILS
    # =========================================================================
    
    def log_guardrail_violation(self, trace_id: str, agent_type: str,
                               rule_type: str, rule_name: str,
                               violation_severity: str, violation_details: Dict[str, Any],
                               action_taken: str, human_review_required: bool = False):
        """
        Log a guardrail violation.
        
        Args:
            trace_id: Associated trace ID
            agent_type: Type of agent
            rule_type: 'hard' or 'adaptive'
            rule_name: Name of the rule
            violation_severity: 'low', 'medium', 'high', or 'critical'
            violation_details: Details dict
            action_taken: 'blocked', 'escalated', 'modified', or 'allowed'
            human_review_required: Whether human review is needed
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO guardrail_violations 
            (trace_id, agent_type, rule_type, rule_name, violation_severity,
             violation_details, action_taken, human_review_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, agent_type, rule_type, rule_name, violation_severity,
              json.dumps(violation_details), action_taken, human_review_required))
        
        conn.commit()
    
    # =========================================================================
    # HITL MANAGEMENT
    # =========================================================================
    
    def create_hitl_request(self, trace_id: str, agent_type: str,
                           reason: str, context: Dict[str, Any],
                           proposed_action: Optional[str] = None) -> str:
        """
        Create a human-in-the-loop escalation request.
        
        Args:
            trace_id: Associated trace ID
            agent_type: Type of agent
            reason: Reason for escalation
            context: Full context for human review
            proposed_action: Optional tentative response
            
        Returns:
            HITL request ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        request_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO hitl_requests 
            (request_id, trace_id, agent_type, reason, context, proposed_action, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (request_id, trace_id, agent_type, reason, json.dumps(context), proposed_action))
        
        conn.commit()
        return request_id
    
    def resolve_hitl_request(self, request_id: str, status: str,
                            human_decision: str, human_feedback: Optional[str] = None):
        """
        Resolve a HITL request.
        
        Args:
            request_id: HITL request ID
            status: 'approved', 'rejected', 'modified', or 'timeout'
            human_decision: The human's decision
            human_feedback: Optional feedback
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Calculate resolution time
        cursor.execute("SELECT timestamp FROM hitl_requests WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        if row:
            created_at = datetime.fromisoformat(row['timestamp'])
            resolution_time_minutes = int((datetime.now() - created_at).total_seconds() / 60)
            
            cursor.execute("""
                UPDATE hitl_requests 
                SET status = ?,
                    human_decision = ?,
                    human_feedback = ?,
                    resolution_time_minutes = ?,
                    resolved_at = datetime('now')
                WHERE request_id = ?
            """, (status, human_decision, human_feedback, resolution_time_minutes, request_id))
            
            conn.commit()
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def create_session(self, session_type: str, user_id: Optional[str] = None) -> str:
        """
        Create a new analysis session.
        
        Args:
            session_type: Type of session
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        session_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, session_type)
            VALUES (?, ?, ?)
        """, (session_id, user_id, session_type))
        
        conn.commit()
        return session_id
    
    def end_session(self, session_id: str, final_status: str = 'completed'):
        """
        End an analysis session and calculate statistics.
        
        Args:
            session_id: Session identifier
            final_status: 'completed', 'incomplete', or 'error'
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Calculate session statistics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT agent_type) as agents_invoked,
                SUM(input_tokens + output_tokens) as total_tokens,
                SUM(cached_tokens) as cached_tokens
            FROM traces
            WHERE session_id = ?
        """, (session_id,))
        
        stats = cursor.fetchone()
        
        # Count HITL escalations
        cursor.execute("""
            SELECT COUNT(*) FROM hitl_requests hr
            JOIN traces t ON hr.trace_id = t.trace_id
            WHERE t.session_id = ?
        """, (session_id,))
        hitl_count = cursor.fetchone()[0]
        
        # Count guardrail violations
        cursor.execute("""
            SELECT COUNT(*) FROM guardrail_violations gv
            JOIN traces t ON gv.trace_id = t.trace_id
            WHERE t.session_id = ?
        """, (session_id,))
        violation_count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE sessions 
            SET end_time = datetime('now'),
                total_agents_invoked = ?,
                total_tokens_used = ?,
                total_cached_tokens = ?,
                hitl_escalations = ?,
                guardrail_violations = ?,
                final_status = ?
            WHERE session_id = ?
        """, (stats['agents_invoked'], stats['total_tokens'], stats['cached_tokens'],
              hitl_count, violation_count, final_status, session_id))
        
        conn.commit()
    
    # =========================================================================
    # EVALUATION TRACKING
    # =========================================================================
    
    def record_evaluation(self, trace_id: str, agent_type: str,
                         factual_grounding_score: float, relevance_score: float,
                         completeness_score: float, coherence_score: float,
                         data_citations_present: bool, confidence_calibrated: bool,
                         anomalies_flagged: bool, overall_quality: str,
                         evaluator_agent: str, evaluation_time_ms: int,
                         requires_review: bool = False, review_reason: Optional[str] = None):
        """
        Record evaluation results for an agent response.
        
        Args:
            trace_id: Associated trace ID
            agent_type: Type of agent
            factual_grounding_score: 0-1 score
            relevance_score: 0-1 score
            completeness_score: 0-1 score
            coherence_score: 0-1 score
            data_citations_present: Whether citations included
            confidence_calibrated: Whether confidence is well-calibrated
            anomalies_flagged: Whether anomalies were flagged
            overall_quality: 'excellent', 'good', 'acceptable', or 'poor'
            evaluator_agent: Which agent did evaluation
            evaluation_time_ms: Evaluation time in ms
            requires_review: Whether review is needed
            review_reason: Optional reason for review
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evaluations 
            (trace_id, agent_type, factual_grounding_score, relevance_score,
             completeness_score, coherence_score, data_citations_present,
             confidence_calibrated, anomalies_flagged, overall_quality,
             requires_review, review_reason, evaluator_agent, evaluation_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, agent_type, factual_grounding_score, relevance_score,
              completeness_score, coherence_score, data_citations_present,
              confidence_calibrated, anomalies_flagged, overall_quality,
              requires_review, review_reason, evaluator_agent, evaluation_time_ms))
        
        conn.commit()
    
    # =========================================================================
    # ANALYTICS & REPORTING
    # =========================================================================
    
    def get_cache_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get cache performance statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM v_cache_performance 
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC
        """, (days,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get agent performance statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM v_agent_performance")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_guardrail_effectiveness(self) -> Dict[str, Any]:
        """Get guardrail effectiveness statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM v_guardrail_effectiveness")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_hitl_performance(self, days: int = 7) -> Dict[str, Any]:
        """Get HITL performance statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM v_hitl_performance 
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC
        """, (days,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Clean prompt cache
        cursor.execute("""
            DELETE FROM prompt_cache 
            WHERE datetime(last_accessed, '+' || ttl_hours || ' hours') < datetime('now')
        """)
        prompt_deleted = cursor.rowcount
        
        # Clean agent response cache
        cursor.execute("""
            DELETE FROM agent_responses 
            WHERE datetime(last_accessed, '+' || ttl_hours || ' hours') < datetime('now')
        """)
        agent_deleted = cursor.rowcount
        
        conn.commit()
        
        return {
            'prompt_cache_deleted': prompt_deleted,
            'agent_cache_deleted': agent_deleted
        }

