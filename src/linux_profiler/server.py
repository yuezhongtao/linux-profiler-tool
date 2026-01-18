"""MCP Server for Linux Performance Profiler with HTTP support."""

import argparse
import asyncio
import json
import os
import platform

from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse

from . import __version__
from .collectors import (
    CPUCollector,
    MemoryCollector,
    DiskCollector,
    NetworkCollector,
    ProcessCollector,
    PerfCollector,
)


# Default configuration
DEFAULT_PORT = 22222
DEFAULT_HOST = "0.0.0.0"

# Initialize collectors
cpu_collector = CPUCollector()
memory_collector = MemoryCollector()
disk_collector = DiskCollector()
network_collector = NetworkCollector()
process_collector = ProcessCollector(top_n=10)
perf_collector = PerfCollector()


def create_mcp_server() -> Server:
    """Create and configure MCP server instance."""
    mcp_server = Server("linux-profiler")

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

    @mcp_server.list_tools()
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
            Tool(
                name="search_processes",
                description="Search for processes by keyword (name or command line). Returns matching process IDs and details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in process names or command lines",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether to perform case-sensitive search (default: false)",
                            "default": False,
                        },
                    },
                    "required": ["keyword"],
                },
            ),
            Tool(
                name="profile_process",
                description="Profile a specific process using perf to collect performance data for flame graph generation. Requires perf tool to be installed on the system.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to profile",
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in seconds to collect data (default: 10)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 300,
                        },
                        "frequency": {
                            "type": "integer",
                            "description": "Sampling frequency in Hz (default: 99)",
                            "default": 99,
                            "minimum": 1,
                            "maximum": 10000,
                        },
                        "event": {
                            "type": "string",
                            "description": "Perf event to record (default: cpu-clock). Other options: cycles, instructions, cache-misses",
                            "default": "cpu-clock",
                        },
                    },
                    "required": ["pid"],
                },
            ),
        ]

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

    @mcp_server.call_tool()
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
            
            elif name == "search_processes":
                keyword = arguments.get("keyword", "")
                case_sensitive = arguments.get("case_sensitive", False)
                result = process_collector.search_processes(keyword, case_sensitive)
            
            elif name == "profile_process":
                pid = arguments.get("pid")
                if pid is None:
                    return [TextContent(type="text", text="Error: 'pid' parameter is required")]
                
                duration = arguments.get("duration", 10)
                frequency = arguments.get("frequency", 99)
                event = arguments.get("event", "cpu-clock")
                
                # Validate parameters
                if not isinstance(pid, int) or pid <= 0:
                    return [TextContent(type="text", text=f"Error: Invalid PID: {pid}")]
                
                if not (1 <= duration <= 300):
                    return [TextContent(type="text", text=f"Error: Duration must be between 1 and 300 seconds")]
                
                if not (1 <= frequency <= 10000):
                    return [TextContent(type="text", text=f"Error: Frequency must be between 1 and 10000 Hz")]
                
                result = perf_collector.collect_process_profile(
                    pid=pid,
                    duration=duration,
                    frequency=frequency,
                    event=event
                )
            
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        except Exception as e:
            return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    return mcp_server


# ============ STDIO Mode ============

async def run_stdio_server():
    """Run the MCP server in STDIO mode."""
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


# ============ HTTP/SSE Mode (Legacy) ============

def create_sse_app() -> Starlette:
    """Create Starlette app for SSE transport (legacy mode)."""
    server = create_mcp_server()
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        """Handle SSE connection for MCP."""
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    async def handle_messages(request):
        """Handle POST messages for MCP."""
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    async def health_check(_request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": __version__,
            "transport": "sse",
        })

    async def server_info(_request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": __version__,
            "transport": "sse",
            "endpoints": {
                "sse": "/sse",
                "messages": "/messages/",
                "health": "/health",
            },
        })

    app = Starlette(
        debug=False,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health_check),
            Route("/", endpoint=server_info),
        ],
    )
    return app


# ============ Streamable HTTP Mode (New Standard) ============

def create_streamable_http_app(stateless: bool = False) -> Starlette:
    """Create Starlette app for Streamable HTTP transport.
    
    Args:
        stateless: If True, run in stateless mode (no session management).
                   If False, run in stateful mode with session support.
    """
    from contextlib import asynccontextmanager
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.routing import Mount
    
    # Create MCP server instance
    mcp_server = create_mcp_server()
    
    # Create session manager
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
        stateless=stateless,
    )
    
    @asynccontextmanager
    async def lifespan(app: Starlette):
        """Application lifespan - manage session manager lifecycle."""
        async with session_manager.run():
            yield

    async def health_check(_request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": __version__,
            "transport": "streamable-http",
            "stateless": stateless,
        })

    async def server_info(_request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": __version__,
            "transport": "streamable-http",
            "stateless": stateless,
            "endpoints": {
                "mcp": "/mcp",
                "health": "/health",
            },
            "capabilities": {
                "streaming": True,
                "json_response": True,
            },
        })
    
    app = Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[
            Mount("/mcp", app=session_manager.handle_request),
            Route("/health", endpoint=health_check),
            Route("/", endpoint=server_info),
        ],
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    
    return app


# ============ Combined HTTP App (SSE + Streamable) ============

def create_combined_http_app(stateless: bool = False) -> Starlette:
    """Create combined app supporting both SSE and Streamable HTTP transports."""
    from contextlib import asynccontextmanager
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.routing import Mount
    
    sse_transport = SseServerTransport("/sse/messages/")
    
    # Create MCP server for Streamable HTTP
    mcp_server = create_mcp_server()
    
    # Create session manager for Streamable HTTP
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
        stateless=stateless,
    )
    
    @asynccontextmanager
    async def lifespan(_app: Starlette):
        """Application lifespan - manage session manager lifecycle."""
        async with session_manager.run():
            yield

    # SSE handlers
    async def handle_sse(request):
        """Handle SSE connection for MCP."""
        server = create_mcp_server()
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    async def handle_sse_messages(request):
        """Handle POST messages for SSE transport."""
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    async def health_check(_request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": __version__,
            "transports": ["sse", "streamable-http"],
        })

    async def server_info(_request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": __version__,
            "transports": {
                "sse": {
                    "endpoint": "/sse",
                    "messages": "/sse/messages/",
                },
                "streamable-http": {
                    "endpoint": "/mcp",
                    "stateless": stateless,
                },
            },
            "health": "/health",
        })
    
    app = Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[
            # SSE transport routes
            Route("/sse", endpoint=handle_sse),
            Route("/sse/messages/", endpoint=handle_sse_messages, methods=["POST"]),
            # Streamable HTTP transport routes (as ASGI mount)
            Mount("/mcp", app=session_manager.handle_request),
            # Common routes
            Route("/health", endpoint=health_check),
            Route("/", endpoint=server_info),
        ],
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    
    return app


async def run_http_server(host: str, port: int, transport: str = "streamable", stateless: bool = False):
    """Run the MCP server in HTTP mode.
    
    Args:
        host: Host to bind to.
        port: Port to listen on.
        transport: Transport type ("sse", "streamable", or "both").
        stateless: If True, run in stateless mode (for streamable transport).
    """
    import uvicorn
    
    if transport == "sse":
        app = create_sse_app()
        transport_name = "SSE"
    elif transport == "streamable":
        app = create_streamable_http_app(stateless=stateless)
        transport_name = "Streamable HTTP"
    else:  # both
        app = create_combined_http_app(stateless=stateless)
        transport_name = "SSE + Streamable HTTP"
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    http_server = uvicorn.Server(config)
    
    print(f"Starting Linux Profiler MCP Server ({transport_name} mode)")
    print(f"Listening on http://{host}:{port}")
    
    if transport == "sse":
        print(f"SSE endpoint: http://{host}:{port}/sse")
        print(f"Messages endpoint: http://{host}:{port}/messages/")
    elif transport == "streamable":
        print(f"MCP endpoint: http://{host}:{port}/mcp")
        print(f"Mode: {'stateless' if stateless else 'stateful'}")
    else:
        print(f"SSE endpoint: http://{host}:{port}/sse")
        print(f"Streamable HTTP endpoint: http://{host}:{port}/mcp")
        print(f"Streamable mode: {'stateless' if stateless else 'stateful'}")
    
    await http_server.serve()


# ============ Main Entry ============

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Linux Performance Profiler MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in STDIO mode (default)
  linux-profiler

  # Run with Streamable HTTP (recommended, new standard)
  linux-profiler --http

  # Run with SSE transport (legacy)
  linux-profiler --http --transport sse

  # Run with both transports
  linux-profiler --http --transport both

  # Streamable HTTP in stateless mode
  linux-profiler --http --stateless

  # Custom host and port
  linux-profiler --http --host 127.0.0.1 --port 9000

Environment variables:
  PROFILER_PORT       Default HTTP port (default: 22222)
  PROFILER_HOST       Default HTTP host (default: 0.0.0.0)
  PROFILER_TRANSPORT  Default transport type (default: streamable)
        """
    )
    
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP mode instead of STDIO mode",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.environ.get("PROFILER_PORT", DEFAULT_PORT)),
        help=f"HTTP server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host", "-H",
        type=str,
        default=os.environ.get("PROFILER_HOST", DEFAULT_HOST),
        help=f"HTTP server host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--transport", "-t",
        type=str,
        choices=["sse", "streamable", "both"],
        default=os.environ.get("PROFILER_TRANSPORT", "streamable"),
        help="HTTP transport type: sse (legacy), streamable (new), or both (default: streamable)",
    )
    parser.add_argument(
        "--stateless",
        action="store_true",
        help="Run Streamable HTTP in stateless mode (no session management)",
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.http:
        asyncio.run(run_http_server(
            args.host,
            args.port,
            transport=args.transport,
            stateless=args.stateless,
        ))
    else:
        asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
