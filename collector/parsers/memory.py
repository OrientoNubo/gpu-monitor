"""Memory metrics parser."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryMetrics:
    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percent: float
    swap_total_bytes: int = 0
    swap_used_bytes: int = 0


def parse_memory(meminfo: str) -> Optional[MemoryMetrics]:
    """
    Parse memory metrics from /proc/meminfo output.

    Args:
        meminfo: Output of 'cat /proc/meminfo | grep -E ...'
                 Contains lines like:
                 MemTotal:       32946852 kB
                 MemAvailable:   28123456 kB

    Returns:
        MemoryMetrics object or None if parsing fails
    """
    try:
        values = {}

        for line in meminfo.strip().split('\n'):
            if not line.strip():
                continue

            parts = line.split(':')
            if len(parts) != 2:
                continue

            key = parts[0].strip()
            value_parts = parts[1].strip().split()

            if value_parts:
                # Value is in kB, convert to bytes
                value_kb = int(value_parts[0])
                values[key] = value_kb * 1024

        # Extract values
        total = values.get('MemTotal', 0)
        available = values.get('MemAvailable', 0)
        free = values.get('MemFree', 0)
        buffers = values.get('Buffers', 0)
        cached = values.get('Cached', 0)

        # If MemAvailable is not present (older kernels), calculate it
        if available == 0 and total > 0:
            available = free + buffers + cached

        used = total - available

        # Calculate usage percentage
        usage_percent = round((used / total) * 100, 1) if total > 0 else 0.0

        # Swap
        swap_total = values.get('SwapTotal', 0)
        swap_free = values.get('SwapFree', 0)
        swap_used = swap_total - swap_free

        return MemoryMetrics(
            total_bytes=total,
            available_bytes=available,
            used_bytes=used,
            usage_percent=usage_percent,
            swap_total_bytes=swap_total,
            swap_used_bytes=swap_used,
        )

    except (ValueError, KeyError):
        return None
