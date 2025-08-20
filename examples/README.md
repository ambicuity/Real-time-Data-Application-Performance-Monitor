# Performance Monitor Usage Examples

This directory contains practical examples of how to use the Real-time Data Application Performance Monitor.

## Examples

### 1. Basic Example (`basic_example.py`)
Demonstrates basic performance monitoring with default settings.

**Usage:**
```bash
python examples/basic_example.py
```

**What it does:**
- Starts monitoring with normal load simulation
- Runs for 60 seconds
- Generates console and HTML reports
- Shows basic performance metrics

### 2. Stress Test Example (`stress_test_example.py`)
Comprehensive stress testing across multiple scenarios.

**Usage:**
```bash
python examples/stress_test_example.py
```

**What it does:**
- Runs multiple stress test scenarios
- Identifies performance bottlenecks
- Generates comprehensive analysis
- Creates detailed stress test reports

### 3. Custom Monitoring (`custom_monitoring_example.py`)
Shows how to customize monitoring for specific use cases.

**Usage:**
```bash
python examples/custom_monitoring_example.py
```

**What it does:**
- Demonstrates custom configuration
- Shows advanced metric collection
- Implements custom analysis logic
- Creates specialized reports

## Running Examples

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install the package:
```bash
python setup.py develop
```

3. Run any example:
```bash
cd examples/
python basic_example.py
```

## Expected Output

Each example will:
- Display real-time monitoring information
- Show performance metrics and alerts
- Generate HTML reports in the current directory
- Print summary statistics to console

## Customization

You can modify the examples to:
- Change monitoring duration
- Adjust performance thresholds
- Use different simulation scenarios
- Customize report formats
- Add custom metrics

Refer to the main documentation for detailed configuration options.