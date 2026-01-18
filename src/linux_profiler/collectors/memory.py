"""Memory performance collector."""

import psutil
from typing import Any

from .base import BaseCollector
from .utils import bytes_to_human


class MemoryCollector(BaseCollector):
    """Collector for memory performance metrics."""

    def collect(self) -> dict[str, Any]:
        """Collect memory and swap usage metrics."""
        virtual = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "virtual": {
                "total_bytes": virtual.total,
                "total_human": bytes_to_human(virtual.total),
                "available_bytes": virtual.available,
                "available_human": bytes_to_human(virtual.available),
                "used_bytes": virtual.used,
                "used_human": bytes_to_human(virtual.used),
                "free_bytes": virtual.free,
                "free_human": bytes_to_human(virtual.free),
                "percent": round(virtual.percent, 2),
                "buffers_bytes": getattr(virtual, 'buffers', 0),
                "cached_bytes": getattr(virtual, 'cached', 0),
                "shared_bytes": getattr(virtual, 'shared', 0),
            },
            "swap": {
                "total_bytes": swap.total,
                "total_human": bytes_to_human(swap.total),
                "used_bytes": swap.used,
                "used_human": bytes_to_human(swap.used),
                "free_bytes": swap.free,
                "free_human": bytes_to_human(swap.free),
                "percent": round(swap.percent, 2),
                "sin_bytes": swap.sin,
                "sout_bytes": swap.sout,
            },
        }

    def get_description(self) -> str:
        return "Collects virtual memory and swap usage metrics including buffers and cache."
