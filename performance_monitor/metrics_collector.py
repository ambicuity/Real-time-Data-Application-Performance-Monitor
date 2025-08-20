"""
Performance Metrics Collection Module

Collects real-time performance metrics including latency, throughput, 
CPU usage, and memory consumption.
"""

import time
import threading
import psutil
import statistics
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PerformanceMetric:
    """Container for a single performance metric."""
    timestamp: float
    metric_type: str
    value: float
    unit: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class MetricsCollector:
    """Collects various performance metrics in real-time."""
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self._metrics_buffer = deque(maxlen=buffer_size)
        self._running = False
        self._collection_thread = None
        self._lock = threading.Lock()
        
        # Metric-specific buffers for efficient calculations
        self._latency_buffer = deque(maxlen=1000)
        self._throughput_counter = 0
        self._last_throughput_time = time.time()
        
    def start_collection(self, interval: float = 1.0):
        """Start automatic metric collection."""
        if self._running:
            return
            
        self._running = True
        self._collection_thread = threading.Thread(
            target=self._collect_system_metrics,
            args=(interval,),
            daemon=True
        )
        self._collection_thread.start()
        
    def stop_collection(self):
        """Stop automatic metric collection."""
        self._running = False
        if self._collection_thread:
            self._collection_thread.join()
            
    def record_latency(self, latency_ms: float, operation: str = "default"):
        """Record a latency measurement."""
        timestamp = time.time()
        
        with self._lock:
            self._latency_buffer.append(latency_ms)
            
            metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type="latency",
                value=latency_ms,
                unit="ms",
                tags={"operation": operation}
            )
            self._metrics_buffer.append(metric)
            
    def record_throughput_event(self, count: int = 1):
        """Record throughput events."""
        with self._lock:
            self._throughput_counter += count
            
    def get_current_latency_stats(self) -> Dict[str, float]:
        """Get current latency statistics."""
        with self._lock:
            if not self._latency_buffer:
                return {}
                
            latencies = list(self._latency_buffer)
            
        return {
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": self._percentile(latencies, 95),
            "p99": self._percentile(latencies, 99),
            "count": len(latencies)
        }
        
    def get_current_throughput(self) -> float:
        """Get current throughput (events per second)."""
        current_time = time.time()
        with self._lock:
            time_diff = current_time - self._last_throughput_time
            if time_diff >= 1.0:  # Calculate over 1-second windows
                throughput = self._throughput_counter / time_diff
                self._throughput_counter = 0
                self._last_throughput_time = current_time
                return throughput
            return 0.0
            
    def get_metrics_in_range(self, start_time: float, end_time: float) -> List[PerformanceMetric]:
        """Get metrics within a time range."""
        with self._lock:
            return [
                metric for metric in self._metrics_buffer
                if start_time <= metric.timestamp <= end_time
            ]
            
    def get_recent_metrics(self, seconds: int = 60) -> List[PerformanceMetric]:
        """Get metrics from the last N seconds."""
        end_time = time.time()
        start_time = end_time - seconds
        return self.get_metrics_in_range(start_time, end_time)
        
    def clear_metrics(self):
        """Clear all collected metrics."""
        with self._lock:
            self._metrics_buffer.clear()
            self._latency_buffer.clear()
            self._throughput_counter = 0
            self._last_throughput_time = time.time()
            
    def _collect_system_metrics(self, interval: float):
        """Background thread for collecting system metrics."""
        while self._running:
            try:
                timestamp = time.time()
                
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_metric = PerformanceMetric(
                    timestamp=timestamp,
                    metric_type="cpu_usage",
                    value=cpu_percent,
                    unit="%"
                )
                
                # Memory metrics
                memory = psutil.virtual_memory()
                memory_metric = PerformanceMetric(
                    timestamp=timestamp,
                    metric_type="memory_usage",
                    value=memory.percent,
                    unit="%"
                )
                
                memory_used_metric = PerformanceMetric(
                    timestamp=timestamp,
                    metric_type="memory_used",
                    value=memory.used / (1024 * 1024),  # MB
                    unit="MB"
                )
                
                # Throughput metric
                throughput = self.get_current_throughput()
                if throughput > 0:
                    throughput_metric = PerformanceMetric(
                        timestamp=timestamp,
                        metric_type="throughput",
                        value=throughput,
                        unit="events/sec"
                    )
                    
                    with self._lock:
                        self._metrics_buffer.append(throughput_metric)
                
                with self._lock:
                    self._metrics_buffer.extend([cpu_metric, memory_metric, memory_used_metric])
                    
            except Exception as e:
                # Log error but continue collection
                print(f"Error collecting system metrics: {e}")
                
            time.sleep(interval)
            
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset."""
        if not data:
            return 0.0
            
        sorted_data = sorted(data)
        n = len(sorted_data)
        index = (percentile / 100.0) * (n - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class PerformanceAnalyzer:
    """Analyzes collected performance metrics to identify issues and trends."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        
    def analyze_performance_trends(self, hours: int = 1) -> Dict[str, any]:
        """Analyze performance trends over time."""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        metrics = self.collector.get_metrics_in_range(start_time, end_time)
        
        # Group metrics by type
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.metric_type].append(metric.value)
            
        analysis = {}
        
        for metric_type, values in metric_groups.items():
            if values:
                analysis[metric_type] = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "trend": self._calculate_trend(values)
                }
                
        return analysis
        
    def identify_performance_issues(self, thresholds: Dict[str, float] = None) -> List[Dict[str, any]]:
        """Identify potential performance issues."""
        if thresholds is None:
            thresholds = {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "latency": 1000.0,  # ms
                "min_throughput": 100.0  # events/sec
            }
            
        issues = []
        recent_metrics = self.collector.get_recent_metrics(300)  # Last 5 minutes
        
        # Group metrics by type
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.metric_type].append(metric.value)
            
        # Check CPU usage
        if "cpu_usage" in metric_groups:
            cpu_values = metric_groups["cpu_usage"]
            avg_cpu = statistics.mean(cpu_values)
            if avg_cpu > thresholds["cpu_usage"]:
                issues.append({
                    "type": "high_cpu_usage",
                    "severity": "warning" if avg_cpu < 90 else "critical",
                    "value": avg_cpu,
                    "threshold": thresholds["cpu_usage"],
                    "description": f"Average CPU usage ({avg_cpu:.1f}%) exceeds threshold"
                })
                
        # Check memory usage
        if "memory_usage" in metric_groups:
            memory_values = metric_groups["memory_usage"]
            avg_memory = statistics.mean(memory_values)
            if avg_memory > thresholds["memory_usage"]:
                issues.append({
                    "type": "high_memory_usage",
                    "severity": "warning" if avg_memory < 95 else "critical",
                    "value": avg_memory,
                    "threshold": thresholds["memory_usage"],
                    "description": f"Average memory usage ({avg_memory:.1f}%) exceeds threshold"
                })
                
        # Check latency
        latency_stats = self.collector.get_current_latency_stats()
        if latency_stats and latency_stats.get("p95", 0) > thresholds["latency"]:
            issues.append({
                "type": "high_latency",
                "severity": "warning",
                "value": latency_stats["p95"],
                "threshold": thresholds["latency"],
                "description": f"95th percentile latency ({latency_stats['p95']:.1f}ms) exceeds threshold"
            })
            
        # Check throughput
        if "throughput" in metric_groups:
            throughput_values = metric_groups["throughput"]
            if throughput_values:
                avg_throughput = statistics.mean(throughput_values)
                if avg_throughput < thresholds["min_throughput"]:
                    issues.append({
                        "type": "low_throughput",
                        "severity": "warning",
                        "value": avg_throughput,
                        "threshold": thresholds["min_throughput"],
                        "description": f"Average throughput ({avg_throughput:.1f} events/sec) below threshold"
                    })
                    
        return issues
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction (increasing, decreasing, stable)."""
        if len(values) < 2:
            return "unknown"
            
        # Simple trend calculation using first and last quarters
        quarter_size = len(values) // 4
        if quarter_size < 1:
            return "stable"
            
        first_quarter_avg = statistics.mean(values[:quarter_size])
        last_quarter_avg = statistics.mean(values[-quarter_size:])
        
        change_percent = ((last_quarter_avg - first_quarter_avg) / first_quarter_avg) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"