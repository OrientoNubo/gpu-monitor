"""Batch commands for collecting system and GPU metrics."""

# Combined command - single SSH execution to get all data
# This solves the N+1 query problem by getting everything in one shot
COMBINED_COMMAND = r"""
echo '===HOSTNAME==='
hostname

echo '===TIMESTAMP==='
date -Iseconds

echo '===UPTIME==='
uptime -s 2>/dev/null || echo 'N/A'

echo '===CPU_STAT==='
cat /proc/stat | head -1

echo '===CPU_INFO==='
grep -c ^processor /proc/cpuinfo 2>/dev/null || echo '0'

echo '===MEMORY==='
cat /proc/meminfo | grep -E '^(MemTotal|MemAvailable|MemFree|Buffers|Cached|SwapTotal|SwapFree):'

echo '===DISK==='
df -B1 --output=source,size,used,avail,target 2>/dev/null | grep -E '^/dev/' || df -k | grep -E '^/dev/'

echo '===GPU_INFO==='
nvidia-smi --query-gpu=index,name,uuid,temperature.gpu,utilization.gpu,memory.used,memory.total,driver_version --format=csv,noheader,nounits 2>/dev/null || echo 'NO_GPU'

echo '===GPU_PROCESSES==='
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_gpu_memory --format=csv,noheader,nounits 2>/dev/null || echo 'NO_PROCESSES'

echo '===ALL_PROCESSES==='
ps -eo pid,user,comm --no-headers 2>/dev/null

echo '===END==='
"""


def parse_sections(output: str) -> dict:
    """Parse the combined command output into sections."""
    sections = {}
    current_section = None
    current_lines = []

    for line in output.split('\n'):
        line = line.rstrip()

        if line.startswith('===') and line.endswith('==='):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_lines)

            # Start new section
            current_section = line.strip('=')
            current_lines = []
        elif current_section:
            current_lines.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_lines)

    return sections
