"""
Test Suite for Layer 0 - Context Hub
Validates context collection, latency, and data persistence
"""

import time
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.context_hub import ContextHub
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_context_snapshot_latency():
    """Test 1: Validate context snapshot latency < 100ms"""
    print("\n=== Test 1: Context Snapshot Latency ===")
    
    hub = ContextHub(polling_interval=1.0)
    
    latencies = []
    iterations = 10
    
    for i in range(iterations):
        snapshot = hub.get_context_snapshot()
        latencies.append(snapshot['latency_ms'])
        print(f"  Snapshot {i+1}: {snapshot['latency_ms']}ms")
        time.sleep(0.5)
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    print(f"\n  Average latency: {avg_latency:.1f}ms")
    print(f"  Max latency: {max_latency}ms")
    
    if avg_latency < 100:
        print("  ✅ PASS: Average latency < 100ms")
        return True
    else:
        print("  ❌ FAIL: Average latency >= 100ms")
        return False


def test_data_persistence():
    """Test 2: Validate data persistence to database"""
    print("\n=== Test 2: Data Persistence ===")
    
    hub = ContextHub(polling_interval=2.0, db_path="data/test_orbit.db")
    
    # Get initial stats
    initial_stats = hub.db.get_stats()
    initial_count = initial_stats['total_events']
    print(f"  Initial DB records: {initial_count}")
    
    # Save 5 snapshots
    print("  Saving 5 snapshots...")
    for i in range(5):
        snapshot = hub.get_context_snapshot()
        hub.save_snapshot(snapshot)
        print(f"    Saved snapshot {i+1}")
        time.sleep(0.5)
    
    # Check final stats
    final_stats = hub.db.get_stats()
    final_count = final_stats['total_events']
    added = final_count - initial_count
    
    print(f"  Final DB records: {final_count}")
    print(f"  Added: {added} records")
    
    if added == 5:
        print("  ✅ PASS: All snapshots persisted")
        return True
    else:
        print(f"  ❌ FAIL: Expected 5, got {added}")
        return False


def test_monitor_integration():
    """Test 3: Validate all monitors are working"""
    print("\n=== Test 3: Monitor Integration ===")
    
    hub = ContextHub(polling_interval=2.0)
    
    snapshot = hub.get_context_snapshot()
    
    # Check window monitor
    has_window = snapshot['active_app'] is not None
    print(f"  Window Monitor: {'✅' if has_window else '❌'} (app: {snapshot['active_app']})")
    
    # Check idle detector
    has_idle = snapshot['idle_time'] >= 0
    print(f"  Idle Detector: {'✅' if has_idle else '❌'} (idle: {snapshot['idle_time']}s)")
    
    # Check file watcher (start it first)
    hub.file_watcher.start()
    time.sleep(2)
    file_stats = hub.file_watcher.get_change_summary()
    has_file_watcher = file_stats['is_watching']
    print(f"  File Watcher: {'✅' if has_file_watcher else '❌'} (watching: {file_stats['is_watching']})")
    hub.file_watcher.stop()
    
    # Check database
    try:
        hub.db.get_stats()
        has_db = True
    except Exception:
        has_db = False
    print(f"  Database: {'✅' if has_db else '❌'}")
    
    all_working = has_window and has_idle and has_file_watcher and has_db
    
    if all_working:
        print("\n  ✅ PASS: All monitors integrated")
        return True
    else:
        print("\n  ❌ FAIL: Some monitors not working")
        return False


def test_continuous_monitoring():
    """Test 4: Validate continuous monitoring for 15 seconds"""
    print("\n=== Test 4: Continuous Monitoring (15s) ===")
    
    hub = ContextHub(polling_interval=3.0)
    
    snapshots_collected = []
    
    def collect_snapshot(snapshot):
        snapshots_collected.append(snapshot)
        print(f"  [{snapshot['timestamp']}] Snapshot #{snapshot['snapshot_count']} - Latency: {snapshot['latency_ms']}ms")
    
    hub.start(save_to_db=False, callback=collect_snapshot)
    
    print("  Monitoring for 15 seconds...")
    time.sleep(15)
    
    hub.stop()
    
    print(f"\n  Collected {len(snapshots_collected)} snapshots")
    
    # Should collect ~5 snapshots in 15s with 3s interval
    if len(snapshots_collected) >= 4:
        print("  ✅ PASS: Continuous monitoring working")
        return True
    else:
        print("  ❌ FAIL: Too few snapshots collected")
        return False


def test_error_handling():
    """Test 5: Validate error handling"""
    print("\n=== Test 5: Error Handling ===")
    
    hub = ContextHub(polling_interval=1.0)
    
    # Simulate error condition (invalid path)
    hub.file_watcher.watch_path = Path("/nonexistent/path/that/does/not/exist")
    
    try:
        # This should handle the error gracefully
        snapshot = hub.get_context_snapshot()
        print(f"  Snapshot with error: {snapshot['error_count']} errors")
        print("  ✅ PASS: Error handled gracefully")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Unhandled exception: {e}")
        return False


def run_all_tests():
    """Run all Layer 0 tests"""
    print("\n" + "="*60)
    print("ORBIT Layer 0 - Context Hub Test Suite")
    print("="*60)
    
    results = []
    
    try:
        results.append(("Latency Test", test_context_snapshot_latency()))
        results.append(("Persistence Test", test_data_persistence()))
        results.append(("Integration Test", test_monitor_integration()))
        results.append(("Continuous Monitoring", test_continuous_monitoring()))
        results.append(("Error Handling", test_error_handling()))
        
    except Exception as e:
        logger.error(f"Test suite error: {e}")
        print(f"\n❌ Test suite crashed: {e}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED - Layer 0 is ready!")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed - needs attention")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
