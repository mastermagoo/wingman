#!/usr/bin/env python3
"""
Comprehensive database integration tests for Paul Wingman
Tests all functions and generates sample data
"""

import time
import random
from datetime import datetime, timedelta
from intel_integration import IntelDatabase

# Test claims dataset
TEST_CLAIMS = [
    ("The Earth is flat", "FALSE", "enhanced", 0.98),
    ("Water boils at 100°C at sea level", "TRUE", "simple", 0.95),
    ("COVID-19 vaccines contain microchips", "FALSE", "enhanced", 0.99),
    ("The moon landing was faked", "FALSE", "enhanced", 0.97),
    ("Python is a programming language", "TRUE", "simple", 1.0),
    ("5G towers cause health problems", "FALSE", "enhanced", 0.96),
    ("Climate change is real", "TRUE", "enhanced", 0.94),
    ("The Great Wall of China is visible from space", "FALSE", "simple", 0.92),
    ("Vaccines cause autism", "FALSE", "enhanced", 0.99),
    ("The sun rises in the east", "TRUE", "simple", 1.0),
    ("Birds aren't real", "FALSE", "simple", 0.85),
    ("Quantum computers exist", "TRUE", "enhanced", 0.88),
    ("AI will replace all jobs by 2025", "UNCERTAIN", "enhanced", 0.45),
    ("Mars has water", "TRUE", "enhanced", 0.91),
    ("The pyramids were built by aliens", "FALSE", "enhanced", 0.95)
]

def populate_test_data(db: IntelDatabase, num_records: int = 50):
    """Populate database with test verification records"""
    print(f"\n📊 Populating {num_records} test records...")

    sources = ['api', 'telegram', 'web', 'cli', 'manual']
    success_count = 0

    for i in range(num_records):
        claim, verdict, verifier, confidence = random.choice(TEST_CLAIMS)

        # Add some variation to the claim
        if random.random() > 0.7:
            claim += f" (variant {i})"

        # Random processing time
        processing_time = random.randint(50, 500)

        # Random source
        source = random.choice(sources)

        # Evidence for true/false claims
        evidence = []
        checked = []
        if verdict == "TRUE":
            evidence = [f"Scientific fact #{i}", f"Peer reviewed study"]
            checked = ["wikipedia", "scientific_journals"]
        elif verdict == "FALSE":
            evidence = [f"Debunked by experts", f"No credible evidence"]
            checked = ["fact_checkers", "scientific_consensus"]
        elif verdict == "UNCERTAIN":
            evidence = [f"Insufficient data"]
            checked = ["multiple_sources"]

        success = db.log_verification(
            claim=claim,
            verdict=verdict,
            verifier_type=verifier,
            source=source,
            processing_time_ms=processing_time,
            confidence_score=confidence + random.uniform(-0.05, 0.05),
            evidence_found=evidence,
            checked_sources=checked
        )

        if success:
            success_count += 1

        # Small delay to spread timestamps
        time.sleep(0.01)

    print(f"✅ Successfully inserted {success_count}/{num_records} records")
    return success_count

def test_all_functions(db: IntelDatabase):
    """Test all database functions"""
    print("\n🧪 Testing all database functions...")

    # Test 1: Stats
    print("\n1. Testing get_stats()...")
    for time_range in ['1h', '24h', '7d', '30d']:
        stats = db.get_stats(time_range)
        if 'error' not in stats:
            total = stats['overall'].get('total_verifications', 0)
            print(f"   {time_range}: {total} verifications")

    # Test 2: History
    print("\n2. Testing get_history()...")
    history = db.get_history(limit=10)
    print(f"   Retrieved {len(history)} recent records")

    # Test 3: History with filters
    print("\n3. Testing filtered history...")
    false_history = db.get_history(limit=5, verdict_filter='FALSE')
    print(f"   FALSE verdicts: {len(false_history)} records")

    # Test 4: False claims
    print("\n4. Testing get_false_claims()...")
    false_claims = db.get_false_claims(days=7)
    print(f"   Found {len(false_claims)} unique false claims")
    if false_claims:
        top_false = false_claims[0]
        print(f"   Top false claim: '{top_false['claim'][:50]}...' ({top_false['occurrences']} times)")

    # Test 5: Verifier performance
    print("\n5. Testing get_verifier_performance()...")
    performance = db.get_verifier_performance(days=7)
    for verifier, metrics in performance.items():
        print(f"   {verifier}: {metrics['total']} verifications, "
              f"avg time: {metrics['processing_time']['avg']:.0f}ms")

    # Test 6: Search
    print("\n6. Testing search_claims()...")
    search_results = db.search_claims("vaccine")
    print(f"   Search 'vaccine': {len(search_results)} results")
    search_results = db.search_claims("earth")
    print(f"   Search 'earth': {len(search_results)} results")

    # Test 7: Update stats
    print("\n7. Testing update_performance_stats()...")
    success = db.update_performance_stats()
    print(f"   Stats update: {'✅ Success' if success else '❌ Failed'}")

    # Test 8: Refresh views
    print("\n8. Testing refresh_materialized_views()...")
    success = db.refresh_materialized_views()
    print(f"   View refresh: {'✅ Success' if success else '❌ Failed'}")

def stress_test(db: IntelDatabase, num_operations: int = 100):
    """Stress test with rapid operations"""
    print(f"\n⚡ Stress testing with {num_operations} rapid operations...")

    start_time = time.time()
    success_count = 0

    for i in range(num_operations):
        claim = f"Stress test claim #{i}"
        verdict = random.choice(['TRUE', 'FALSE', 'UNCERTAIN'])

        success = db.log_verification(
            claim=claim,
            verdict=verdict,
            verifier_type='simple',
            processing_time_ms=random.randint(10, 100),
            confidence_score=random.random()
        )

        if success:
            success_count += 1

    elapsed = time.time() - start_time
    ops_per_sec = num_operations / elapsed

    print(f"✅ Completed {success_count}/{num_operations} operations")
    print(f"⏱️  Time: {elapsed:.2f}s ({ops_per_sec:.1f} ops/sec)")

def display_dashboard(db: IntelDatabase):
    """Display a dashboard-style summary"""
    print("\n📊 WINGMAN VERIFICATION DASHBOARD")
    print("=" * 50)

    # Get 24h stats
    stats = db.get_stats('24h')

    if 'overall' in stats:
        overall = stats['overall']
        print(f"\n📈 Last 24 Hours:")
        print(f"   Total Verifications: {overall.get('total_verifications', 0)}")
        print(f"   Unique Claims: {overall.get('unique_claims', 0)}")

        avg_time = overall.get('avg_processing_time')
        if avg_time:
            print(f"   Avg Processing Time: {float(avg_time):.0f}ms")

        avg_conf = overall.get('avg_confidence')
        if avg_conf:
            print(f"   Avg Confidence: {avg_conf:.2%}")

    if 'verdict_breakdown' in stats:
        print(f"\n⚖️ Verdict Distribution:")
        for verdict in stats['verdict_breakdown']:
            print(f"   {verdict['verdict']:10s}: {verdict['count']:4d} ({float(verdict['percentage']):.1f}%)")

    if 'verifier_performance' in stats:
        print(f"\n🔧 Verifier Performance:")
        for verifier in stats['verifier_performance']:
            print(f"   {verifier['verifier_type']:10s}: {verifier['count']} checks, "
                  f"avg {float(verifier['avg_time']):.0f}ms")

    if 'top_false_claims' in stats and stats['top_false_claims']:
        print(f"\n❌ Top False Claims:")
        for i, claim in enumerate(stats['top_false_claims'][:5], 1):
            print(f"   {i}. '{claim['claim'][:40]}...' ({claim['occurrences']}x)")

    print("\n" + "=" * 50)

def main():
    """Main test execution"""
    print("🚀 Paul Wingman Database Integration Test Suite")
    print("=" * 50)

    # Initialize database
    db = IntelDatabase()

    try:
        # Populate test data
        populate_test_data(db, num_records=50)

        # Test all functions
        test_all_functions(db)

        # Stress test
        stress_test(db, num_operations=100)

        # Display dashboard
        display_dashboard(db)

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")

    finally:
        db.close()
        print("\n🔒 Database connection closed")

if __name__ == "__main__":
    main()