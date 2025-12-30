#!/usr/bin/env python3
"""
GPU/CPU Monitor Collector - Main Entry Point

Collects system and GPU metrics from multiple servers via SSH
and outputs structured JSON data.
"""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from . import __version__
from .config import load_config, CollectorConfig
from .ssh_client import SSHCollector, CollectionResult
from .parsers import (
    parse_cpu,
    parse_memory,
    parse_disk,
    parse_gpus,
    build_process_map,
)


def process_result(result: CollectionResult) -> Dict[str, Any]:
    """Process a collection result into structured data."""
    server_data = {
        "name": result.server_name,
        "host": result.host,
        "status": "online" if result.success else "offline",
        "error_message": result.error,
        "collected_at": result.collected_at.isoformat() if result.collected_at else None,
    }

    if not result.success:
        return server_data

    sections = result.sections

    # Parse hostname
    server_data["hostname"] = sections.get("HOSTNAME", "").strip() or result.host

    # Parse system metrics
    cpu_metrics = parse_cpu(
        sections.get("CPU_STAT", ""),
        sections.get("CPU_INFO", "1"),
    )

    memory_metrics = parse_memory(sections.get("MEMORY", ""))
    disk_metrics = parse_disk(sections.get("DISK", ""))

    server_data["system"] = {
        "cpu": {
            "usage_percent": cpu_metrics.usage_percent if cpu_metrics else 0,
            "cores": cpu_metrics.cores if cpu_metrics else 0,
        },
        "memory": {
            "total_bytes": memory_metrics.total_bytes if memory_metrics else 0,
            "available_bytes": memory_metrics.available_bytes if memory_metrics else 0,
            "used_bytes": memory_metrics.used_bytes if memory_metrics else 0,
            "usage_percent": memory_metrics.usage_percent if memory_metrics else 0,
        },
        "disks": [
            {
                "device": disk.device,
                "mount_point": disk.mount_point,
                "total_bytes": disk.total_bytes,
                "used_bytes": disk.used_bytes,
                "available_bytes": disk.available_bytes,
                "usage_percent": disk.usage_percent,
            }
            for disk in disk_metrics
        ],
    }

    # Parse GPU metrics
    process_map = build_process_map(sections.get("ALL_PROCESSES", ""))
    gpu_metrics = parse_gpus(
        sections.get("GPU_INFO", "NO_GPU"),
        sections.get("GPU_PROCESSES", "NO_PROCESSES"),
        process_map,
    )

    server_data["gpus"] = [
        {
            "index": gpu.index,
            "name": gpu.name,
            "uuid": gpu.uuid,
            "temperature_celsius": gpu.temperature_celsius,
            "utilization_percent": gpu.utilization_percent,
            "memory": {
                "used_mb": gpu.memory.used_mb,
                "total_mb": gpu.memory.total_mb,
                "usage_percent": gpu.memory.usage_percent,
            },
            "driver_version": gpu.driver_version,
            "processes": [
                {
                    "pid": proc.pid,
                    "user": proc.user,
                    "command": proc.command,
                    "gpu_memory_mb": proc.gpu_memory_mb,
                }
                for proc in gpu.processes
            ],
        }
        for gpu in gpu_metrics
    ]

    return server_data


def collect_and_output(config: CollectorConfig, use_async: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """Collect data from all servers and return structured output."""
    if verbose:
        print(f"Collecting from {len(config.servers)} servers...")

    collector = SSHCollector(config.servers, timeout=config.timeout)

    # Collect data
    if use_async:
        try:
            results = asyncio.run(collector.collect_all_async())
        except ImportError:
            if verbose:
                print("asyncssh not available, falling back to sync mode")
            results = collector.collect_all_sync()
    else:
        results = collector.collect_all_sync()

    # Process results
    servers_data = []
    for result in results:
        if verbose:
            status = "OK" if result.success else f"FAILED: {result.error}"
            print(f"  {result.server_name}: {status}")

        server_data = process_result(result)
        servers_data.append(server_data)

    # Build output
    output = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "collector_version": __version__,
        "servers": servers_data,
    }

    return output


def save_output(data: Dict[str, Any], output_file: str, verbose: bool = False) -> None:
    """Save output to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"Output saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="GPU/CPU Monitor Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output',
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (overrides config)',
    )
    parser.add_argument(
        '--async',
        dest='use_async',
        action='store_true',
        help='Use async SSH (requires asyncssh)',
    )
    parser.add_argument(
        '--stdout',
        action='store_true',
        help='Print JSON to stdout instead of file',
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )

    args = parser.parse_args()

    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Override output file if specified
    if args.output:
        config.output_file = args.output

    # Collect data
    data = collect_and_output(config, use_async=args.use_async, verbose=args.verbose)

    # Output
    if args.stdout:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        save_output(data, config.output_file, verbose=args.verbose)


if __name__ == "__main__":
    main()
