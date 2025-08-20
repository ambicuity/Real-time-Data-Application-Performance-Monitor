#!/usr/bin/env python3
"""
Example: Basic Performance Monitoring

This example demonstrates basic usage of the performance monitoring tool.
"""

import time
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from performance_monitor.cli import PerformanceMonitorApp


def main():
    print("🔍 Real-time Performance Monitor - Basic Example")
    print("=" * 50)
    
    # Create the monitoring application
    app = PerformanceMonitorApp()
    
    print("Starting performance monitoring with simulation...")
    print("This will run for 60 seconds with normal load simulation.")
    print("Press Ctrl+C to stop early.\n")
    
    try:
        # Start monitoring with simulation for 60 seconds
        app.start_monitoring(
            simulate=True,
            scenario="normal_load",
            duration=60
        )
        
        print("\n✅ Monitoring completed successfully!")
        
        # Generate a quick console report
        print("\n📊 Generating performance report...")
        app.reporter.generate_console_report(hours=1)
        
        # Generate HTML report
        report_path = "basic_example_report.html"
        app.generate_report(report_path, "html", 1)
        print(f"\n📄 HTML report saved to: {report_path}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Monitoring interrupted by user.")
        app.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        app.stop_monitoring()


if __name__ == "__main__":
    main()