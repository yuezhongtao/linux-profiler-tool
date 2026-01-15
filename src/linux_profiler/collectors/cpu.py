"""CPU performance collector."""

import psutil
from typing import Any

from .base import BaseCollector


class CPUCollector(BaseCollector):
    """Collector for CPU performance metrics."""

    def collect(self) -> dict[str, Any]:
        """Collect CPU metrics including usage, frequency, and load average."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq(percpu=True)
        cpu_times = psutil.cpu_times_percent(interval=0)
        load_avg = psutil.getloadavg()
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)

        freq_info = []
        if cpu_freq:
            for i, freq in enumerate(cpu_freq):
                freq_info.append({
                    "core": i,
                    "current_mhz": round(freq.current, 2),
                    "min_mhz": round(freq.min, 2) if freq.min else None,
                    "max_mhz": round(freq.max, 2) if freq.max else None,
                })

        return {
            "overall_percent": round(sum(cpu_percent) / len(cpu_percent), 2),
            "per_core_percent": [round(p, 2) for p in cpu_percent],
            "core_count_physical": cpu_count,
            "core_count_logical": cpu_count_logical,
            "frequency": freq_info,
            "times": {
                "user": round(cpu_times.user, 2),
                "system": round(cpu_times.system, 2),
                "idle": round(cpu_times.idle, 2),
                "iowait": round(getattr(cpu_times, 'iowait', 0), 2),
                "irq": round(getattr(cpu_times, 'irq', 0), 2),
                "softirq": round(getattr(cpu_times, 'softirq', 0), 2),
            },
            "load_average": {
                "1min": round(load_avg[0], 2),
                "5min": round(load_avg[1], 2),
                "15min": round(load_avg[2], 2),
            },
        }

    def get_description(self) -> str:
        return "Collects CPU usage, frequency, load average, and time distribution metrics."
