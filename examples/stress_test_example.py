#!/usr/bin/env python3
"""
Example: Stress Testing and Performance Analysis

This example demonstrates stress testing capabilities and advanced analysis.
"""

import time
import sys
import os
import threading

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from performance_monitor.cli import PerformanceMonitorApp
from performance_monitor.data_simulator import WorkloadScenario


def run_stress_test_scenario(app, scenario_name, duration=120):
    """Run a specific stress test scenario."""
    print(f"\n🔥 Running stress test: {scenario_name}")
    print(f"Duration: {duration} seconds")
    print("-" * 40)
    
    try:
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=lambda: app.start_monitoring(
                simulate=True,
                scenario=scenario_name,
                duration=duration
            ),
            daemon=True
        )
        
        monitor_thread.start()
        
        # Wait for completion
        monitor_thread.join()
        
        print(f"✅ {scenario_name} completed successfully!")
        
        # Analyze issues
        issues = app.analyzer.identify_performance_issues()
        if issues:
            print(f"\n⚠️  Issues found during {scenario_name}:")
            for issue in issues:
                print(f"  - {issue['type']}: {issue['description']}")
        else:
            print(f"\n✅ No performance issues detected in {scenario_name}")
            
        return issues
        
    except Exception as e:
        print(f"❌ Error in {scenario_name}: {e}")
        return []


def main():
    print("🔥 Performance Monitor - Stress Testing Example")
    print("=" * 50)
    
    # Create the monitoring application with stress test config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'stress_test.yaml')
    app = PerformanceMonitorApp(config_path)
    
    # Define stress test scenarios
    stress_scenarios = [
        ("normal_load", 60),
        ("high_load", 90),
        ("bursty_traffic", 120),
        ("overload", 60)
    ]
    
    all_issues = []
    
    print("Running comprehensive stress test suite...")
    print("This will test various load conditions and identify bottlenecks.\n")
    
    try:
        for scenario, duration in stress_scenarios:
            issues = run_stress_test_scenario(app, scenario, duration)
            all_issues.extend(issues)
            
            # Brief pause between tests
            print("\n⏸️  Pausing for 10 seconds between tests...")
            time.sleep(10)
            
        print("\n" + "=" * 50)
        print("🏁 STRESS TEST SUMMARY")
        print("=" * 50)
        
        if all_issues:
            print(f"\n⚠️  Total issues identified: {len(all_issues)}")
            
            # Group issues by type
            issue_counts = {}
            for issue in all_issues:
                issue_type = issue['type']
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                
            print("\nIssue breakdown:")
            for issue_type, count in issue_counts.items():
                print(f"  - {issue_type}: {count} occurrences")
                
        else:
            print("\n✅ No performance issues detected across all scenarios!")
            print("System handled all stress test scenarios successfully.")
            
        # Generate comprehensive report
        report_path = "stress_test_report.html"
        app.generate_report(report_path, "html", 2)
        print(f"\n📄 Comprehensive stress test report saved to: {report_path}")
        
        # Generate console summary
        print("\n📊 Final Performance Summary:")
        app.reporter.generate_console_report(hours=2)
        
    except KeyboardInterrupt:
        print("\n⚠️  Stress testing interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during stress testing: {e}")
    finally:
        app.stop_monitoring()


if __name__ == "__main__":
    main()