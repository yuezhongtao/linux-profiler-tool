"""MCP Server for Linux Performance Profiler."""

import asyncio
import json
import platform
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .collectors import (
    CPUCollector,
    MemoryCollector,
    DiskCollector,
    NetworkCollector,
    ProcessCollector,
)


# Initialize collectors
cpu_collector = CPUCollector()
memory_collector = MemoryCollector()
disk_collector = DiskCollector()
network_collector = NetworkCollector()
process_collector = ProcessCollector(top_n=10)

# Create MCP server
server = Server("linux-profiler")


def get_system_info() -> dict[str, Any]:
    """Get basic system information."""
    return {
        "hostname": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "timestamp": datetime.now().isoformat(),
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available performance profiling tools."""
    return [
        Tool(
            name="get_system_info",
            description="Get basic system information including hostname, OS, kernel version, and architecture.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_cpu_metrics",
            description=cpu_collector.get_description(),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_memory_metrics",
            description=memory_collector.get_description(),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_disk_metrics",
            description=disk_collector.get_description(),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_network_metrics",
            description=network_collector.get_description(),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_process_metrics",
            description=process_collector.get_description(),
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top processes to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_all_metrics",
            description="Get a comprehensive performance report including CPU, memory, disk, network, and process metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_processes": {
                        "type": "boolean",
                        "description": "Whether to include process information (default: true)",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_performance_summary",
            description="Get a brief performance summary with key metrics and potential issues.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls for performance profiling."""
    try:
        if name == "get_system_info":
            result = get_system_info()
        
        elif name == "get_cpu_metrics":
            result = cpu_collector.collect()
        
        elif name == "get_memory_metrics":
            result = memory_collector.collect()
        
        elif name == "get_disk_metrics":
            result = disk_collector.collect()
        
        elif name == "get_network_metrics":
            result = network_collector.collect()
        
        elif name == "get_process_metrics":
            top_n = arguments.get("top_n", 10)
            collector = ProcessCollector(top_n=top_n)
            result = collector.collect()
        
        elif name == "get_all_metrics":
            include_processes = arguments.get("include_processes", True)
            result = {
                "system": get_system_info(),
                "cpu": cpu_collector.collect(),
                "memory": memory_collector.collect(),
                "disk": disk_collector.collect(),
                "network": network_collector.collect(),
            }
            if include_processes:
                result["processes"] = process_collector.collect()
        
        elif name == "get_performance_summary":
            result = generate_performance_summary()
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


def generate_performance_summary() -> dict[str, Any]:
    """Generate a performance summary with potential issues."""
    cpu = cpu_collector.collect()
    memory = memory_collector.collect()
    disk = disk_collector.collect()
    
    issues = []
    warnings = []
    
    # Check CPU
    if cpu["overall_percent"] > 90:
        issues.append(f"Critical: CPU usage is very high ({cpu['overall_percent']}%)")
    elif cpu["overall_percent"] > 70:
        warnings.append(f"Warning: CPU usage is elevated ({cpu['overall_percent']}%)")
    
    if cpu["load_average"]["1min"] > cpu["core_count_logical"] * 2:
        issues.append(f"Critical: Load average ({cpu['load_average']['1min']}) is very high")
    elif cpu["load_average"]["1min"] > cpu["core_count_logical"]:
        warnings.append(f"Warning: Load average ({cpu['load_average']['1min']}) exceeds core count")
    
    # Check Memory
    if memory["virtual"]["percent"] > 95:
        issues.append(f"Critical: Memory usage is critical ({memory['virtual']['percent']}%)")
    elif memory["virtual"]["percent"] > 80:
        warnings.append(f"Warning: Memory usage is high ({memory['virtual']['percent']}%)")
    
    if memory["swap"]["percent"] > 50:
        warnings.append(f"Warning: Swap usage is high ({memory['swap']['percent']}%)")
    
    # Check Disk
    for partition in disk["partitions"]:
        if partition["percent"] > 95:
            issues.append(f"Critical: Disk {partition['mountpoint']} is almost full ({partition['percent']}%)")
        elif partition["percent"] > 80:
            warnings.append(f"Warning: Disk {partition['mountpoint']} usage is high ({partition['percent']}%)")
    
    # Determine overall status
    if issues:
        status = "critical"
    elif warnings:
        status = "warning"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "cpu_percent": cpu["overall_percent"],
            "load_average_1min": cpu["load_average"]["1min"],
            "memory_percent": memory["virtual"]["percent"],
            "swap_percent": memory["swap"]["percent"],
        },
        "issues": issues,
        "warnings": warnings,
    }


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
