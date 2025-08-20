"""
Command Line Interface for Real-time Performance Monitor

Provides CLI commands for monitoring, simulation, and reporting.
"""

import click
import time
import yaml
import os
import sys
from typing import Dict, Optional
import threading
import signal

from .metrics_collector import MetricsCollector, PerformanceAnalyzer
from .data_simulator import SimulatedDataApplication, WorkloadType, WorkloadScenario
from .reporter import PerformanceReporter
from .config_manager import ConfigManager


class PerformanceMonitorApp:
    """Main application controller."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        self.metrics_collector = MetricsCollector(
            buffer_size=self.config.get('metrics', {}).get('buffer_size', 10000)
        )
        self.analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.reporter = PerformanceReporter(self.metrics_collector, self.analyzer)
        
        self.simulator: Optional[SimulatedDataApplication] = None
        self._running = False
        self._monitor_thread = None
        
    def start_monitoring(self, 
                        simulate: bool = True,
                        scenario: str = "normal_load",
                        duration: Optional[int] = None):
        """Start performance monitoring."""
        if self._running:
            click.echo("Monitoring is already running.")
            return
            
        self._running = True
        
        # Start metrics collection
        collection_interval = self.config.get('monitoring', {}).get('interval', 1.0)
        self.metrics_collector.start_collection(collection_interval)
        
        click.echo(f"Started performance monitoring (interval: {collection_interval}s)")
        
        # Start simulation if requested
        if simulate:
            self._start_simulation(scenario)
            
        # Start monitoring thread for periodic analysis
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if duration:
            click.echo(f"Monitoring for {duration} seconds...")
            time.sleep(duration)
            self.stop_monitoring()
        else:
            click.echo("Monitoring started. Press Ctrl+C to stop.")
            try:
                # Keep main thread alive
                while self._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_monitoring()
                
    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self._running:
            return
            
        click.echo("Stopping performance monitoring...")
        self._running = False
        
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
            
        self.metrics_collector.stop_collection()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            
        click.echo("Performance monitoring stopped.")
        
    def generate_report(self, 
                       output_path: str = "performance_report.html",
                       format: str = "html",
                       hours: int = 1):
        """Generate performance report."""
        click.echo(f"Generating {format} report...")
        
        if format == "html":
            self.reporter.generate_html_report(output_path, hours)
        elif format == "json":
            self.reporter.generate_json_report(output_path, hours)
        else:
            click.echo(f"Unsupported format: {format}")
            return
            
        click.echo(f"Report generated: {output_path}")
        
    def run_simulation(self, 
                      scenario: str = "normal_load",
                      duration: int = 300,
                      workload_type: Optional[str] = None):
        """Run simulation without monitoring."""
        click.echo(f"Starting simulation: {scenario}")
        
        if workload_type:
            try:
                wt = WorkloadType(workload_type)
            except ValueError:
                click.echo(f"Invalid workload type: {workload_type}")
                return
        else:
            scenario_config = WorkloadScenario.get_scenario_config(scenario)
            wt = scenario_config['workload_type']
            
        # Create and start simulation
        config = WorkloadScenario.get_scenario_config(scenario)
        simulator = SimulatedDataApplication(
            workload_type=wt,
            num_processors=config['num_processors'],
            buffer_size=config['buffer_size']
        )
        
        simulator.start()
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            click.echo("Simulation interrupted.")
        finally:
            simulator.stop()
            
    def _start_simulation(self, scenario: str):
        """Start simulation with monitoring."""
        click.echo(f"Starting simulation: {scenario}")
        
        config = WorkloadScenario.get_scenario_config(scenario)
        self.simulator = SimulatedDataApplication(
            workload_type=config['workload_type'],
            num_processors=config['num_processors'],
            buffer_size=config['buffer_size']
        )
        
        # Set up metrics callback
        def metrics_callback(metric_type: str, value: float, operation: str = "default"):
            if metric_type == 'latency':
                self.metrics_collector.record_latency(value, operation)
            elif metric_type == 'throughput_event':
                self.metrics_collector.record_throughput_event(int(value))
                
        self.simulator.set_metrics_callback(metrics_callback)
        self.simulator.start()
        
    def _monitoring_loop(self):
        """Background monitoring loop for analysis and alerts."""
        analysis_interval = self.config.get('monitoring', {}).get('analysis_interval', 60)
        
        while self._running:
            try:
                time.sleep(analysis_interval)
                
                # Analyze performance and check for issues
                issues = self.analyzer.identify_performance_issues()
                
                if issues:
                    self._handle_performance_issues(issues)
                    
                # Print periodic status
                self._print_status()
                
            except Exception as e:
                click.echo(f"Error in monitoring loop: {e}")
                
    def _handle_performance_issues(self, issues):
        """Handle identified performance issues."""
        click.echo(f"\n⚠️  Performance Issues Detected ({len(issues)} issues):")
        
        for issue in issues:
            severity_icon = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵"
            }.get(issue.get('severity', 'info'), "⚪")
            
            click.echo(f"  {severity_icon} {issue['type']}: {issue['description']}")
            
    def _print_status(self):
        """Print current status."""
        latency_stats = self.metrics_collector.get_current_latency_stats()
        throughput = self.metrics_collector.get_current_throughput()
        
        if latency_stats or throughput > 0:
            click.echo(f"\n📊 Status Update:")
            
            if latency_stats:
                click.echo(f"  Latency - Mean: {latency_stats.get('mean', 0):.1f}ms, "
                          f"P95: {latency_stats.get('p95', 0):.1f}ms, "
                          f"P99: {latency_stats.get('p99', 0):.1f}ms")
                          
            if throughput > 0:
                click.echo(f"  Throughput: {throughput:.1f} events/sec")
                
            if self.simulator:
                stats = self.simulator.get_statistics()
                click.echo(f"  Processed: {stats['events_processed']} events, "
                          f"Success: {stats['success_rate']:.1f}%, "
                          f"Queue: {stats['queue_size']}")
                          
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        click.echo(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop_monitoring()
        sys.exit(0)


# CLI Commands
@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Real-time Data Application Performance Monitor."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--simulate/--no-simulate', default=True, 
              help='Start simulation along with monitoring')
@click.option('--scenario', '-s', default='normal_load',
              type=click.Choice(WorkloadScenario.list_scenarios()),
              help='Simulation scenario')
@click.option('--duration', '-d', type=int,
              help='Monitoring duration in seconds')
@click.pass_context
def start(ctx, config, simulate, scenario, duration):
    """Start performance monitoring."""
    config_path = config or ctx.obj.get('config')
    app = PerformanceMonitorApp(config_path)
    app.start_monitoring(simulate, scenario, duration)


@cli.command()
@click.option('--output', '-o', default='performance_report.html',
              help='Output file path')
@click.option('--format', '-f', default='html',
              type=click.Choice(['html', 'json']),
              help='Report format')
@click.option('--hours', '-h', default=1, type=int,
              help='Hours of data to include')
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def report(ctx, output, format, hours, config):
    """Generate performance report."""
    config_path = config or ctx.obj.get('config')
    app = PerformanceMonitorApp(config_path)
    app.generate_report(output, format, hours)


@cli.command()
@click.option('--scenario', '-s', default='normal_load',
              type=click.Choice(WorkloadScenario.list_scenarios()),
              help='Simulation scenario')
@click.option('--duration', '-d', default=300, type=int,
              help='Simulation duration in seconds')
@click.option('--workload', '-w',
              type=click.Choice(['low', 'medium', 'high', 'bursty']),
              help='Override workload type')
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def simulate(ctx, scenario, duration, workload, config):
    """Run simulation without monitoring."""
    config_path = config or ctx.obj.get('config')
    app = PerformanceMonitorApp(config_path)
    app.run_simulation(scenario, duration, workload)


@cli.command()
def scenarios():
    """List available simulation scenarios."""
    click.echo("Available simulation scenarios:")
    for scenario in WorkloadScenario.list_scenarios():
        config = WorkloadScenario.get_scenario_config(scenario)
        click.echo(f"  {scenario}:")
        click.echo(f"    Workload: {config['workload_type'].value}")
        click.echo(f"    Processors: {config['num_processors']}")
        click.echo(f"    Buffer Size: {config['buffer_size']}")
        click.echo(f"    Duration: {config['duration']}s")
        click.echo()


@cli.command()
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def config_info(ctx, config):
    """Show current configuration."""
    config_path = config or ctx.obj.get('config')
    config_manager = ConfigManager(config_path)
    current_config = config_manager.get_config()
    
    click.echo("Current Configuration:")
    click.echo(yaml.dump(current_config, default_flow_style=False))


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()