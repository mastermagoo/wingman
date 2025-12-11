#!/usr/bin/env python3
"""
Paul Wingman - Intel System Database Integration
Connects to TimescaleDB to store verification logs and provide analytics
"""

import os
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import ThreadedConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('TIMESCALE_HOST', 'localhost'),
    'port': int(os.getenv('TIMESCALE_PORT', '5432')),
    'database': os.getenv('TIMESCALE_DB', 'intel'),
    'user': os.getenv('TIMESCALE_USER', 'intel'),
    'password': os.getenv('TIMESCALE_PASS', 'intel')
}


class IntelDatabase:
    """Database interface for Paul Wingman verification logs"""

    def __init__(self, min_conn: int = 2, max_conn: int = 10):
        """
        Initialize database connection pool

        Args:
            min_conn: Minimum number of connections in pool
            max_conn: Maximum number of connections in pool
        """
        self.pool = None
        self._initialize_pool(min_conn, max_conn)

    def _initialize_pool(self, min_conn: int, max_conn: int) -> None:
        """Initialize connection pool with retry logic"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.pool = ThreadedConnectionPool(
                    min_conn,
                    max_conn,
                    **DB_CONFIG
                )
                logger.info(f"Database connection pool initialized (attempt {attempt + 1})")
                return
            except psycopg2.Error as e:
                logger.error(f"Failed to connect to database (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def log_verification(self,
                        claim: str,
                        verdict: str,
                        verifier_type: str = 'simple',
                        details: Optional[Dict] = None,
                        source: str = 'api',
                        processing_time_ms: Optional[int] = None,
                        confidence_score: Optional[float] = None,
                        evidence_found: Optional[List[str]] = None,
                        checked_sources: Optional[List[str]] = None,
                        error_message: Optional[str] = None) -> bool:
        """
        Log a verification result to the database

        Args:
            claim: The claim text that was verified
            verdict: Verification result (TRUE, FALSE, UNCERTAIN, ERROR)
            verifier_type: Type of verifier used (simple, enhanced, hybrid)
            details: Additional details as JSON
            source: Source of the verification request
            processing_time_ms: Time taken to process in milliseconds
            confidence_score: Confidence score between 0 and 1
            evidence_found: List of evidence strings found
            checked_sources: List of sources that were checked
            error_message: Error message if verdict is ERROR

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                    INSERT INTO verification_logs (
                        claim, verdict, verifier_type, details, source,
                        processing_time_ms, confidence_score, evidence_found,
                        checked_sources, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, timestamp
                    """

                    cursor.execute(query, (
                        claim,
                        verdict,
                        verifier_type,
                        Json(details) if details else None,
                        source,
                        processing_time_ms,
                        confidence_score,
                        evidence_found,
                        checked_sources,
                        error_message
                    ))

                    result = cursor.fetchone()
                    logger.info(f"Logged verification {result[0]} at {result[1]}: {verdict} for '{claim[:50]}...'")
                    return True

        except Exception as e:
            logger.error(f"Failed to log verification: {e}")
            return False

    def get_stats(self, time_range: str = '24h', hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get verification statistics for a time range

        Args:
            time_range: Time range string (e.g., '24h', '7d', '30d', '1h')
            hours: Alternative way to specify time range in hours

        Returns:
            Dictionary with statistics
        """
        # Handle hours parameter
        if hours:
            interval = f"{hours} hours"
            time_range = f"{hours}h" if hours <= 24 else f"{hours//24}d"
        else:
            # Parse time range
            interval_map = {
                '1h': '1 hour',
                '24h': '24 hours',
                '7d': '7 days',
                '30d': '30 days'
            }
            interval = interval_map.get(time_range, '24 hours')

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Overall stats
                    cursor.execute("""
                    SELECT
                        COUNT(*) as total_verifications,
                        COUNT(DISTINCT claim) as unique_claims,
                        AVG(processing_time_ms) as avg_processing_time,
                        AVG(confidence_score) as avg_confidence
                    FROM verification_logs
                    WHERE timestamp > NOW() - INTERVAL %s
                    """, (interval,))
                    overall = cursor.fetchone()

                    # Verdict breakdown
                    cursor.execute("""
                    SELECT
                        verdict,
                        COUNT(*) as count,
                        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
                    FROM verification_logs
                    WHERE timestamp > NOW() - INTERVAL %s
                    GROUP BY verdict
                    ORDER BY count DESC
                    """, (interval,))
                    verdicts = cursor.fetchall()

                    # Verifier performance
                    cursor.execute("""
                    SELECT
                        verifier_type,
                        COUNT(*) as count,
                        AVG(processing_time_ms) as avg_time,
                        AVG(confidence_score) as avg_confidence
                    FROM verification_logs
                    WHERE timestamp > NOW() - INTERVAL %s
                    GROUP BY verifier_type
                    ORDER BY count DESC
                    """, (interval,))
                    verifiers = cursor.fetchall()

                    # Top false claims
                    cursor.execute("""
                    SELECT
                        claim,
                        COUNT(*) as occurrences
                    FROM verification_logs
                    WHERE verdict = 'FALSE'
                        AND timestamp > NOW() - INTERVAL %s
                    GROUP BY claim
                    ORDER BY occurrences DESC
                    LIMIT 10
                    """, (interval,))
                    top_false = cursor.fetchall()

                    return {
                        'time_range': time_range,
                        'overall': dict(overall) if overall else {},
                        'verdict_breakdown': [dict(v) for v in verdicts],
                        'verifier_performance': [dict(v) for v in verifiers],
                        'top_false_claims': [dict(f) for f in top_false]
                    }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}

    def get_history(self, limit: int = 100, offset: int = 0,
                   verdict_filter: Optional[str] = None,
                   verifier_filter: Optional[str] = None) -> List[Dict]:
        """
        Get recent verification history

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            verdict_filter: Filter by verdict (TRUE, FALSE, UNCERTAIN, ERROR)
            verifier_filter: Filter by verifier type

        Returns:
            List of verification records
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Build query with optional filters
                    query = """
                    SELECT
                        id, timestamp, claim, verdict, verifier_type,
                        source, processing_time_ms, confidence_score,
                        evidence_found, checked_sources, error_message
                    FROM verification_logs
                    WHERE 1=1
                    """
                    params = []

                    if verdict_filter:
                        query += " AND verdict = %s"
                        params.append(verdict_filter)

                    if verifier_filter:
                        query += " AND verifier_type = %s"
                        params.append(verifier_filter)

                    query += """
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                    """
                    params.extend([limit, offset])

                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    # Convert to list of dicts with datetime handling
                    history = []
                    for row in results:
                        record = dict(row)
                        if record.get('timestamp'):
                            record['timestamp'] = record['timestamp'].isoformat()
                        history.append(record)

                    return history

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def get_verification_history(self, page: int = 1, limit: int = 50) -> Dict:
        """
        Get paginated verification history

        Args:
            page: Page number (1-based)
            limit: Records per page

        Returns:
            Dict with verifications list and total count
        """
        try:
            offset = (page - 1) * limit
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get total count
                    cursor.execute("SELECT COUNT(*) as total FROM verification_logs")
                    total = cursor.fetchone()['total']

                    # Get paginated results
                    history = self.get_history(limit=limit, offset=offset)

                    return {
                        'verifications': history,
                        'total': total,
                        'page': page,
                        'limit': limit
                    }
        except Exception as e:
            logger.error(f"Failed to get verification history: {e}")
            return {'verifications': [], 'total': 0, 'page': page, 'limit': limit}

    def get_false_claims_analytics(self) -> Dict:
        """
        Get analytics on false claims

        Returns:
            Dict with false claims analytics
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get top false claims with counts
                    cursor.execute("""
                    SELECT
                        claim,
                        COUNT(*) as count,
                        MAX(timestamp) as last_seen
                    FROM verification_logs
                    WHERE verdict = 'FALSE'
                    GROUP BY claim
                    ORDER BY count DESC
                    LIMIT 20
                    """)
                    false_claims = cursor.fetchall()

                    # Convert timestamps
                    for claim in false_claims:
                        if claim.get('last_seen'):
                            claim['last_seen'] = claim['last_seen'].isoformat()

                    # Get total false count
                    cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM verification_logs
                    WHERE verdict = 'FALSE'
                    """)
                    total_false = cursor.fetchone()['total']

                    return {
                        'false_claims': false_claims,
                        'total_false': total_false
                    }
        except Exception as e:
            logger.error(f"Failed to get false claims analytics: {e}")
            return {'false_claims': [], 'total_false': 0}

    def get_false_claims(self, days: int = 7) -> List[Dict]:
        """
        Get all FALSE verdict claims with details

        Args:
            days: Number of days to look back

        Returns:
            List of false claims with details
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                    SELECT
                        claim,
                        COUNT(*) as occurrences,
                        MIN(timestamp) as first_seen,
                        MAX(timestamp) as last_seen,
                        ARRAY_AGG(DISTINCT source) as sources,
                        ARRAY_AGG(DISTINCT verifier_type) as verifiers_used
                    FROM verification_logs
                    WHERE verdict = 'FALSE'
                        AND timestamp > NOW() - INTERVAL '%s days'
                    GROUP BY claim
                    ORDER BY occurrences DESC
                    """, (days,))

                    results = []
                    for row in cursor.fetchall():
                        record = dict(row)
                        record['first_seen'] = record['first_seen'].isoformat()
                        record['last_seen'] = record['last_seen'].isoformat()
                        results.append(record)

                    return results

        except Exception as e:
            logger.error(f"Failed to get false claims: {e}")
            return []

    def get_verifier_performance(self, days: int = 7) -> Dict[str, Dict]:
        """
        Compare performance between verifier types

        Args:
            days: Number of days to analyze

        Returns:
            Performance metrics for each verifier type
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                    SELECT
                        verifier_type,
                        COUNT(*) as total_verifications,
                        SUM(CASE WHEN verdict = 'TRUE' THEN 1 ELSE 0 END) as true_count,
                        SUM(CASE WHEN verdict = 'FALSE' THEN 1 ELSE 0 END) as false_count,
                        SUM(CASE WHEN verdict = 'UNCERTAIN' THEN 1 ELSE 0 END) as uncertain_count,
                        SUM(CASE WHEN verdict = 'ERROR' THEN 1 ELSE 0 END) as error_count,
                        AVG(processing_time_ms) as avg_processing_time,
                        MIN(processing_time_ms) as min_processing_time,
                        MAX(processing_time_ms) as max_processing_time,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_time_ms) as median_processing_time,
                        AVG(confidence_score) as avg_confidence,
                        MIN(confidence_score) as min_confidence,
                        MAX(confidence_score) as max_confidence
                    FROM verification_logs
                    WHERE timestamp > NOW() - INTERVAL '%s days'
                    GROUP BY verifier_type
                    """, (days,))

                    performance = {}
                    for row in cursor.fetchall():
                        verifier = row['verifier_type']
                        performance[verifier] = {
                            'total': row['total_verifications'],
                            'verdicts': {
                                'true': row['true_count'],
                                'false': row['false_count'],
                                'uncertain': row['uncertain_count'],
                                'error': row['error_count']
                            },
                            'processing_time': {
                                'avg': float(row['avg_processing_time']) if row['avg_processing_time'] else 0,
                                'min': row['min_processing_time'],
                                'max': row['max_processing_time'],
                                'median': float(row['median_processing_time']) if row['median_processing_time'] else 0
                            },
                            'confidence': {
                                'avg': float(row['avg_confidence']) if row['avg_confidence'] else 0,
                                'min': float(row['min_confidence']) if row['min_confidence'] else 0,
                                'max': float(row['max_confidence']) if row['max_confidence'] else 0
                            }
                        }

                    return performance

        except Exception as e:
            logger.error(f"Failed to get verifier performance: {e}")
            return {}

    def search_claims(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search claims by keyword using full-text search

        Args:
            keyword: Search keyword
            limit: Maximum results to return

        Returns:
            List of matching claims
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                    SELECT
                        id, timestamp, claim, verdict, verifier_type,
                        confidence_score, processing_time_ms,
                        ts_rank(to_tsvector('english', claim), plainto_tsquery('english', %s)) as relevance
                    FROM verification_logs
                    WHERE to_tsvector('english', claim) @@ plainto_tsquery('english', %s)
                    ORDER BY relevance DESC, timestamp DESC
                    LIMIT %s
                    """, (keyword, keyword, limit))

                    results = []
                    for row in cursor.fetchall():
                        record = dict(row)
                        record['timestamp'] = record['timestamp'].isoformat()
                        results.append(record)

                    return results

        except Exception as e:
            logger.error(f"Failed to search claims: {e}")
            return []

    def update_performance_stats(self) -> bool:
        """Update daily performance statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT update_performance_stats()")
                    cursor.execute("SELECT update_false_patterns()")
                    logger.info("Performance stats updated successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to update performance stats: {e}")
            return False

    def refresh_materialized_views(self) -> bool:
        """Refresh materialized views for faster queries"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT refresh_hourly_stats()")
                    logger.info("Materialized views refreshed successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to refresh materialized views: {e}")
            return False

    def create_schema(self) -> bool:
        """Create database schema if it doesn't exist"""
        try:
            schema_file = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
            with open(schema_file, 'r') as f:
                schema_sql = f.read()

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    logger.info("Database schema created/updated successfully")
                    return True

        except FileNotFoundError:
            logger.error(f"Schema file not found: database_schema.sql")
            return False
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False

    def close(self):
        """Close all database connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Convenience functions for standalone usage
def test_connection():
    """Test database connection"""
    try:
        db = IntelDatabase()
        stats = db.get_stats('1h')
        print(f"Database connection successful. Stats: {stats}")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def log_test_verification():
    """Log a test verification"""
    try:
        db = IntelDatabase()
        success = db.log_verification(
            claim="Test claim from intel_integration.py",
            verdict="TRUE",
            verifier_type="simple",
            details={"test": True, "source": "manual"},
            processing_time_ms=100,
            confidence_score=0.95,
            evidence_found=["Test evidence 1", "Test evidence 2"],
            checked_sources=["filesystem", "processes"]
        )
        print(f"Test verification logged: {success}")
        db.close()
        return success
    except Exception as e:
        print(f"Failed to log test verification: {e}")
        return False


if __name__ == "__main__":
    # Test the database connection and basic operations
    print("Testing Intel Database Integration...")

    if test_connection():
        print("✓ Connection test passed")

        if log_test_verification():
            print("✓ Verification logging test passed")

            # Get and display stats
            db = IntelDatabase()
            stats = db.get_stats('24h')
            # Convert Decimals to floats for JSON serialization
            stats_json = json.dumps(stats, indent=2, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))
            print(f"\n24-hour stats: {stats_json}")

            # Get recent history
            history = db.get_history(limit=5)
            print(f"\nRecent verifications: {len(history)} records")

            db.close()
        else:
            print("✗ Verification logging test failed")
    else:
        print("✗ Connection test failed")