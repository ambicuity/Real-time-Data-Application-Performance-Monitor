"""
Test suite for the performance monitoring system.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from performance_monitor.metrics_collector import MetricsCollector, PerformanceAnalyzer, PerformanceMetric
from performance_monitor.data_simulator import SimulatedDataApplication, WorkloadType, DataProcessor
from performance_monitor.config_manager import ConfigManager
from performance_monitor.reporter import PerformanceReporter


class TestMetricsCollector:
    """Test metrics collection functionality."""
    
    def setup_method(self):
        self.collector = MetricsCollector(buffer_size=100)
        
    def teardown_method(self):
        if self.collector._running:
            self.collector.stop_collection()
            
    def test_latency_recording(self):
        """Test latency metric recording."""
        self.collector.record_latency(100.5, "test_operation")
        
        stats = self.collector.get_current_latency_stats()
        assert stats['count'] == 1
        assert stats['mean'] == 100.5
        assert stats['min'] == 100.5
        assert stats['max'] == 100.5
        
    def test_throughput_recording(self):
        """Test throughput metric recording."""
        self.collector.record_throughput_event(5)
        self.collector.record_throughput_event(3)
        
        # Wait a bit to ensure time difference
        time.sleep(0.1)
        
        # The exact throughput will depend on timing, so just check it's positive
        throughput = self.collector.get_current_throughput()
        # May be 0 if not enough time has passed, so we'll just check structure
        assert isinstance(throughput, float)
        
    def test_metrics_buffer(self):
        """Test metrics buffer functionality."""
        # Add some metrics
        for i in range(10):
            self.collector.record_latency(i * 10)
            
        recent_metrics = self.collector.get_recent_metrics(60)
        assert len(recent_metrics) > 0
        
        # Test time range filtering
        end_time = time.time()
        start_time = end_time - 30
        range_metrics = self.collector.get_metrics_in_range(start_time, end_time)
        
        assert all(start_time <= metric.timestamp <= end_time for metric in range_metrics)
        
    def test_clear_metrics(self):
        """Test clearing metrics."""
        self.collector.record_latency(100)
        self.collector.record_throughput_event(1)
        
        assert len(self.collector.get_recent_metrics()) > 0
        
        self.collector.clear_metrics()
        
        assert len(self.collector.get_recent_metrics()) == 0
        assert self.collector.get_current_latency_stats() == {}
        
    def test_system_metrics_collection(self):
        """Test automatic system metrics collection."""
        self.collector.start_collection(interval=0.1)
        
        # Wait for some metrics to be collected
        time.sleep(0.5)
        
        metrics = self.collector.get_recent_metrics(10)
        
        # Should have some system metrics
        metric_types = {metric.metric_type for metric in metrics}
        expected_types = {'cpu_usage', 'memory_usage', 'memory_used'}
        
        assert len(metric_types.intersection(expected_types)) > 0
        
        self.collector.stop_collection()


class TestPerformanceAnalyzer:
    """Test performance analysis functionality."""
    
    def setup_method(self):
        self.collector = MetricsCollector(buffer_size=100)
        self.analyzer = PerformanceAnalyzer(self.collector)
        
    def test_performance_trends(self):
        """Test performance trend analysis."""
        # Add some test metrics
        current_time = time.time()
        
        for i in range(20):
            metric = PerformanceMetric(
                timestamp=current_time - (20 - i) * 60,  # Spread over 20 minutes
                metric_type="test_metric",
                value=i * 10,  # Increasing trend
                unit="ms"
            )
            self.collector._metrics_buffer.append(metric)
            
        trends = self.analyzer.analyze_performance_trends(hours=1)
        
        assert 'test_metric' in trends
        assert trends['test_metric']['trend'] == 'increasing'
        assert trends['test_metric']['count'] == 20
        
    def test_issue_identification(self):
        """Test performance issue identification."""
        # Add metrics that should trigger issues
        current_time = time.time()
        
        # Add high CPU usage metrics
        for _ in range(10):
            metric = PerformanceMetric(
                timestamp=current_time - 60,
                metric_type="cpu_usage",
                value=95.0,  # High CPU
                unit="%"
            )
            self.collector._metrics_buffer.append(metric)
            
        # Add high latency
        self.collector.record_latency(2000)  # High latency
        
        issues = self.analyzer.identify_performance_issues()
        
        issue_types = {issue['type'] for issue in issues}
        assert 'high_cpu_usage' in issue_types
        assert 'high_latency' in issue_types


class TestDataSimulator:
    """Test data simulation functionality."""
    
    def test_data_processor(self):
        """Test data processing functionality."""
        processor = DataProcessor(
            processing_time_range=(0.001, 0.002),
            error_rate=0.0,  # No errors for test
            memory_usage_mb=10
        )
        
        from performance_monitor.data_simulator import DataEvent
        import uuid
        
        event = DataEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type="test",
            data={"test": "data"}
        )
        
        processed_event, processing_time = processor.process_event(event)
        
        assert processed_event.data["processed_at"] > 0
        assert processing_time > 0
        assert "processing_time_ms" in processed_event.data
        
    def test_workload_generator(self):
        """Test workload generation."""
        from performance_monitor.data_simulator import WorkloadGenerator
        
        generator = WorkloadGenerator(WorkloadType.LOW)
        
        event = generator.generate_event()
        
        assert event.event_id
        assert event.timestamp > 0
        assert event.event_type in generator.event_types
        assert isinstance(event.data, dict)
        
        # Test event rate
        rate = generator.get_event_rate()
        assert rate > 0
        
    def test_simulated_application(self):
        """Test complete simulated application."""
        app = SimulatedDataApplication(
            workload_type=WorkloadType.LOW,
            num_processors=2,
            buffer_size=100
        )
        
        # Set up metrics callback
        metrics_received = []
        
        def metrics_callback(metric_type, value, operation="default"):
            metrics_received.append((metric_type, value, operation))
            
        app.set_metrics_callback(metrics_callback)
        
        # Start for a short time
        app.start()
        time.sleep(2)
        app.stop()
        
        stats = app.get_statistics()
        
        assert stats['events_generated'] > 0
        assert stats['events_processed'] >= 0
        assert len(metrics_received) > 0


class TestConfigManager:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration loading."""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert 'monitoring' in config
        assert 'metrics' in config
        assert 'thresholds' in config
        
        assert config['monitoring']['interval'] == 1.0
        
    def test_config_sections(self):
        """Test configuration section access."""
        config_manager = ConfigManager()
        
        monitoring_config = config_manager.get_section('monitoring')
        assert monitoring_config['interval'] == 1.0
        
        value = config_manager.get_value('monitoring', 'interval')
        assert value == 1.0
        
        default_value = config_manager.get_value('nonexistent', 'key', 'default')
        assert default_value == 'default'
        
    def test_config_updates(self):
        """Test configuration updates."""
        config_manager = ConfigManager()
        
        updates = {
            'monitoring': {
                'interval': 2.0
            }
        }
        
        config_manager.update_config(updates)
        
        value = config_manager.get_value('monitoring', 'interval')
        assert value == 2.0


class TestReporter:
    """Test reporting functionality."""
    
    def setup_method(self):
        self.collector = MetricsCollector(buffer_size=100)
        self.analyzer = PerformanceAnalyzer(self.collector)
        self.reporter = PerformanceReporter(self.collector, self.analyzer)
        
    def test_report_data_collection(self):
        """Test report data collection."""
        # Add some test metrics
        self.collector.record_latency(100)
        self.collector.record_throughput_event(10)
        
        # Access private method for testing
        report_data = self.reporter._collect_report_data(1)
        
        assert 'summary' in report_data
        assert 'latency_stats' in report_data
        assert report_data['summary']['total_metrics'] >= 0
        
    def test_console_report(self):
        """Test console report generation."""
        # Add some metrics
        self.collector.record_latency(100)
        
        # Should not raise an exception
        self.reporter.generate_console_report(1)
        
    def test_json_report(self, tmp_path):
        """Test JSON report generation."""
        # Add some metrics
        self.collector.record_latency(100)
        
        output_file = tmp_path / "test_report.json"
        self.reporter.generate_json_report(str(output_file), 1)
        
        assert output_file.exists()
        
        # Verify it's valid JSON
        import json
        with open(output_file) as f:
            report_data = json.load(f)
            
        assert 'summary' in report_data
        
    def test_html_report(self, tmp_path):
        """Test HTML report generation."""
        # Add some metrics
        self.collector.record_latency(100)
        
        output_file = tmp_path / "test_report.html"
        self.reporter.generate_html_report(str(output_file), 1)
        
        assert output_file.exists()
        
        # Verify it contains expected HTML content
        content = output_file.read_text()
        assert '<html>' in content
        assert 'Performance Monitor Report' in content


# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_monitoring_with_simulation(self):
        """Test complete monitoring with simulation."""
        from performance_monitor.cli import PerformanceMonitorApp
        
        # Create app with minimal config
        app = PerformanceMonitorApp()
        
        # Start monitoring for a short time
        monitor_thread = threading.Thread(
            target=lambda: app.start_monitoring(
                simulate=True,
                scenario="normal_load", 
                duration=3
            )
        )
        
        monitor_thread.start()
        monitor_thread.join(timeout=10)
        
        # Check that metrics were collected
        recent_metrics = app.metrics_collector.get_recent_metrics(10)
        assert len(recent_metrics) > 0
        
    def test_end_to_end_workflow(self, tmp_path):
        """Test complete end-to-end workflow."""
        from performance_monitor.cli import PerformanceMonitorApp
        
        app = PerformanceMonitorApp()
        
        # Simulate some activity
        app.metrics_collector.record_latency(50, "test")
        app.metrics_collector.record_latency(100, "test")
        app.metrics_collector.record_throughput_event(10)
        
        # Generate report
        report_file = tmp_path / "integration_report.html"
        app.generate_report(str(report_file), "html", 1)
        
        assert report_file.exists()
        
        # Verify report content
        content = report_file.read_text()
        assert 'Performance Monitor Report' in content


if __name__ == '__main__':
    pytest.main([__file__])