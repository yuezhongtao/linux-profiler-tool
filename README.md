## Linux性能分析工具

一个支持 MCP (Model Context Protocol) 协议远程调用的 Linux 性能分析工具。

### 功能特性

- **CPU 分析**: 使用率、频率、负载均衡、各核心状态
- **内存分析**: 虚拟内存、交换分区、缓存使用
- **磁盘分析**: 分区使用率、I/O 读写统计
- **网络分析**: 接口流量、连接状态、错误统计
- **进程分析**: Top N CPU/内存消耗进程、进程状态统计
- **健康检查**: 自动识别性能问题和告警

### 项目结构

```
linux-profiler-tool/
├── src/linux_profiler/
│   ├── __init__.py
│   ├── server.py              # MCP 服务器主入口
│   └── collectors/
│       ├── __init__.py
│       ├── base.py            # 采集器基类
│       ├── cpu.py             # CPU 指标采集
│       ├── memory.py          # 内存指标采集
│       ├── disk.py            # 磁盘 I/O 采集
│       ├── network.py         # 网络指标采集
│       └── process.py         # 进程指标采集
├── pyproject.toml
├── mcp_config.json            # MCP 配置示例
└── README.md
```

### 安装

```bash
# 克隆项目
cd linux-profiler-tool

# 安装依赖
pip install -e .

# 或使用 uv
uv pip install -e .
```

### 使用方式

#### 1. 作为 MCP Server 运行

```bash
# 直接运行
python -m linux_profiler.server

# 或使用安装后的命令
linux-profiler
```

#### 2. 配置 MCP 客户端

将以下配置添加到你的 MCP 客户端配置文件中：

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

### 可用的 MCP Tools

| 工具名称 | 描述 |
|---------|------|
| `get_system_info` | 获取系统基本信息（主机名、OS、内核版本等） |
| `get_cpu_metrics` | 获取 CPU 使用率、频率、负载均衡 |
| `get_memory_metrics` | 获取内存和交换分区使用情况 |
| `get_disk_metrics` | 获取磁盘分区和 I/O 统计 |
| `get_network_metrics` | 获取网络接口流量和连接状态 |
| `get_process_metrics` | 获取进程统计和 Top N 资源消耗者 |
| `get_all_metrics` | 获取所有性能指标的综合报告 |
| `get_performance_summary` | 获取性能摘要和问题告警 |

### 示例输出

#### get_performance_summary

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

### 依赖

- Python >= 3.10
- mcp >= 1.0.0
- psutil >= 5.9.0
- pydantic >= 2.0.0
