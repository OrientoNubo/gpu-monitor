"""Process information parser."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ProcessInfo:
    pid: int
    user: str
    command: str


def build_process_map(ps_output: str) -> Dict[int, ProcessInfo]:
    """
    Build a mapping from PID to process info.

    This solves the N+1 query problem by parsing all processes at once
    instead of querying each PID individually.

    Args:
        ps_output: Output of 'ps -eo pid,user,comm --no-headers'
                   Format:
                   1234 root     systemd
                   5678 user1    python

    Returns:
        Dictionary mapping PID to ProcessInfo
    """
    process_map = {}

    for line in ps_output.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = line.split(None, 2)  # Split into at most 3 parts
        if len(parts) < 3:
            continue

        try:
            pid = int(parts[0])
            user = parts[1]
            command = parts[2]

            process_map[pid] = ProcessInfo(
                pid=pid,
                user=user,
                command=command,
            )
        except (ValueError, IndexError):
            continue

    return process_map


def get_process_info(process_map: Dict[int, ProcessInfo], pid: int) -> Optional[ProcessInfo]:
    """Get process info by PID from the pre-built map."""
    return process_map.get(pid)
