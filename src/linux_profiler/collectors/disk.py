"""Disk I/O performance collector."""

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


class DiskCollector(BaseCollector):
    """Collector for disk I/O performance metrics."""

    def collect(self) -> dict[str, Any]:
        """Collect disk usage and I/O statistics."""
        partitions = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "opts": partition.opts,
                    "total_bytes": usage.total,
                    "total_human": bytes_to_human(usage.total),
                    "used_bytes": usage.used,
                    "used_human": bytes_to_human(usage.used),
                    "free_bytes": usage.free,
                    "free_human": bytes_to_human(usage.free),
                    "percent": round(usage.percent, 2),
                })
            except (PermissionError, OSError):
                continue

        io_counters = psutil.disk_io_counters(perdisk=True)
        io_stats = {}
        if io_counters:
            for disk_name, counters in io_counters.items():
                io_stats[disk_name] = {
                    "read_count": counters.read_count,
                    "write_count": counters.write_count,
                    "read_bytes": counters.read_bytes,
                    "read_human": bytes_to_human(counters.read_bytes),
                    "write_bytes": counters.write_bytes,
                    "write_human": bytes_to_human(counters.write_bytes),
                    "read_time_ms": counters.read_time,
                    "write_time_ms": counters.write_time,
                    "busy_time_ms": getattr(counters, 'busy_time', None),
                }

        return {
            "partitions": partitions,
            "io_counters": io_stats,
        }

    def get_description(self) -> str:
        return "Collects disk partition usage and I/O statistics including read/write counts and times."
