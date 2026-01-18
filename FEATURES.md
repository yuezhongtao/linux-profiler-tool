# New Features

## Process Search and Profiling

### 1. Search Processes by Keyword

**Tool**: `search_processes`

Search for processes by keyword (name or command line) and get a list of matching processes.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keyword` | string | Yes | Keyword to search for in process names or command lines |
| `case_sensitive` | boolean | No | Whether to perform case-sensitive search (default: false) |

#### Example Usage

```json
{
  "tool": "search_processes",
  "arguments": {
    "keyword": "python",
    "case_sensitive": false
  }
}
```

#### Example Response

```json
{
  "success": true,
  "keyword": "python",
  "case_sensitive": false,
  "matched_count": 5,
  "processes": [
    {
      "pid": 12345,
      "name": "python3",
      "username": "user",
      "cmdline": "python3 /path/to/script.py --option value",
      "cpu_percent": 15.5,
      "memory_percent": 2.3,
      "status": "running"
    },
    {
      "pid": 12346,
      "name": "python",
      "username": "user",
      "cmdline": "python manage.py runserver",
      "cpu_percent": 8.2,
      "memory_percent": 1.8,
      "status": "sleeping"
    }
  ],
  "tip": "Use the PID from this list to profile a specific process with profile_process tool"
}
```

---

### 2. Profile Process with Perf

**Tool**: `profile_process`

Collect performance profile data for a specific process using `perf` tool. The output includes data suitable for generating flame graphs.

#### Prerequisites

The `perf` tool must be installed on the system:

```bash
# Ubuntu/Debian
sudo apt-get install linux-tools-generic linux-tools-$(uname -r)

# RHEL/CentOS/Fedora
sudo yum install perf

# Arch Linux
sudo pacman -S perf
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pid` | integer | Yes | - | Process ID to profile |
| `duration` | integer | No | 10 | Duration in seconds to collect data (1-300) |
| `frequency` | integer | No | 99 | Sampling frequency in Hz (1-10000) |
| `event` | string | No | cpu-clock | Perf event to record (cpu-clock, cycles, instructions, cache-misses) |

#### Example Usage

```json
{
  "tool": "profile_process",
  "arguments": {
    "pid": 12345,
    "duration": 30,
    "frequency": 99,
    "event": "cpu-clock"
  }
}
```

#### Example Response

```json
{
  "success": true,
  "pid": 12345,
  "duration": 30,
  "frequency": 99,
  "event": "cpu-clock",
  "timestamp": "2026-01-17 22:30:15",
  "statistics": {
    "total_samples": 15,
    "top_functions": [
      {
        "overhead_percent": 45.2,
        "command": "python3",
        "function": "do_work"
      },
      {
        "overhead_percent": 23.1,
        "command": "python3",
        "function": "process_data"
      },
      {
        "overhead_percent": 12.5,
        "command": "python3",
        "function": "__pthread_cond_wait"
      }
    ]
  },
  "flame_graph_data": [
    {
      "command": "python3",
      "pid": 12345,
      "timestamp": "123456.789",
      "stack": [
        "do_work",
        "process_data",
        "main"
      ]
    }
  ],
  "raw_stack_traces": "...",
  "report_summary": "...",
  "help": "Use flame_graph_data to generate flame graph visualization"
}
```

---

## Workflow: Search and Profile

1. **Search for the target process**:

```json
{
  "tool": "search_processes",
  "arguments": {
    "keyword": "myapp"
  }
}
```

2. **Get the PID from search results**:

```json
{
  "matched_count": 2,
  "processes": [
    {
      "pid": 12345,
      "name": "myapp",
      ...
    }
  ]
}
```

3. **Profile the process**:

```json
{
  "tool": "profile_process",
  "arguments": {
    "pid": 12345,
    "duration": 30
  }
}
```

4. **Generate flame graph** (optional):

Use the `flame_graph_data` from the response with flame graph tools like:
- [FlameGraph](https://github.com/brendangregg/FlameGraph)
- [speedscope](https://www.speedscope.app/)
- [d3-flame-graph](https://github.com/spiermar/d3-flame-graph)

---

## Troubleshooting

### Permission Denied

If you get permission errors when profiling:

```bash
# Option 1: Run as root (not recommended for production)
sudo linux-profiler --http

# Option 2: Enable kernel.perf_event_paranoid
sudo sysctl -w kernel.perf_event_paranoid=-1

# Option 3: Add capability to perf binary
sudo setcap cap_sys_admin=ep /usr/bin/perf
```

### Perf Tool Not Available

If `perf` is not installed:

```json
{
  "success": false,
  "error": "perf tool is not available on this system",
  "help": "Install perf with: apt-get install linux-tools-generic (Ubuntu/Debian) or yum install perf (RHEL/CentOS)"
}
```

### Process Not Found

If the process doesn't exist:

```json
{
  "success": false,
  "error": "Process with PID 12345 does not exist"
}
```

---

## Performance Considerations

- **CPU Impact**: Profiling with `perf` has minimal overhead (typically <5%)
- **Duration**: Longer durations provide more accurate data but consume more resources
- **Frequency**: Higher frequencies provide more detail but increase overhead
- **Disk Space**: Perf data files are temporary and automatically cleaned up

---

## Integration Examples

### With AI Assistants

```
User: "Find all python processes and profile the one using most CPU"

AI Assistant:
1. Calls search_processes with keyword="python"
2. Analyzes CPU usage from results
3. Calls profile_process with the highest CPU process PID
4. Presents performance analysis and flame graph data
```

### With Monitoring Systems

```python
import requests

# Search for process
response = requests.post(
    "http://server:22222/mcp",
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_processes",
            "arguments": {"keyword": "myapp"}
        },
        "id": 1
    }
)

# Profile the process
pid = response.json()["result"]["processes"][0]["pid"]
profile_response = requests.post(
    "http://server:22222/mcp",
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "profile_process",
            "arguments": {"pid": pid, "duration": 30}
        },
        "id": 2
    }
)
```

---

## Supported Perf Events

| Event | Description | Use Case |
|-------|-------------|----------|
| `cpu-clock` | CPU clock cycles | General CPU profiling |
| `cycles` | Hardware CPU cycles | CPU-bound workloads |
| `instructions` | CPU instructions | Instruction-level analysis |
| `cache-misses` | L1/L2 cache misses | Memory access optimization |

---

## Flame Graph Generation

The `flame_graph_data` output is structured for easy flame graph generation:

```python
def generate_flame_graph(flame_graph_data):
    """Convert perf data to flame graph format."""
    lines = []
    for sample in flame_graph_data:
        if sample['stack']:
            stack_trace = ';'.join(sample['stack'])
            lines.append(f"{sample['command']};{stack_trace} 1")
    return '\\n'.join(lines)
```

Then use with [FlameGraph](https://github.com/brendangregg/FlameGraph):

```bash
cat flame_data.txt | flamegraph.pl > flame.svg
```
