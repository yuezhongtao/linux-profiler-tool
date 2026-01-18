# Linux Performance Profiler

A Linux system performance profiler with MCP (Model Context Protocol) remote invocation support.

[中文文档](README.md) | English

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

## ✨ Features

- **CPU Analysis**: Usage rate, frequency, load average, per-core status
- **Memory Analysis**: Virtual memory, swap space, cache usage
- **Disk Analysis**: Partition usage, I/O read/write statistics
- **Network Analysis**: Interface traffic, connection status, error statistics
- **Process Analysis**: Top N CPU/memory consumers, process status statistics
- **Health Check**: Automatic identification of performance issues and alerts

## 📁 Project Structure

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
│       └── process.py         # Process metrics collector
├── pyproject.toml
├── mcp_config.json            # MCP configuration example
├── LICENSE                    # Apache 2.0 License
└── README.md
```

## 🚀 Installation

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

> **Note**: If you encounter `ModuleNotFoundError: No module named 'linux_profiler'`, please refer to [FIX_GUIDE.md](FIX_GUIDE.md) for troubleshooting.

## 💡 Usage

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

## 🔧 Available MCP Tools

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

## 📊 Example Output

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

## ⚙️ Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--http` | Enable HTTP mode (default is STDIO mode) |
| `--port, -p` | HTTP listening port (default: 22222) |
| `--host, -H` | HTTP listening address (default: 0.0.0.0) |
| `--transport, -t` | Transport type: `streamable` (default), `sse`, `both` |
| `--stateless` | Streamable HTTP stateless mode |

## 🌍 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROFILER_PORT` | HTTP default port | 22222 |
| `PROFILER_HOST` | HTTP default address | 0.0.0.0 |
| `PROFILER_TRANSPORT` | Default transport type | streamable |

## 📦 Dependencies

- Python >= 3.10
- mcp >= 1.0.0
- psutil >= 5.9.0
- starlette >= 0.27.0
- uvicorn >= 0.24.0
- pydantic >= 2.0.0

## 🔍 Use Cases

### 1. Local Performance Monitoring
Monitor your local machine's performance metrics in real-time through MCP-compatible AI assistants.

### 2. Remote Server Monitoring
Deploy the profiler on remote servers and monitor multiple servers centrally through HTTP endpoints.

### 3. AI-Powered DevOps
Integrate with AI assistants to automate performance analysis, anomaly detection, and troubleshooting recommendations.

### 4. System Health Checks
Set up automated health checks and receive alerts when system resources exceed thresholds.

## 🛠️ Development

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

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Troubleshooting

For common issues and solutions, please refer to:
- [INSTALL.md](INSTALL.md) - Detailed installation guide
- [FIX_GUIDE.md](FIX_GUIDE.md) - Troubleshooting guide

## 🌟 Acknowledgments

- Built with [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- Performance metrics powered by [psutil](https://github.com/giampaolo/psutil)
- HTTP server built with [Starlette](https://www.starlette.io/)

---

## 📜 License

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
