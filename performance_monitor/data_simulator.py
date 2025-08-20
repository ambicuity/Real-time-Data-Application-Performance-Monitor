"""
Simulated Real-time Data Application

Simulates various types of real-time data processing workloads to test
the performance monitoring system.
"""

import time
import random
import threading
import queue
import json
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import uuid


class WorkloadType(Enum):
    """Types of simulated workloads."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BURSTY = "bursty"
    CUSTOM = "custom"


@dataclass
class DataEvent:
    """Represents a data event in the simulation."""
    event_id: str
    timestamp: float
    event_type: str
    data: Dict
    priority: int = 1
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "data": self.data,
            "priority": self.priority
        }


class WorkloadGenerator:
    """Generates simulated workload events."""
    
    def __init__(self, workload_type: WorkloadType = WorkloadType.MEDIUM):
        self.workload_type = workload_type
        self.event_types = [
            "user_action", "sensor_reading", "transaction", 
            "log_entry", "metric_update", "alert"
        ]
        
    def generate_event(self) -> DataEvent:
        """Generate a single data event."""
        event_type = random.choice(self.event_types)
        
        # Generate realistic data based on event type
        data = self._generate_event_data(event_type)
        
        return DataEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            priority=random.randint(1, 5)
        )
        
    def get_event_rate(self) -> float:
        """Get events per second based on workload type."""
        rates = {
            WorkloadType.LOW: 10,
            WorkloadType.MEDIUM: 100,
            WorkloadType.HIGH: 1000,
            WorkloadType.BURSTY: self._get_bursty_rate(),
        }
        return rates.get(self.workload_type, 100)
        
    def _generate_event_data(self, event_type: str) -> Dict:
        """Generate realistic data for different event types."""
        base_data = {
            "source": f"source_{random.randint(1, 10)}",
            "region": random.choice(["us-east", "us-west", "eu-central", "asia-pacific"])
        }
        
        if event_type == "user_action":
            base_data.update({
                "user_id": f"user_{random.randint(1, 1000)}",
                "action": random.choice(["click", "view", "purchase", "login"]),
                "session_id": f"session_{random.randint(1, 100)}"
            })
        elif event_type == "sensor_reading":
            base_data.update({
                "sensor_id": f"sensor_{random.randint(1, 50)}",
                "value": round(random.uniform(0, 100), 2),
                "unit": random.choice(["celsius", "percent", "psi", "rpm"])
            })
        elif event_type == "transaction":
            base_data.update({
                "transaction_id": f"txn_{random.randint(1, 10000)}",
                "amount": round(random.uniform(1, 1000), 2),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "merchant": f"merchant_{random.randint(1, 100)}"
            })
        elif event_type == "log_entry":
            base_data.update({
                "level": random.choice(["INFO", "WARN", "ERROR", "DEBUG"]),
                "message": "Sample log message for simulation",
                "component": f"service_{random.randint(1, 5)}"
            })
        elif event_type == "metric_update":
            base_data.update({
                "metric_name": random.choice(["cpu_usage", "memory_usage", "disk_io", "network_io"]),
                "value": round(random.uniform(0, 100), 2),
                "host": f"host_{random.randint(1, 20)}"
            })
        elif event_type == "alert":
            base_data.update({
                "alert_id": f"alert_{random.randint(1, 1000)}",
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "description": "Simulated alert condition detected"
            })
            
        return base_data
        
    def _get_bursty_rate(self) -> float:
        """Get bursty event rate that varies over time."""
        # Create bursts every 30 seconds
        cycle_time = time.time() % 30
        if cycle_time < 5:  # 5 seconds of high activity
            return 2000
        elif cycle_time < 10:  # 5 seconds of medium activity
            return 500
        else:  # 20 seconds of low activity
            return 50


class DataProcessor:
    """Simulates data processing with configurable latency."""
    
    def __init__(self, 
                 processing_time_range: tuple = (0.001, 0.01),
                 error_rate: float = 0.01,
                 memory_usage_mb: int = 100):
        self.processing_time_range = processing_time_range
        self.error_rate = error_rate
        self.memory_usage_mb = memory_usage_mb
        self._memory_buffer = []
        
        # Simulate memory usage
        self._allocate_memory()
        
    def process_event(self, event: DataEvent) -> tuple[DataEvent, float]:
        """Process an event and return processed event with processing time."""
        start_time = time.time()
        
        # Simulate processing delay
        processing_time = random.uniform(*self.processing_time_range)
        time.sleep(processing_time)
        
        # Simulate errors
        if random.random() < self.error_rate:
            raise Exception(f"Simulated processing error for event {event.event_id}")
            
        # Add processing metadata
        event.data["processed_at"] = time.time()
        event.data["processing_time_ms"] = processing_time * 1000
        
        actual_processing_time = time.time() - start_time
        return event, actual_processing_time * 1000  # Return in milliseconds
        
    def _allocate_memory(self):
        """Simulate memory usage."""
        # Allocate some memory to simulate realistic memory usage
        memory_size = self.memory_usage_mb * 1024 * 1024 // 8  # rough estimate
        self._memory_buffer = [0] * min(memory_size, 1000000)  # Cap at reasonable size


class SimulatedDataApplication:
    """Main simulated data application."""
    
    def __init__(self, 
                 workload_type: WorkloadType = WorkloadType.MEDIUM,
                 num_processors: int = 4,
                 buffer_size: int = 1000):
        self.workload_type = workload_type
        self.num_processors = num_processors
        self.buffer_size = buffer_size
        
        self.generator = WorkloadGenerator(workload_type)
        self.processors = [DataProcessor() for _ in range(num_processors)]
        
        self.event_queue = queue.Queue(maxsize=buffer_size)
        self.processed_events = queue.Queue()
        
        self._running = False
        self._threads = []
        self._metrics_callback: Optional[Callable] = None
        
        # Statistics
        self.events_generated = 0
        self.events_processed = 0
        self.events_failed = 0
        self.total_processing_time = 0.0
        
    def set_metrics_callback(self, callback: Callable):
        """Set callback for reporting metrics."""
        self._metrics_callback = callback
        
    def start(self):
        """Start the simulated application."""
        if self._running:
            return
            
        self._running = True
        
        # Start event generator thread
        generator_thread = threading.Thread(target=self._generate_events, daemon=True)
        generator_thread.start()
        self._threads.append(generator_thread)
        
        # Start processor threads
        for i, processor in enumerate(self.processors):
            processor_thread = threading.Thread(
                target=self._process_events,
                args=(processor, f"processor_{i}"),
                daemon=True
            )
            processor_thread.start()
            self._threads.append(processor_thread)
            
        print(f"Started simulated data application with {self.num_processors} processors")
        print(f"Workload type: {self.workload_type.value}")
        print(f"Target event rate: {self.generator.get_event_rate()} events/sec")
        
    def stop(self):
        """Stop the simulated application."""
        self._running = False
        for thread in self._threads:
            thread.join(timeout=5.0)
        self._threads.clear()
        
        print("Stopped simulated data application")
        self._print_statistics()
        
    def get_statistics(self) -> Dict[str, any]:
        """Get application statistics."""
        uptime = time.time() if self._running else 0
        avg_processing_time = (
            self.total_processing_time / self.events_processed
            if self.events_processed > 0 else 0
        )
        
        return {
            "events_generated": self.events_generated,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "queue_size": self.event_queue.qsize(),
            "average_processing_time_ms": avg_processing_time,
            "success_rate": (
                (self.events_processed / max(self.events_generated, 1)) * 100
                if self.events_generated > 0 else 0
            ),
            "error_rate": (
                (self.events_failed / max(self.events_processed + self.events_failed, 1)) * 100
                if (self.events_processed + self.events_failed) > 0 else 0
            )
        }
        
    def _generate_events(self):
        """Generate events continuously."""
        while self._running:
            try:
                event = self.generator.generate_event()
                self.event_queue.put(event, timeout=1.0)
                self.events_generated += 1
                
                # Report throughput to metrics collector
                if self._metrics_callback:
                    self._metrics_callback('throughput_event', 1)
                    
            except queue.Full:
                print("Event queue full, dropping event")
            except Exception as e:
                print(f"Error generating event: {e}")
                
            # Sleep based on target event rate
            target_rate = self.generator.get_event_rate()
            if target_rate > 0:
                time.sleep(1.0 / target_rate)
                
    def _process_events(self, processor: DataProcessor, processor_name: str):
        """Process events from the queue."""
        while self._running:
            try:
                event = self.event_queue.get(timeout=1.0)
                
                try:
                    processed_event, processing_time_ms = processor.process_event(event)
                    self.processed_events.put(processed_event)
                    self.events_processed += 1
                    self.total_processing_time += processing_time_ms
                    
                    # Report latency to metrics collector
                    if self._metrics_callback:
                        self._metrics_callback('latency', processing_time_ms, processor_name)
                        
                except Exception as e:
                    self.events_failed += 1
                    print(f"Processing error in {processor_name}: {e}")
                    
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processor {processor_name}: {e}")
                
    def _print_statistics(self):
        """Print application statistics."""
        stats = self.get_statistics()
        print("\n=== Simulation Statistics ===")
        print(f"Events Generated: {stats['events_generated']}")
        print(f"Events Processed: {stats['events_processed']}")
        print(f"Events Failed: {stats['events_failed']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Error Rate: {stats['error_rate']:.1f}%")
        print(f"Average Processing Time: {stats['average_processing_time_ms']:.2f}ms")
        print(f"Final Queue Size: {stats['queue_size']}")


class WorkloadScenario:
    """Predefined workload scenarios for testing."""
    
    @staticmethod
    def get_scenario_config(scenario_name: str) -> Dict:
        """Get configuration for a named scenario."""
        scenarios = {
            "normal_load": {
                "workload_type": WorkloadType.MEDIUM,
                "num_processors": 4,
                "buffer_size": 1000,
                "duration": 300
            },
            "high_load": {
                "workload_type": WorkloadType.HIGH,
                "num_processors": 4,
                "buffer_size": 1000,
                "duration": 300
            },
            "overload": {
                "workload_type": WorkloadType.HIGH,
                "num_processors": 2,
                "buffer_size": 500,
                "duration": 300
            },
            "bursty_traffic": {
                "workload_type": WorkloadType.BURSTY,
                "num_processors": 6,
                "buffer_size": 2000,
                "duration": 600
            },
            "memory_intensive": {
                "workload_type": WorkloadType.MEDIUM,
                "num_processors": 8,
                "buffer_size": 5000,
                "duration": 300
            }
        }
        
        return scenarios.get(scenario_name, scenarios["normal_load"])
        
    @staticmethod
    def list_scenarios() -> List[str]:
        """List available scenario names."""
        return ["normal_load", "high_load", "overload", "bursty_traffic", "memory_intensive"]