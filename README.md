# Linux Performance Profiler

A comprehensive Linux system performance profiler with MCP (Model Context Protocol) remote invocation support, featuring advanced process profiling and flame graph generation.

[中文文档](README_CN.md) | English

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Features

- **CPU Analysis**: Usage rate, frequency, load average, per-core status
- **Memory Analysis**: Virtual memory, swap space, cache usage
- **Disk Analysis**: Partition usage, I/O read/write statistics
- **Network Analysis**: Interface traffic, connection status, error statistics
- **Process Analysis**: Top N CPU/memory consumers, process status statistics
- **🔥 Process Search**: 🆕 Search processes by name or command line keywords
- **🔥 Performance Profiling**: 🆕 Profile processes with perf and generate CPU flame graphs
- **Health Check**: Automatic identification of performance issues and alerts

## Project Structure

```
linux-profiler-tool/
├── src/linux_profiler/
│   ├── __init__.py
│   ├── server.py              # MCP server main entry
│   └── collectors/
│       ├── __init__.py
│       ├── base.py            # Collector base class
│       ├── cpu.py             # CPU metrics collector
│       ├── memory.py          # Memory metrics collector
│       ├── disk.py            # Disk I/O collector
│       ├── network.py         # Network metrics collector
│       ├── process.py         # Process metrics & search collector
│       └── perf.py            # 🆕 Perf profiling & flame graph collector
├── examples/
│   └── profile_workflow.py    # 🆕 Interactive profiling demo
├── pyproject.toml
├── mcp_config.json            # MCP configuration example
├── FEATURES.md                # 🆕 Detailed feature documentation
├── CHANGELOG.md               # 🆕 Version changelog
├── LICENSE                    # Apache 2.0 License
└── README.md
```

## Installation

```bash
# Clone the project
cd linux-profiler-tool

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install dependencies (development mode)
pip install -e .

# Or use uv (faster)
uv pip install -e .

# Verify installation
linux-profiler --help
```

> **Note**: If you encounter `ModuleNotFoundError`, ensure you're in the project directory and have activated the virtual environment. Run `pip install -e .` to install in development mode.

## Usage

### 1. STDIO Mode (Local Invocation)

```bash
# Run directly (default STDIO mode)
python -m linux_profiler.server

# Or use the installed command
linux-profiler
```

### 2. HTTP Mode (Remote Invocation)

Two HTTP transport protocols are supported:

**Streamable HTTP (Recommended, MCP new standard):**
```bash
# Start Streamable HTTP service (default)
linux-profiler --http

# Stateless mode
linux-profiler --http --stateless

# Custom port
linux-profiler --http --port 22222
```

**SSE Transport (Legacy mode):**
```bash
# Use SSE transport
linux-profiler --http --transport sse
```

**Support both transports simultaneously:**
```bash
# Enable both SSE and Streamable HTTP
linux-profiler --http --transport both
```

Available endpoints after startup:

| Transport Type | Endpoint | Description |
|----------------|----------|-------------|
| Streamable HTTP | `/mcp` | MCP main endpoint (GET/POST/DELETE) |
| SSE | `/sse` | SSE connection endpoint |
| SSE | `/sse/messages/` | SSE message endpoint (both mode only) |
| Common | `/health` | Health check |
| Common | `/` | Service information |

### 3. Configure MCP Client

**STDIO Mode Configuration:**
```json
{
  "mcpServers": {
    "linux-profiler": {
      "command": "python",
      "args": ["-m", "linux_profiler.server"],
      "cwd": "/path/to/linux-profiler-tool",
      "env": {
        "PYTHONPATH": "/path/to/linux-profiler-tool/src"
      }
    }
  }
}
```

**Streamable HTTP Mode Configuration (Recommended):**
```json
{
  "mcpServers": {
    "linux-profiler": {
      "url": "http://your-server:22222/mcp",
      "transportType": "streamable-http"
    }
  }
}
```

**SSE Mode Configuration (Legacy):**
```json
{
  "mcpServers": {
    "linux-profiler": {
      "url": "http://your-server:22222/sse"
    }
  }
}
```

## Available MCP Tools

### Core Monitoring Tools

| Tool Name | Description |
|-----------|-------------|
| `get_system_info` | Get basic system information (hostname, OS, kernel version, etc.) |
| `get_cpu_metrics` | Get CPU usage, frequency, and load average |
| `get_memory_metrics` | Get memory and swap space usage |
| `get_disk_metrics` | Get disk partition and I/O statistics |
| `get_network_metrics` | Get network interface traffic and connection status |
| `get_process_metrics` | Get process statistics and top N resource consumers |
| `get_all_metrics` | Get comprehensive report of all performance metrics |
| `get_performance_summary` | Get performance summary and issue alerts |

### 🆕 Advanced Profiling Tools (v1.1.0)

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `search_processes` | Search processes by keyword (name or command line) | `keyword` (required), `case_sensitive` (optional) |
| `profile_process` | Profile process using Linux perf, generate flame graph data | `pid` (required), `duration`, `frequency`, `event` |

> **🔥 New Features**: 
> - **Process Search**: Quickly find processes by name or command patterns
> - **CPU Profiling**: Deep performance analysis with perf tool integration
> - **Flame Graph Generation**: Interactive HTML flame graphs for performance visualization
> 
> See [FEATURES.md](FEATURES.md) for detailed documentation and examples.

## Example Output

### get_performance_summary

```json
{
  "status": "warning",
  "timestamp": "2026-01-14T10:30:00",
  "summary": {
    "cpu_percent": 45.2,
    "load_average_1min": 2.5,
    "memory_percent": 72.3,
    "swap_percent": 15.0
  },
  "issues": [],
  "warnings": [
    "Warning: Memory usage is high (72.3%)"
  ]
}
```

### search_processes

```json
{
  "success": true,
  "keyword": "nginx",
  "case_sensitive": false,
  "matched_count": 3,
  "processes": [
    {
      "pid": 1234,
      "name": "nginx",
      "username": "www-data",
      "cmdline": "nginx: master process /usr/sbin/nginx",
      "cpu_percent": 0.5,
      "memory_percent": 0.3,
      "status": "sleeping"
    },
    {
      "pid": 1235,
      "name": "nginx",
      "username": "www-data",
      "cmdline": "nginx: worker process",
      "cpu_percent": 2.1,
      "memory_percent": 0.4,
      "status": "running"
    }
  ],
  "tip": "Use the PID from this list to profile a specific process with profile_process tool"
}
```

### profile_process

```json
{
  "success": true,
  "pid": 1234,
  "duration": 30,
  "frequency": 99,
  "event": "cpu-clock",
  "timestamp": "2026-01-18 07:42:12",
  "statistics": {
    "total_samples": 287,
    "top_functions": [
      {
        "overhead_percent": 15.2,
        "command": "nginx",
        "function": "ngx_http_process_request"
      },
      {
        "overhead_percent": 8.7,
        "command": "nginx",
        "function": "ngx_event_process_posted"
      }
    ]
  },
  "flame_graph_data": [
    "nginx;[libc] __GI___libc_write;ngx_write_channel 12",
    "nginx;ngx_event_process_posted;ngx_http_request_handler 45"
  ],
  "help": "Use flame_graph_data to generate flame graph visualization"
}
```

### get_system_info

```json
{
  "hostname": "web-server-01",
  "system": "Linux",
  "kernel_version": "5.15.0-91-generic",
  "architecture": "x86_64",
  "python_version": "3.10.12",
  "boot_time": "2026-01-10T08:30:00"
}
```

### get_cpu_metrics

```json
{
  "cpu_percent": 35.5,
  "cpu_count": {
    "physical": 8,
    "logical": 16
  },
  "cpu_freq": {
    "current": 2400.0,
    "min": 800.0,
    "max": 3800.0
  },
  "load_average": {
    "1min": 2.15,
    "5min": 1.89,
    "15min": 1.76
  },
  "per_cpu_percent": [25.0, 38.5, 42.1, 30.0, ...],
  "cpu_times_percent": {
    "user": 25.5,
    "system": 8.0,
    "idle": 66.5,
    "iowait": 0.0
  }
}
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--http` | Enable HTTP mode (default is STDIO mode) |
| `--port, -p` | HTTP listening port (default: 22222) |
| `--host, -H` | HTTP listening address (default: 0.0.0.0) |
| `--transport, -t` | Transport type: `streamable` (default), `sse`, `both` |
| `--stateless` | Streamable HTTP stateless mode |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROFILER_PORT` | HTTP default port | 22222 |
| `PROFILER_HOST` | HTTP default address | 0.0.0.0 |
| `PROFILER_TRANSPORT` | Default transport type | streamable |

## Dependencies

### Core Dependencies
- Python >= 3.10
- mcp >= 1.0.0
- psutil >= 5.9.0
- starlette >= 0.27.0
- uvicorn >= 0.24.0
- pydantic >= 2.0.0

### Additional Requirements for Profiling (profile_process)
- **Linux system** (perf is Linux-specific)
- **perf tool** installed:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install linux-tools-generic linux-tools-$(uname -r)
  
  # RHEL/CentOS
  sudo yum install perf
  
  # Arch Linux
  sudo pacman -S perf
  ```

### Optional: Enable perf for non-root users
```bash
# Temporarily (until reboot)
sudo sysctl -w kernel.perf_event_paranoid=-1

# Permanently
echo "kernel.perf_event_paranoid = -1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Use Cases

### 1. Local Performance Monitoring
Monitor your local machine's performance metrics in real-time through MCP-compatible AI assistants.

### 2. Remote Server Monitoring
Deploy the profiler on remote servers and monitor multiple servers centrally through HTTP endpoints.

### 3. AI-Powered DevOps
Integrate with AI assistants to automate performance analysis, anomaly detection, and troubleshooting recommendations.

### 4. System Health Checks
Set up automated health checks and receive alerts when system resources exceed thresholds.

### 5. 🆕 Process Performance Analysis
Search for resource-intensive processes and generate detailed CPU flame graphs to identify bottlenecks.

**Example Workflow**:
```bash
# 1. Search for processes
search_processes --keyword "python"

# 2. Profile the target process
profile_process --pid 12345 --duration 30

# 3. Generate interactive flame graph
# The tool outputs flame_graph_data that can be visualized with:
# - FlameGraph tools (https://github.com/brendangregg/FlameGraph)
# - speedscope (https://www.speedscope.app/)
# - Or the built-in HTML generator
```

### 6. 🆕 Performance Bottleneck Identification
Quickly identify CPU-intensive functions and optimize hot code paths using flame graph visualization.

**Try the Interactive Demo**:
```bash
python examples/profile_workflow.py
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=linux_profiler
```

### Code Quality

```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
ruff check src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Troubleshooting

For common issues and solutions, please refer to:
- [INSTALL.md](INSTALL.md) - Detailed installation guide
- [FIX_GUIDE.md](FIX_GUIDE.md) - Troubleshooting guide

## Acknowledgments

- Built with [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- Performance metrics powered by [psutil](https://github.com/giampaolo/psutil)
- HTTP server built with [Starlette](https://www.starlette.io/)

---

## License

```
Copyright 2026 Linux Profiler MCP Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

See [LICENSE](LICENSE) for the full license text.

---

**Made with ❤️ for the DevOps and AI community**
