"""Network performance collector."""

import psutil
from typing import Any

from .base import BaseCollector
from .utils import bytes_to_human


class NetworkCollector(BaseCollector):
    """Collector for network performance metrics."""

    def collect(self) -> dict[str, Any]:
        """Collect network I/O and connection statistics."""
        io_counters = psutil.net_io_counters(pernic=True)
        interfaces = {}
        
        for nic_name, counters in io_counters.items():
            interfaces[nic_name] = {
                "bytes_sent": counters.bytes_sent,
                "bytes_sent_human": bytes_to_human(counters.bytes_sent),
                "bytes_recv": counters.bytes_recv,
                "bytes_recv_human": bytes_to_human(counters.bytes_recv),
                "packets_sent": counters.packets_sent,
                "packets_recv": counters.packets_recv,
                "errin": counters.errin,
                "errout": counters.errout,
                "dropin": counters.dropin,
                "dropout": counters.dropout,
            }

        # Get network addresses
        addrs = psutil.net_if_addrs()
        addresses = {}
        for nic_name, addr_list in addrs.items():
            addresses[nic_name] = []
            for addr in addr_list:
                addresses[nic_name].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                })

        # Get connection statistics
        try:
            connections = psutil.net_connections(kind='inet')
            conn_stats = {
                "total": len(connections),
                "established": sum(1 for c in connections if c.status == 'ESTABLISHED'),
                "listen": sum(1 for c in connections if c.status == 'LISTEN'),
                "time_wait": sum(1 for c in connections if c.status == 'TIME_WAIT'),
                "close_wait": sum(1 for c in connections if c.status == 'CLOSE_WAIT'),
            }
        except psutil.AccessDenied:
            conn_stats = {"error": "Access denied - requires root privileges"}

        return {
            "interfaces": interfaces,
            "addresses": addresses,
            "connections": conn_stats,
        }

    def get_description(self) -> str:
        return "Collects network I/O statistics, interface addresses, and connection states."
