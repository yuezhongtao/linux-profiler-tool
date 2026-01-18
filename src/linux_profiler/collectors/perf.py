"""Performance profiling collector using perf."""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .base import BaseCollector


class PerfCollector(BaseCollector):
    """Collector for perf-based performance profiling."""

    def __init__(self):
        """Initialize perf collector."""
        self._check_perf_available()

    def _check_perf_available(self) -> bool:
        """Check if perf tool is available on the system."""
        try:
            result = subprocess.run(
                ["perf", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def collect(self) -> dict[str, Any]:
        """Not used for this collector."""
        raise NotImplementedError("Use collect_process_profile instead")

    def collect_process_profile(
        self,
        pid: int,
        duration: int = 10,
        frequency: int = 99,
        event: str = "cpu-clock"
    ) -> dict[str, Any]:
        """
        Collect performance profile for a specific process using perf.

        Args:
            pid: Process ID to profile
            duration: Duration in seconds to collect data (default: 10)
            frequency: Sampling frequency in Hz (default: 99)
            event: Perf event to record (default: cpu-clock)

        Returns:
            Dictionary containing profiling data and flame graph information
        """
        if not self._check_perf_available():
            return {
                "success": False,
                "error": "perf tool is not available on this system",
                "help": "Install perf with: apt-get install linux-tools-generic (Ubuntu/Debian) or yum install perf (RHEL/CentOS)"
            }

        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
        except ProcessLookupError:
            return {
                "success": False,
                "error": f"Process with PID {pid} does not exist"
            }
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied to access process {pid}"
            }

        # Create temporary directory for perf data
        with tempfile.TemporaryDirectory() as temp_dir:
            perf_data_file = Path(temp_dir) / "perf.data"
            
            # Record perf data
            try:
                record_cmd = [
                    "perf", "record",
                    "-F", str(frequency),
                    "-p", str(pid),
                    "-g",  # Enable call-graph (stack trace) recording
                    "-e", event,
                    "-o", str(perf_data_file),
                    "--", "sleep", str(duration)
                ]
                
                record_result = subprocess.run(
                    record_cmd,
                    capture_output=True,
                    text=True,
                    timeout=duration + 10
                )
                
                if record_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"perf record failed: {record_result.stderr}",
                        "command": " ".join(record_cmd)
                    }
                
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": f"perf record timed out after {duration + 10} seconds"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to run perf record: {str(e)}"
                }

            # Parse perf data to get stack traces
            try:
                script_cmd = [
                    "perf", "script",
                    "-i", str(perf_data_file)
                ]
                
                script_result = subprocess.run(
                    script_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if script_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"perf script failed: {script_result.stderr}"
                    }
                
                stack_traces = script_result.stdout
                
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "perf script timed out"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to parse perf data: {str(e)}"
                }

            # Get report summary
            try:
                report_cmd = [
                    "perf", "report",
                    "-i", str(perf_data_file),
                    "--stdio",
                    "--no-children"
                ]
                
                report_result = subprocess.run(
                    report_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                report_summary = report_result.stdout if report_result.returncode == 0 else ""
                
            except Exception:
                report_summary = ""

            # Parse stack traces for flame graph format
            flame_graph_data = self._parse_to_flame_graph_format(stack_traces)
            
            # Get statistics
            stats = self._extract_statistics(report_summary)

            return {
                "success": True,
                "pid": pid,
                "duration": duration,
                "frequency": frequency,
                "event": event,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "statistics": stats,
                "flame_graph_data": flame_graph_data,
                "raw_stack_traces": stack_traces[:10000] if len(stack_traces) > 10000 else stack_traces,  # Limit size
                "report_summary": report_summary[:5000] if len(report_summary) > 5000 else report_summary,  # Limit size
                "help": "Use flame_graph_data to generate flame graph visualization"
            }

    def _parse_to_flame_graph_format(self, stack_traces: str) -> list[dict[str, Any]]:
        """
        Parse perf script output to flame graph format.

        Returns:
            List of stack samples in format suitable for flame graph generation
        """
        samples = []
        current_sample = None
        current_stack = []
        
        for line in stack_traces.split('\n'):
            line = line.strip()
            
            if not line:
                # End of current sample
                if current_sample and current_stack:
                    samples.append({
                        "command": current_sample.get("command", ""),
                        "pid": current_sample.get("pid", 0),
                        "timestamp": current_sample.get("timestamp", ""),
                        "stack": list(reversed(current_stack))  # Reverse for flame graph (root at bottom)
                    })
                current_sample = None
                current_stack = []
                continue
            
            # Sample header line (e.g., "python 12345 [000] 123456.789: cpu-clock:")
            if not line.startswith('\t') and ':' in line:
                parts = line.split()
                if len(parts) >= 4:
                    current_sample = {
                        "command": parts[0],
                        "pid": int(parts[1]) if parts[1].isdigit() else 0,
                        "timestamp": parts[3] if len(parts) > 3 else ""
                    }
            # Stack frame line (starts with tab)
            elif line.startswith('\t'):
                # Remove leading whitespace and address
                frame = line.strip()
                # Extract function name (format: "address function (module)")
                if '(' in frame:
                    func_part = frame.split('(')[0].strip()
                    # Remove address part
                    parts = func_part.split(maxsplit=1)
                    if len(parts) > 1:
                        current_stack.append(parts[1])
                    else:
                        current_stack.append(func_part)
        
        return samples

    def _extract_statistics(self, report_summary: str) -> dict[str, Any]:
        """Extract key statistics from perf report."""
        top_functions: list[dict[str, Any]] = []
        stats: dict[str, Any] = {
            "total_samples": 0,
            "top_functions": top_functions
        }
        
        if not report_summary:
            return stats
        
        # Parse report to extract top functions
        in_overhead_section = False
        for line in report_summary.split('\n'):
            line = line.strip()
            
            # Look for overhead section
            if 'Overhead' in line and 'Command' in line:
                in_overhead_section = True
                continue
            
            if in_overhead_section and line:
                # Try to parse overhead line (e.g., "12.34%  python  [.] function_name")
                parts = line.split()
                if len(parts) >= 3 and '%' in parts[0]:
                    try:
                        overhead = float(parts[0].rstrip('%'))
                        command = parts[1]
                        # Function name is usually after symbol type [.]
                        func_name = ' '.join(parts[3:]) if len(parts) > 3 else parts[2]
                        
                        top_functions.append({
                            "overhead_percent": overhead,
                            "command": command,
                            "function": func_name
                        })
                        
                        if len(top_functions) >= 20:  # Limit to top 20
                            break
                    except (ValueError, IndexError):
                        continue
        
        stats["total_samples"] = len(top_functions)
        
        return stats

    def get_description(self) -> str:
        return "Collects performance profile data using perf for flame graph generation."
