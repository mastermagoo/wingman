#!/usr/bin/env python3
"""
Validation Results Store
Stores validation results in Postgres validation_results table
"""

import os
import json
import psycopg2
from typing import Dict, Any, Optional


def _get_postgres_connection():
    """Get Postgres connection for validation storage"""
    # Try different environment variable patterns
    db_host = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT', '5432')
    db_name = os.getenv('POSTGRES_DB') or os.getenv('DB_NAME', 'wingman')
    db_user = os.getenv('POSTGRES_USER') or os.getenv('DB_USER', 'wingman')
    db_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD', '')

    return psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )


def store_validation_result(
    approval_id: str,
    validation_result: Dict[str, Any]
) -> bool:
    """
    Store validation result in Postgres validation_results table

    Args:
        approval_id: The approval request ID
        validation_result: Dict from CompositeValidator.validate()

    Returns:
        True if stored successfully, False otherwise
    """
    try:
        conn = _get_postgres_connection()
        cursor = conn.cursor()

        # Check if approval exists in Postgres (may be in-memory mode)
        try:
            cursor.execute("SELECT COUNT(*) FROM approvals WHERE id = %s", (approval_id,))
            approval_exists = cursor.fetchone()[0] > 0
        except Exception:
            # approvals table doesn't exist - approval store is in memory mode
            cursor.close()
            conn.close()
            return True  # Not an error - just skip storage in memory mode

        if not approval_exists:
            # Approval is in memory, skip validation storage
            cursor.close()
            conn.close()
            return True  # Not an error - just skip storage in memory mode

        # Extract validator scores (flat dict of validator_name -> int)
        validator_scores = validation_result.get('validator_scores', {})

        cursor.execute("""
            INSERT INTO validation_results (
                approval_id,
                decision,
                composite_score,
                semantic_analysis,
                code_scan_results,
                dependency_analysis,
                quality_assessment,
                telegram_report
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            approval_id,
            validation_result.get('recommendation', 'MANUAL_REVIEW'),
            validation_result.get('overall_score'),
            json.dumps({
                'score': validator_scores.get('semantic_analyzer', 0),
                'risk_level': validation_result.get('risk_level', 'UNKNOWN')
            }),
            json.dumps({
                'score': validator_scores.get('code_scanner', 0)
            }),
            json.dumps({
                'score': validator_scores.get('dependency_analyzer', 0)
            }),
            json.dumps({
                'score': validator_scores.get('content_quality', 0)
            }),
            validation_result.get('reasoning', '')
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Failed to store validation result: {e}")
        # Don't fail the approval flow if validation storage fails
        return False
