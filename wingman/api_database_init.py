#!/usr/bin/env python3
"""
API Database Initialization Script
Ensures database tables exist and are properly configured for API usage
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intel_integration import IntelDatabase


def initialize_database():
    """
    Initialize database for API server usage
    """
    print("Initializing database for API server...")

    try:
        # Initialize connection
        print("Connecting to database...")
        db = IntelDatabase()

        # Test connection with a simple query
        print("Testing database connection...")
        stats = db.get_stats()
        print(f"Database connected successfully!")
        print(f"Current stats: {stats}")

        # Check if we can write
        print("\nTesting write capability...")
        test_claim = "Database initialization test claim"
        db.log_verification(
            claim=test_claim,
            verdict="TRUE",
            verifier_type="simple",  # Use valid verifier type
            processing_time_ms=1,
            source="api_init"
        )
        print("Write test successful!")

        # Verify the write
        history = db.get_verification_history(page=1, limit=1)
        if history['total'] > 0:
            print(f"Verified write - found {history['total']} verifications in database")

        print("\n✅ Database initialization complete!")
        print("API server can now use database for persistence")

        return True

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure TimescaleDB is running:")
        print("   docker-compose up timescale")
        print("2. Check database credentials in environment variables")
        print("3. Verify database schema is created:")
        print("   Check /Volumes/intel-system/wingman/database_schema.sql")

        return False


def check_environment():
    """
    Check environment variables for database configuration
    """
    print("\nChecking environment configuration...")

    env_vars = {
        'TIMESCALE_HOST': os.environ.get('TIMESCALE_HOST', 'localhost'),
        'TIMESCALE_PORT': os.environ.get('TIMESCALE_PORT', '5432'),
        'TIMESCALE_DB': os.environ.get('TIMESCALE_DB', 'intel'),
        'TIMESCALE_USER': os.environ.get('TIMESCALE_USER', 'intel'),
        'TIMESCALE_PASS': os.environ.get('TIMESCALE_PASS', 'intel')
    }

    print("Database configuration:")
    for key, value in env_vars.items():
        if key == 'TIMESCALE_PASS':
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")

    return env_vars


def wait_for_database(max_attempts=5, delay=2):
    """
    Wait for database to be available
    """
    print(f"\nWaiting for database (max {max_attempts} attempts)...")

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}/{max_attempts}...")
            db = IntelDatabase()
            db.get_stats()
            print("Database is available!")
            return True
        except Exception as e:
            if attempt < max_attempts:
                print(f"  Database not ready: {e}")
                print(f"  Waiting {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"  Failed after {max_attempts} attempts")
                return False

    return False


if __name__ == "__main__":
    print("=" * 60)
    print("API DATABASE INITIALIZATION")
    print("=" * 60)

    # Check environment
    check_environment()

    # Wait for database
    if not wait_for_database():
        print("\n⚠️  Database is not available")
        print("API server will run with in-memory storage fallback")
        sys.exit(1)

    # Initialize database
    if initialize_database():
        print("\n✅ Database ready for API server")
        sys.exit(0)
    else:
        print("\n⚠️  Database initialization incomplete")
        print("API server will run with limited functionality")
        sys.exit(1)