"""GPU metrics parser."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .process import ProcessInfo


@dataclass
class GPUProcess:
    pid: int
    user: str
    command: str
    gpu_memory_mb: int


@dataclass
class GPUMemory:
    used_mb: int
    total_mb: int
    usage_percent: float


@dataclass
class GPUMetrics:
    index: int
    name: str
    uuid: str
    temperature_celsius: int
    utilization_percent: int
    memory: GPUMemory
    driver_version: str
    processes: List[GPUProcess] = field(default_factory=list)


def parse_gpus(
    gpu_info: str,
    gpu_processes: str,
    process_map: Dict[int, ProcessInfo],
) -> List[GPUMetrics]:
    """
    Parse GPU metrics from nvidia-smi output.

    Args:
        gpu_info: Output of nvidia-smi --query-gpu=...
                  Format: 0, NVIDIA RTX 6000, GPU-xxx, 39, 0, 43, 49140, 570.133.07
        gpu_processes: Output of nvidia-smi --query-compute-apps=...
                       Format: GPU-xxx, 1234, 5000
        process_map: Pre-built process map from ps output

    Returns:
        List of GPUMetrics objects
    """
    if 'NO_GPU' in gpu_info:
        return []

    # Build UUID to GPU index mapping
    uuid_to_gpu: Dict[str, GPUMetrics] = {}
    gpus: List[GPUMetrics] = []

    # Parse GPU info
    for line in gpu_info.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 8:
            continue

        try:
            index = int(parts[0])
            name = parts[1]
            uuid = parts[2]
            temp = int(parts[3]) if parts[3].isdigit() else 0
            util = int(parts[4]) if parts[4].isdigit() else 0
            mem_used = int(parts[5]) if parts[5].isdigit() else 0
            mem_total = int(parts[6]) if parts[6].isdigit() else 1
            driver = parts[7]

            mem_percent = round((mem_used / mem_total) * 100, 1) if mem_total > 0 else 0.0

            gpu = GPUMetrics(
                index=index,
                name=name,
                uuid=uuid,
                temperature_celsius=temp,
                utilization_percent=util,
                memory=GPUMemory(
                    used_mb=mem_used,
                    total_mb=mem_total,
                    usage_percent=mem_percent,
                ),
                driver_version=driver,
                processes=[],
            )

            gpus.append(gpu)
            uuid_to_gpu[uuid] = gpu

        except (ValueError, IndexError):
            continue

    # Parse GPU processes
    if 'NO_PROCESSES' not in gpu_processes:
        for line in gpu_processes.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 3:
                continue

            try:
                gpu_uuid = parts[0]
                pid = int(parts[1])
                gpu_mem = int(parts[2]) if parts[2].isdigit() else 0

                # Find the GPU this process belongs to
                gpu = uuid_to_gpu.get(gpu_uuid)
                if not gpu:
                    continue

                # Get process info from the pre-built map
                proc_info = process_map.get(pid)
                user = proc_info.user if proc_info else "unknown"
                command = proc_info.command if proc_info else "unknown"

                gpu.processes.append(GPUProcess(
                    pid=pid,
                    user=user,
                    command=command,
                    gpu_memory_mb=gpu_mem,
                ))

            except (ValueError, IndexError):
                continue

    return gpus
