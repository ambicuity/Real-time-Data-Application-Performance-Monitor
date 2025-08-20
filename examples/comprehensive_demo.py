#!/usr/bin/env python3
"""
Example: Comprehensive Performance Analysis Demo

This example demonstrates all major features of the performance monitoring tool.
"""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from performance_monitor.cli import PerformanceMonitorApp
from performance_monitor.data_simulator import WorkloadScenario


def run_comprehensive_demo():
    """Run a comprehensive demonstration of all features."""
    
    print("🚀 Real-time Performance Monitor - Comprehensive Demo")
    print("=" * 60)
    print("This demo will showcase all major features of the tool:")
    print("• Real-time metrics collection")
    print("• Performance analysis and issue detection")
    print("• Multiple simulation scenarios")
    print("• Comprehensive reporting")
    print("• Troubleshooting assistance")
    print("=" * 60)
    
    # Create the monitoring application
    app = PerformanceMonitorApp()
    
    # Phase 1: Baseline Performance Test
    print("\n🔍 PHASE 1: Baseline Performance Analysis")
    print("-" * 40)
    print("Running normal load scenario for 30 seconds...")
    
    try:
        app.start_monitoring(
            simulate=True,
            scenario="normal_load",
            duration=30
        )
        
        print("✅ Baseline test completed!")
        
        # Generate quick console report
        print("\n📊 Baseline Performance Summary:")
        app.reporter.generate_console_report(hours=1)
        
    except Exception as e:
        print(f"❌ Error in baseline test: {e}")
        return
        
    # Brief pause
    time.sleep(5)
    
    # Phase 2: Stress Testing
    print("\n🔥 PHASE 2: Stress Testing Analysis")
    print("-" * 40)
    print("Running high-load scenario to identify bottlenecks...")
    
    try:
        app.start_monitoring(
            simulate=True,
            scenario="high_load", 
            duration=30
        )
        
        print("✅ Stress test completed!")
        
        # Analyze issues detected during stress test
        issues = app.analyzer.identify_performance_issues()
        if issues:
            print(f"\n⚠️  Performance Issues Detected ({len(issues)}):")
            for issue in issues:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.get('severity', 'info'), "⚪")
                print(f"  {severity_icon} {issue['type']}: {issue['description']}")
        else:
            print("\n✅ No performance issues detected during stress test!")
            
    except Exception as e:
        print(f"❌ Error in stress test: {e}")
        return
        
    # Brief pause
    time.sleep(5)
    
    # Phase 3: Bursty Traffic Analysis
    print("\n📈 PHASE 3: Bursty Traffic Pattern Analysis")
    print("-" * 40)
    print("Testing system response to variable load patterns...")
    
    try:
        app.start_monitoring(
            simulate=True,
            scenario="bursty_traffic",
            duration=45  # Longer to see burst patterns
        )
        
        print("✅ Bursty traffic test completed!")
        
        # Analyze performance trends
        trends = app.analyzer.analyze_performance_trends(hours=1)
        if trends:
            print("\n📊 Performance Trends Detected:")
            for metric_type, trend_info in trends.items():
                trend = trend_info.get('trend', 'unknown')
                trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(trend, "❓")
                print(f"  {trend_icon} {metric_type}: {trend} (avg: {trend_info.get('mean', 0):.2f})")
                
    except Exception as e:
        print(f"❌ Error in bursty traffic test: {e}")
        return
        
    # Phase 4: Final Analysis and Reporting
    print("\n📄 PHASE 4: Comprehensive Reporting")
    print("-" * 40)
    
    try:
        # Generate multiple report formats
        html_report = "comprehensive_demo_report.html"
        json_report = "comprehensive_demo_report.json"
        
        print("Generating comprehensive HTML report...")
        app.generate_report(html_report, "html", 2)
        print(f"📄 HTML report saved to: {html_report}")
        
        print("Generating JSON data export...")
        app.generate_report(json_report, "json", 2)
        print(f"📄 JSON report saved to: {json_report}")
        
        # Final console summary
        print("\n📊 FINAL PERFORMANCE SUMMARY:")
        print("=" * 40)
        app.reporter.generate_console_report(hours=2)
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        
    # Phase 5: Recommendations
    print("\n💡 PHASE 5: Performance Recommendations")
    print("-" * 40)
    
    # Get recent metrics for analysis
    recent_metrics = app.metrics_collector.get_recent_metrics(7200)  # 2 hours
    latency_stats = app.metrics_collector.get_current_latency_stats()
    
    print("Based on the comprehensive analysis, here are the key findings:")
    
    if latency_stats:
        p95_latency = latency_stats.get('p95', 0)
        if p95_latency > 500:
            print("⚠️  High latency detected - consider optimizing processing algorithms")
        elif p95_latency < 100:
            print("✅ Excellent latency performance - system is well-optimized")
        else:
            print("✅ Good latency performance - within acceptable ranges")
            
    print(f"📊 Total metrics collected: {len(recent_metrics):,}")
    print("📈 Performance monitoring completed successfully!")
    
    # Summary of capabilities demonstrated
    print("\n🎯 CAPABILITIES DEMONSTRATED:")
    print("✅ Real-time metrics collection (latency, throughput, system resources)")
    print("✅ Performance analysis and trend identification")
    print("✅ Automated issue detection and alerting")
    print("✅ Multiple simulation scenarios for comprehensive testing")
    print("✅ Rich reporting in multiple formats (HTML, JSON, console)")
    print("✅ Troubleshooting assistance and optimization recommendations")
    print("✅ Impact analysis of performance changes over time")
    
    print("\n🏁 Demo completed successfully!")
    print("Check the generated reports for detailed analysis.")


def main():
    """Main demo entry point."""
    print("Starting comprehensive performance monitoring demo...")
    print("This will run for approximately 3-4 minutes and test various scenarios.")
    print("\nPress Ctrl+C at any time to stop the demo.\n")
    
    try:
        run_comprehensive_demo()
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error in demo: {e}")


if __name__ == "__main__":
    main()