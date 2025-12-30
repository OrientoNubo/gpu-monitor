"""Disk metrics parser."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiskMetrics:
    device: str
    mount_point: str
    total_bytes: int
    used_bytes: int
    available_bytes: int
    usage_percent: float


def parse_disk(df_output: str) -> List[DiskMetrics]:
    """
    Parse disk metrics from df output.

    Args:
        df_output: Output of 'df -B1 --output=source,size,used,avail,target'
                   Format: /dev/sda1  1000000000  300000000  700000000  /

    Returns:
        List of DiskMetrics objects
    """
    disks = []

    for line in df_output.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Filesystem'):
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        try:
            device = parts[0]
            # Skip non-physical devices
            if not device.startswith('/dev/'):
                continue

            # Parse values (in bytes if -B1 was used, otherwise in KB blocks)
            total = int(parts[1])
            used = int(parts[2])
            available = int(parts[3])
            mount_point = parts[4]

            # If values seem too small, they might be in KB (fallback for systems without -B1)
            if total < 1000000:  # Less than 1MB total is suspicious
                total *= 1024
                used *= 1024
                available *= 1024

            # Calculate usage percentage
            usage_percent = round((used / total) * 100, 1) if total > 0 else 0.0

            disks.append(DiskMetrics(
                device=device,
                mount_point=mount_point,
                total_bytes=total,
                used_bytes=used,
                available_bytes=available,
                usage_percent=usage_percent,
            ))

        except (ValueError, IndexError):
            continue

    return disks
