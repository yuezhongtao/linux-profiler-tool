"""Process performance collector."""

import psutil
from typing import Any

from .base import BaseCollector


def bytes_to_human(bytes_val: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


class ProcessCollector(BaseCollector):
    """Collector for process performance metrics."""

    def __init__(self, top_n: int = 10):
        """Initialize with number of top processes to return.
        
        Args:
            top_n: Number of top processes to include in results.
        """
        self.top_n = top_n

    def collect(self) -> dict[str, Any]:
        """Collect process statistics and top resource consumers."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                          'memory_percent', 'memory_info', 'status',
                                          'create_time', 'num_threads']):
            try:
                info = proc.info
                mem_info = info.get('memory_info')
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "username": info['username'],
                    "cpu_percent": round(info['cpu_percent'] or 0, 2),
                    "memory_percent": round(info['memory_percent'] or 0, 2),
                    "memory_rss_bytes": mem_info.rss if mem_info else 0,
                    "memory_rss_human": bytes_to_human(mem_info.rss) if mem_info else "0 B",
                    "memory_vms_bytes": mem_info.vms if mem_info else 0,
                    "status": info['status'],
                    "num_threads": info['num_threads'],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by CPU usage
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:self.top_n]
        
        # Sort by memory usage
        top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:self.top_n]

        # Process status summary
        status_counts = {}
        for proc in processes:
            status = proc['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_count": len(processes),
            "status_summary": status_counts,
            "top_cpu_consumers": top_cpu,
            "top_memory_consumers": top_memory,
        }

    def get_description(self) -> str:
        return f"Collects process statistics including top {self.top_n} CPU and memory consumers."
