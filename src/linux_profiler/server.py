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
from mcp.server.streamable_http import StreamableHTTPServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

from .collectors import (
    CPUCollector,
    MemoryCollector,
    DiskCollector,
    NetworkCollector,
    ProcessCollector,
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


# ============ STDIO Mode ============

async def run_stdio_server():
    """Run the MCP server in STDIO mode."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


# ============ HTTP/SSE Mode (Legacy) ============

def create_sse_app() -> Starlette:
    """Create Starlette app for SSE transport (legacy mode)."""
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

    async def health_check(request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": "1.0.0",
            "transport": "sse",
        })

    async def server_info(request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": "1.0.0",
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
    # Session storage for stateful mode
    session_transports: dict[str, StreamableHTTPServerTransport] = {}
    session_lock = asyncio.Lock()

    async def handle_mcp(request):
        """Handle MCP requests via Streamable HTTP."""
        if stateless:
            # Stateless mode: create new transport for each request
            transport = StreamableHTTPServerTransport(
                mcp_session_id=None,
                is_json_response_enabled=True,
            )
            async with transport.connect() as streams:
                read_stream, write_stream = streams
                # Run server in background task
                async def run_server():
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
                task = asyncio.create_task(run_server())
                try:
                    response = await transport.handle_request(
                        request.scope, request.receive, request._send
                    )
                    return response
                finally:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        else:
            # Stateful mode: maintain sessions
            session_id = request.headers.get("mcp-session-id")
            
            async with session_lock:
                if session_id and session_id in session_transports:
                    transport = session_transports[session_id]
                else:
                    # Create new session
                    transport = StreamableHTTPServerTransport(
                        mcp_session_id=None,
                        is_json_response_enabled=True,
                    )
                    
            # Handle the request
            async with transport.connect() as streams:
                read_stream, write_stream = streams
                
                async def run_server():
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
                
                task = asyncio.create_task(run_server())
                try:
                    response = await transport.handle_request(
                        request.scope, request.receive, request._send
                    )
                    
                    # Store session if new
                    if transport.mcp_session_id:
                        async with session_lock:
                            session_transports[transport.mcp_session_id] = transport
                    
                    return response
                finally:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def handle_mcp_delete(request):
        """Handle session termination."""
        session_id = request.headers.get("mcp-session-id")
        if session_id:
            async with session_lock:
                if session_id in session_transports:
                    del session_transports[session_id]
        return JSONResponse({"status": "session terminated"})

    async def health_check(request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": "1.0.0",
            "transport": "streamable-http",
            "stateless": stateless,
        })

    async def server_info(request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": "1.0.0",
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
        routes=[
            Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST"]),
            Route("/mcp", endpoint=handle_mcp_delete, methods=["DELETE"]),
            Route("/health", endpoint=health_check),
            Route("/", endpoint=server_info),
        ],
    )
    return app


# ============ Combined HTTP App (SSE + Streamable) ============

def create_combined_http_app(stateless: bool = False) -> Starlette:
    """Create combined app supporting both SSE and Streamable HTTP transports."""
    sse_transport = SseServerTransport("/sse/messages/")
    session_transports: dict[str, StreamableHTTPServerTransport] = {}
    session_lock = asyncio.Lock()

    # SSE handlers
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

    async def handle_sse_messages(request):
        """Handle POST messages for SSE transport."""
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    # Streamable HTTP handlers
    async def handle_mcp(request):
        """Handle MCP requests via Streamable HTTP."""
        if stateless:
            transport = StreamableHTTPServerTransport(
                mcp_session_id=None,
                is_json_response_enabled=True,
            )
            async with transport.connect() as streams:
                read_stream, write_stream = streams
                async def run_server():
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
                task = asyncio.create_task(run_server())
                try:
                    response = await transport.handle_request(
                        request.scope, request.receive, request._send
                    )
                    return response
                finally:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        else:
            session_id = request.headers.get("mcp-session-id")
            
            async with session_lock:
                if session_id and session_id in session_transports:
                    transport = session_transports[session_id]
                else:
                    transport = StreamableHTTPServerTransport(
                        mcp_session_id=None,
                        is_json_response_enabled=True,
                    )
                    
            async with transport.connect() as streams:
                read_stream, write_stream = streams
                
                async def run_server():
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
                
                task = asyncio.create_task(run_server())
                try:
                    response = await transport.handle_request(
                        request.scope, request.receive, request._send
                    )
                    
                    if transport.mcp_session_id:
                        async with session_lock:
                            session_transports[transport.mcp_session_id] = transport
                    
                    return response
                finally:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

    async def handle_mcp_delete(request):
        """Handle session termination."""
        session_id = request.headers.get("mcp-session-id")
        if session_id:
            async with session_lock:
                if session_id in session_transports:
                    del session_transports[session_id]
        return JSONResponse({"status": "session terminated"})

    async def health_check(request):
        """Health check endpoint."""
        return JSONResponse({
            "status": "ok",
            "service": "linux-profiler",
            "version": "1.0.0",
            "transports": ["sse", "streamable-http"],
        })

    async def server_info(request):
        """Server info endpoint."""
        return JSONResponse({
            "name": "linux-profiler",
            "version": "1.0.0",
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
        routes=[
            # SSE transport routes
            Route("/sse", endpoint=handle_sse),
            Route("/sse/messages/", endpoint=handle_sse_messages, methods=["POST"]),
            # Streamable HTTP transport routes
            Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST"]),
            Route("/mcp", endpoint=handle_mcp_delete, methods=["DELETE"]),
            # Common routes
            Route("/health", endpoint=health_check),
            Route("/", endpoint=server_info),
        ],
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
