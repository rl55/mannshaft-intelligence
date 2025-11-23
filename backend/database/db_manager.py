"""
SQLite database manager for session and analysis result persistence.
"""

import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

from utils.logger import logger


class DatabaseManager:
    """
    Manages SQLite database for storing analysis sessions and results.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/analysis.db
        """
        if db_path is None:
            # Default to data/analysis.db relative to backend directory
            backend_dir = Path(__file__).parent.parent
            data_dir = backend_dir / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "analysis.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    session_type TEXT NOT NULL,
                    user_id TEXT,
                    status TEXT NOT NULL,
                    week_number INTEGER,
                    analysis_type TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    failed_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    session_id TEXT PRIMARY KEY,
                    report TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    execution_time_ms INTEGER NOT NULL,
                    cache_efficiency REAL NOT NULL,
                    agents_executed TEXT NOT NULL,
                    hitl_escalations INTEGER NOT NULL DEFAULT 0,
                    guardrail_violations INTEGER NOT NULL DEFAULT 0,
                    evaluation_passed BOOLEAN NOT NULL DEFAULT 0,
                    regeneration_count INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT,
                    generated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Analysis status table (for progress tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_status (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    current_step TEXT,
                    estimated_time_remaining_seconds INTEGER,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status 
                ON sessions(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at 
                ON sessions(created_at)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def create_session(
        self,
        session_id: str,
        session_type: str,
        user_id: Optional[str] = None,
        week_number: Optional[int] = None,
        analysis_type: Optional[str] = None
    ) -> str:
        """
        Create a new analysis session.
        
        Args:
            session_id: Unique session identifier
            session_type: Type of session
            user_id: User identifier
            week_number: Week number for analysis
            analysis_type: Type of analysis
            
        Returns:
            Session ID
        """
        now = datetime.utcnow()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, session_type, user_id, status,
                    week_number, analysis_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, session_type, user_id, 'queued',
                week_number, analysis_type, now, now
            ))
            
            # Initialize status
            cursor.execute("""
                INSERT INTO analysis_status (
                    session_id, status, progress, updated_at
                ) VALUES (?, ?, ?, ?)
            """, (session_id, 'queued', 0, now))
            
            logger.info(f"Created session {session_id}")
            return session_id
    
    def update_session_status(
        self,
        session_id: str,
        status: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        estimated_time_remaining: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            status: New status
            progress: Progress percentage (0-100)
            current_step: Current step description
            estimated_time_remaining: Estimated time remaining in seconds
            error_message: Error message if failed
        """
        now = datetime.utcnow()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Update sessions table
            update_fields = ['status = ?', 'updated_at = ?']
            update_values = [status, now]
            
            if status == 'completed':
                update_fields.append('completed_at = ?')
                update_values.append(now)
            elif status == 'failed':
                update_fields.append('failed_at = ?')
                update_values.append(now)
                if error_message:
                    update_fields.append('error_message = ?')
                    update_values.append(error_message)
            
            update_values.append(session_id)
            cursor.execute(f"""
                UPDATE sessions 
                SET {', '.join(update_fields)}
                WHERE session_id = ?
            """, update_values)
            
            # Update analysis_status table
            if progress is not None:
                status_fields = ['status = ?', 'updated_at = ?']
                status_values = [status, now]
                
                if progress is not None:
                    status_fields.append('progress = ?')
                    status_values.append(progress)
                if current_step:
                    status_fields.append('current_step = ?')
                    status_values.append(current_step)
                if estimated_time_remaining is not None:
                    status_fields.append('estimated_time_remaining_seconds = ?')
                    status_values.append(estimated_time_remaining)
                
                status_values.append(session_id)
                cursor.execute(f"""
                    UPDATE analysis_status 
                    SET {', '.join(status_fields)}
                    WHERE session_id = ?
                """, status_values)
            
            logger.debug(f"Updated session {session_id} status to {status}")
    
    def save_analysis_result(
        self,
        session_id: str,
        report: Dict[str, Any],
        quality_score: float,
        execution_time_ms: int,
        cache_efficiency: float,
        agents_executed: List[str],
        hitl_escalations: int = 0,
        guardrail_violations: int = 0,
        evaluation_passed: bool = False,
        regeneration_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save analysis result.
        
        Args:
            session_id: Session identifier
            report: Analysis report (will be JSON serialized)
            quality_score: Quality score (0-1)
            execution_time_ms: Execution time in milliseconds
            cache_efficiency: Cache efficiency (0-1)
            agents_executed: List of agent types executed
            hitl_escalations: Number of HITL escalations
            guardrail_violations: Number of guardrail violations
            evaluation_passed: Whether evaluation passed
            regeneration_count: Number of regeneration attempts
            metadata: Additional metadata
        """
        now = datetime.utcnow()
        report_json = json.dumps(report) if isinstance(report, dict) else report
        agents_json = json.dumps(agents_executed)
        metadata_json = json.dumps(metadata) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_results (
                    session_id, report, quality_score, execution_time_ms,
                    cache_efficiency, agents_executed, hitl_escalations,
                    guardrail_violations, evaluation_passed, regeneration_count,
                    metadata, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, report_json, quality_score, execution_time_ms,
                cache_efficiency, agents_json, hitl_escalations,
                guardrail_violations, evaluation_passed, regeneration_count,
                metadata_json, now
            ))
            
            logger.info(f"Saved analysis result for session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, st.status as current_status, st.progress, 
                       st.current_step, st.estimated_time_remaining_seconds
                FROM sessions s
                LEFT JOIN analysis_status st ON s.session_id = st.session_id
                WHERE s.session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                session_dict = dict(row)
                # Also get analysis result to include week_number if available
                result = self.get_analysis_result(session_id)
                if result:
                    # Week number might be in metadata
                    metadata = result.get('metadata', {})
                    if metadata and 'week_number' in metadata:
                        session_dict['week_number'] = metadata['week_number']
                return session_dict
            return None
    
    def get_analysis_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis result by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Analysis result or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_results WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse JSON fields
                result['report'] = json.loads(result['report'])
                result['agents_executed'] = json.loads(result['agents_executed'])
                if result['metadata']:
                    result['metadata'] = json.loads(result['metadata'])
                return result
            return None
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Status data or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        result = None
        if session['current_status'] == 'completed':
            result = self.get_analysis_result(session_id)
        
        return {
            'session_id': session_id,
            'status': session['current_status'],
            'progress': session.get('progress', 0),
            'current_step': session.get('current_step'),
            'estimated_time_remaining_seconds': session.get('estimated_time_remaining_seconds'),
            'result': result
        }
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List sessions with optional filters.
        
        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of sessions
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT s.*, st.status as current_status, st.progress
                FROM sessions s
                LEFT JOIN analysis_status st ON s.session_id = st.session_id
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND s.user_id = ?"
                params.append(user_id)
            
            if status:
                query += " AND st.status = ?"
                params.append(status)
            
            query += " ORDER BY s.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete in order due to foreign key constraints
            cursor.execute("DELETE FROM analysis_results WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM analysis_status WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted session {session_id}")
            return deleted


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """
    Get database manager instance (singleton).
    
    Args:
        db_path: Optional database path (only used on first call)
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager

