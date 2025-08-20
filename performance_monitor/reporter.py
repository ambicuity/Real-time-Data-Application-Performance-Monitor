"""
Performance Reporter Module

Generates comprehensive reports and visualizations of performance data.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import seaborn as sns
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from .metrics_collector import MetricsCollector, PerformanceAnalyzer


class PerformanceReporter:
    """Generates performance reports and visualizations."""
    
    def __init__(self, collector: MetricsCollector, analyzer: PerformanceAnalyzer):
        self.collector = collector
        self.analyzer = analyzer
        
    def generate_html_report(self, output_path: str, hours: int = 1):
        """Generate HTML performance report."""
        # Collect data for report
        report_data = self._collect_report_data(hours)
        
        # Generate HTML content
        html_content = self._generate_html_content(report_data)
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)
            
    def generate_json_report(self, output_path: str, hours: int = 1):
        """Generate JSON performance report."""
        report_data = self._collect_report_data(hours)
        
        # Convert to JSON-serializable format
        json_data = self._prepare_json_data(report_data)
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
            
    def generate_console_report(self, hours: int = 1):
        """Generate and print console report."""
        report_data = self._collect_report_data(hours)
        
        print("\n" + "="*60)
        print(f"PERFORMANCE REPORT - Last {hours} hour(s)")
        print("="*60)
        
        # Summary statistics
        if report_data['summary']:
            print(f"\n📊 SUMMARY")
            print("-" * 20)
            summary = report_data['summary']
            print(f"Total Metrics Collected: {summary.get('total_metrics', 0):,}")
            print(f"Time Range: {summary.get('start_time', 'N/A')} to {summary.get('end_time', 'N/A')}")
            
        # Latency statistics
        if report_data['latency_stats']:
            print(f"\n⏱️  LATENCY METRICS")
            print("-" * 20)
            latency = report_data['latency_stats']
            print(f"Mean Latency: {latency.get('mean', 0):.2f}ms")
            print(f"Median Latency: {latency.get('median', 0):.2f}ms")
            print(f"95th Percentile: {latency.get('p95', 0):.2f}ms")
            print(f"99th Percentile: {latency.get('p99', 0):.2f}ms")
            print(f"Min/Max: {latency.get('min', 0):.2f}ms / {latency.get('max', 0):.2f}ms")
            
        # System metrics
        if report_data['system_stats']:
            print(f"\n🖥️  SYSTEM METRICS")
            print("-" * 20)
            system = report_data['system_stats']
            
            if 'cpu_usage' in system:
                cpu = system['cpu_usage']
                print(f"CPU Usage - Mean: {cpu.get('mean', 0):.1f}%, Max: {cpu.get('max', 0):.1f}%")
                
            if 'memory_usage' in system:
                memory = system['memory_usage']
                print(f"Memory Usage - Mean: {memory.get('mean', 0):.1f}%, Max: {memory.get('max', 0):.1f}%")
                
        # Throughput
        if report_data['throughput_stats']:
            print(f"\n📈 THROUGHPUT METRICS")
            print("-" * 20)
            throughput = report_data['throughput_stats']
            print(f"Average Throughput: {throughput.get('mean', 0):.1f} events/sec")
            print(f"Peak Throughput: {throughput.get('max', 0):.1f} events/sec")
            
        # Performance issues
        if report_data['issues']:
            print(f"\n⚠️  PERFORMANCE ISSUES ({len(report_data['issues'])})")
            print("-" * 20)
            for issue in report_data['issues']:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(issue.get('severity', 'info'), "⚪")
                print(f"{severity_icon} {issue['type']}: {issue['description']}")
                
        # Trends
        if report_data['trends']:
            print(f"\n📊 PERFORMANCE TRENDS")
            print("-" * 20)
            trends = report_data['trends']
            for metric_type, trend_info in trends.items():
                trend = trend_info.get('trend', 'unknown')
                trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(trend, "❓")
                print(f"{trend_icon} {metric_type}: {trend}")
                
        print("\n" + "="*60)
        
    def _collect_report_data(self, hours: int) -> Dict[str, Any]:
        """Collect all data needed for the report."""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        # Get metrics in time range
        metrics = self.collector.get_metrics_in_range(start_time, end_time)
        
        # Group metrics by type
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.metric_type].append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'unit': metric.unit,
                'tags': metric.tags or {}
            })
            
        # Calculate statistics for each metric type
        metric_stats = {}
        for metric_type, values in metric_groups.items():
            if values:
                numeric_values = [v['value'] for v in values]
                metric_stats[metric_type] = {
                    'count': len(numeric_values),
                    'mean': statistics.mean(numeric_values),
                    'median': statistics.median(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'std_dev': statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                    'unit': values[0]['unit'],
                    'values': values
                }
                
        # Get current latency stats
        latency_stats = self.collector.get_current_latency_stats()
        
        # Analyze performance trends
        trends = self.analyzer.analyze_performance_trends(hours)
        
        # Identify issues
        issues = self.analyzer.identify_performance_issues()
        
        # Prepare report data
        return {
            'summary': {
                'total_metrics': len(metrics),
                'start_time': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S'),
                'duration_hours': hours
            },
            'latency_stats': latency_stats,
            'system_stats': {
                key: stats for key, stats in metric_stats.items()
                if key in ['cpu_usage', 'memory_usage', 'memory_used']
            },
            'throughput_stats': metric_stats.get('throughput'),
            'all_metrics': metric_stats,
            'trends': trends,
            'issues': issues,
            'raw_metrics': metrics
        }
        
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for the report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Performance Monitor Report</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 1200px;
            margin: 0 auto;
        }
        .header { 
            color: #333; 
            border-bottom: 3px solid #007acc; 
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .section { 
            margin: 30px 0; 
            padding: 20px;
            border-left: 4px solid #007acc;
            background-color: #f9f9f9;
        }
        .metric-card {
            display: inline-block;
            margin: 10px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: white;
            min-width: 200px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
        }
        .metric-label {
            color: #666;
            font-size: 14px;
        }
        .issue {
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 4px solid #ff9800;
        }
        .issue.critical { border-left-color: #f44336; background-color: #ffebee; }
        .issue.warning { border-left-color: #ff9800; background-color: #fff3e0; }
        .issue.info { border-left-color: #2196f3; background-color: #e3f2fd; }
        .trend {
            display: inline-block;
            margin: 5px 10px;
            padding: 5px 10px;
            background-color: #e1f5fe;
            border-radius: 3px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007acc;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Performance Monitor Report</h1>
            <p>Generated on: {generation_time}</p>
            <p>Report Period: {start_time} to {end_time} ({duration} hours)</p>
        </div>
        
        {summary_section}
        {latency_section}
        {system_section}
        {throughput_section}
        {issues_section}
        {trends_section}
        {raw_data_section}
    </div>
</body>
</html>
"""
        
        # Generate sections
        summary_section = self._generate_summary_section(report_data)
        latency_section = self._generate_latency_section(report_data)
        system_section = self._generate_system_section(report_data)
        throughput_section = self._generate_throughput_section(report_data)
        issues_section = self._generate_issues_section(report_data)
        trends_section = self._generate_trends_section(report_data)
        raw_data_section = self._generate_raw_data_section(report_data)
        
        return html_template.format(
            generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            start_time=report_data['summary'].get('start_time', 'N/A'),
            end_time=report_data['summary'].get('end_time', 'N/A'),
            duration=report_data['summary'].get('duration_hours', 0),
            summary_section=summary_section,
            latency_section=latency_section,
            system_section=system_section,
            throughput_section=throughput_section,
            issues_section=issues_section,
            trends_section=trends_section,
            raw_data_section=raw_data_section
        )
        
    def _generate_summary_section(self, report_data: Dict[str, Any]) -> str:
        summary = report_data.get('summary', {})
        return f"""
        <div class="section">
            <h2>📊 Summary</h2>
            <div class="metric-card">
                <div class="metric-value">{summary.get('total_metrics', 0):,}</div>
                <div class="metric-label">Total Metrics</div>
            </div>
        </div>
        """
        
    def _generate_latency_section(self, report_data: Dict[str, Any]) -> str:
        latency = report_data.get('latency_stats', {})
        if not latency:
            return ""
            
        return f"""
        <div class="section">
            <h2>⏱️ Latency Metrics</h2>
            <div class="metric-card">
                <div class="metric-value">{latency.get('mean', 0):.2f}ms</div>
                <div class="metric-label">Mean Latency</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{latency.get('p95', 0):.2f}ms</div>
                <div class="metric-label">95th Percentile</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{latency.get('p99', 0):.2f}ms</div>
                <div class="metric-label">99th Percentile</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{latency.get('max', 0):.2f}ms</div>
                <div class="metric-label">Max Latency</div>
            </div>
        </div>
        """
        
    def _generate_system_section(self, report_data: Dict[str, Any]) -> str:
        system = report_data.get('system_stats', {})
        if not system:
            return ""
            
        cards = []
        if 'cpu_usage' in system:
            cpu = system['cpu_usage']
            cards.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{cpu['mean']:.1f}%</div>
                    <div class="metric-label">Avg CPU Usage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{cpu['max']:.1f}%</div>
                    <div class="metric-label">Max CPU Usage</div>
                </div>
            """)
            
        if 'memory_usage' in system:
            memory = system['memory_usage']
            cards.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{memory['mean']:.1f}%</div>
                    <div class="metric-label">Avg Memory Usage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{memory['max']:.1f}%</div>
                    <div class="metric-label">Max Memory Usage</div>
                </div>
            """)
            
        return f"""
        <div class="section">
            <h2>🖥️ System Metrics</h2>
            {''.join(cards)}
        </div>
        """ if cards else ""
        
    def _generate_throughput_section(self, report_data: Dict[str, Any]) -> str:
        throughput = report_data.get('throughput_stats')
        if not throughput:
            return ""
            
        return f"""
        <div class="section">
            <h2>📈 Throughput Metrics</h2>
            <div class="metric-card">
                <div class="metric-value">{throughput['mean']:.1f}</div>
                <div class="metric-label">Avg Throughput (events/sec)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{throughput['max']:.1f}</div>
                <div class="metric-label">Peak Throughput (events/sec)</div>
            </div>
        </div>
        """
        
    def _generate_issues_section(self, report_data: Dict[str, Any]) -> str:
        issues = report_data.get('issues', [])
        if not issues:
            return """
            <div class="section">
                <h2>⚠️ Performance Issues</h2>
                <p>✅ No performance issues detected!</p>
            </div>
            """
            
        issue_html = []
        for issue in issues:
            severity = issue.get('severity', 'info')
            issue_html.append(f"""
                <div class="issue {severity}">
                    <strong>{issue['type']}</strong>: {issue['description']}<br>
                    <small>Value: {issue.get('value', 'N/A')}, Threshold: {issue.get('threshold', 'N/A')}</small>
                </div>
            """)
            
        return f"""
        <div class="section">
            <h2>⚠️ Performance Issues ({len(issues)})</h2>
            {''.join(issue_html)}
        </div>
        """
        
    def _generate_trends_section(self, report_data: Dict[str, Any]) -> str:
        trends = report_data.get('trends', {})
        if not trends:
            return ""
            
        trend_html = []
        for metric_type, trend_info in trends.items():
            trend = trend_info.get('trend', 'unknown')
            trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(trend, "❓")
            trend_html.append(f"""
                <div class="trend">
                    {trend_icon} <strong>{metric_type}:</strong> {trend}
                </div>
            """)
            
        return f"""
        <div class="section">
            <h2>📊 Performance Trends</h2>
            {''.join(trend_html)}
        </div>
        """
        
    def _generate_raw_data_section(self, report_data: Dict[str, Any]) -> str:
        all_metrics = report_data.get('all_metrics', {})
        if not all_metrics:
            return ""
            
        table_rows = []
        for metric_type, stats in all_metrics.items():
            table_rows.append(f"""
                <tr>
                    <td>{metric_type}</td>
                    <td>{stats['count']:,}</td>
                    <td>{stats['mean']:.2f} {stats['unit']}</td>
                    <td>{stats['min']:.2f} {stats['unit']}</td>
                    <td>{stats['max']:.2f} {stats['unit']}</td>
                    <td>{stats['std_dev']:.2f} {stats['unit']}</td>
                </tr>
            """)
            
        return f"""
        <div class="section">
            <h2>📋 Detailed Metrics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric Type</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Min</th>
                        <th>Max</th>
                        <th>Std Dev</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
        """
        
    def _prepare_json_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for JSON serialization."""
        # Convert metrics to JSON-serializable format
        json_data = report_data.copy()
        
        # Convert raw metrics
        if 'raw_metrics' in json_data:
            json_data['raw_metrics'] = [
                {
                    'timestamp': metric.timestamp,
                    'metric_type': metric.metric_type,
                    'value': metric.value,
                    'unit': metric.unit,
                    'tags': metric.tags
                }
                for metric in json_data['raw_metrics']
            ]
            
        return json_data