# Linux性能分析工具

一个支持 MCP (Model Context Protocol) 协议远程调用的 Linux 性能分析工具，具备进程搜索和火焰图生成功能。

中文 | [English](README.md)

## 开源许可

本项目采用 [Apache License 2.0](LICENSE) 开源许可证。

### 功能特性

- **CPU 分析**: 使用率、频率、负载均衡、各核心状态
- **内存分析**: 虚拟内存、交换分区、缓存使用
- **磁盘分析**: 分区使用率、I/O 读写统计
- **网络分析**: 接口流量、连接状态、错误统计
- **进程分析**: Top N CPU/内存消耗进程、进程状态统计
- **🔥 进程搜索**: 🆕 通过名称或命令行关键字搜索进程
- **🔥 性能剖析**: 🆕 使用 perf 工具分析进程并生成 CPU 火焰图
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

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖（开发模式）
pip install -e .

# 或使用 uv（更快）
uv pip install -e .

# 验证安装
linux-profiler --help
```

> **注意**: 如果遇到 `ModuleNotFoundError` 错误，请确保您在项目目录中并已激活虚拟环境。运行 `pip install -e .` 以开发模式安装。

### 使用方式

#### 1. STDIO 模式（本地调用）

```bash
# 直接运行（默认 STDIO 模式）
python -m linux_profiler.server

# 或使用安装后的命令
linux-profiler
```

#### 2. HTTP 模式（远程调用）

支持两种 HTTP 传输协议：

**Streamable HTTP（推荐，MCP 新标准）：**
```bash
# 启动 Streamable HTTP 服务（默认）
linux-profiler --http

# 无状态模式
linux-profiler --http --stateless

# 自定义端口
linux-profiler --http --port 22222
```

**SSE 传输（传统模式）：**
```bash
# 使用 SSE 传输
linux-profiler --http --transport sse
```

**同时支持两种传输：**
```bash
# 同时启用 SSE 和 Streamable HTTP
linux-profiler --http --transport both
```

启动后可访问的端点：

| 传输类型 | 端点 | 说明 |
|---------|------|------|
| Streamable HTTP | `/mcp` | MCP 主端点（GET/POST/DELETE） |
| SSE | `/sse` | SSE 连接端点 |
| SSE | `/sse/messages/` | SSE 消息端点（仅 both 模式） |
| 通用 | `/health` | 健康检查 |
| 通用 | `/` | 服务信息 |

#### 3. 配置 MCP 客户端

**STDIO 模式配置：**
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

**Streamable HTTP 模式配置（推荐）：**
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

**SSE 模式配置（传统）：**
```json
{
  "mcpServers": {
    "linux-profiler": {
      "url": "http://your-server:22222/sse"
    }
  }
}
```

### 可用的 MCP Tools

#### 核心监控工具

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

#### 🆕 高级剖析工具 (v1.1.0)

| 工具名称 | 描述 | 参数 |
|---------|------|------|
| `search_processes` | 通过关键字搜索进程（名称或命令行） | `keyword`（必需）, `case_sensitive`（可选） |
| `profile_process` | 使用 Linux perf 分析进程，生成火焰图数据 | `pid`（必需）, `duration`, `frequency`, `event` |

> **🔥 新功能**: 
> - **进程搜索**: 快速通过名称或命令模式查找进程
> - **CPU 剖析**: 通过 perf 工具集成进行深度性能分析
> - **火焰图生成**: 生成交互式 HTML 火焰图进行性能可视化
> 
> 详见 [FEATURES.md](FEATURES.md) 了解详细文档和示例。

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

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--http` | 启用 HTTP 模式（默认为 STDIO 模式） |
| `--port, -p` | HTTP 监听端口（默认: 22222） |
| `--host, -H` | HTTP 监听地址（默认: 0.0.0.0） |
| `--transport, -t` | 传输类型: `streamable`（默认）、`sse`、`both` |
| `--stateless` | Streamable HTTP 无状态模式 |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `PROFILER_PORT` | HTTP 默认端口 | 22222 |
| `PROFILER_HOST` | HTTP 默认地址 | 0.0.0.0 |
| `PROFILER_TRANSPORT` | 默认传输类型 | streamable |

### 依赖

- Python >= 3.10
- mcp >= 1.0.0
- psutil >= 5.9.0
- starlette >= 0.27.0
- uvicorn >= 0.24.0
- pydantic >= 2.0.0

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
