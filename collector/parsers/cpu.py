"""CPU metrics parser."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CPUMetrics:
    usage_percent: float
    cores: int


def parse_cpu(cpu_stat: str, cpu_info: str) -> Optional[CPUMetrics]:
    """
    Parse CPU metrics from /proc/stat and /proc/cpuinfo output.

    Args:
        cpu_stat: Output of 'cat /proc/stat | head -1'
                  Format: cpu  user nice system idle iowait irq softirq steal guest guest_nice
        cpu_info: Output of 'grep -c ^processor /proc/cpuinfo'

    Returns:
        CPUMetrics object or None if parsing fails
    """
    try:
        # Parse core count
        cores = int(cpu_info.strip()) if cpu_info.strip().isdigit() else 1

        # Parse CPU stat
        # Format: cpu  user nice system idle iowait irq softirq steal guest guest_nice
        parts = cpu_stat.strip().split()
        if len(parts) < 5 or parts[0] != 'cpu':
            return CPUMetrics(usage_percent=0.0, cores=cores)

        # Extract values (all in jiffies)
        user = int(parts[1])
        nice = int(parts[2])
        system = int(parts[3])
        idle = int(parts[4])
        iowait = int(parts[5]) if len(parts) > 5 else 0
        irq = int(parts[6]) if len(parts) > 6 else 0
        softirq = int(parts[7]) if len(parts) > 7 else 0
        steal = int(parts[8]) if len(parts) > 8 else 0

        # Calculate usage
        # Note: This is cumulative since boot, for instant usage we'd need two samples
        # For simplicity, we calculate based on non-idle vs total
        total = user + nice + system + idle + iowait + irq + softirq + steal
        idle_total = idle + iowait

        if total > 0:
            usage_percent = round((1 - idle_total / total) * 100, 1)
        else:
            usage_percent = 0.0

        return CPUMetrics(usage_percent=usage_percent, cores=cores)

    except (ValueError, IndexError):
        return None
