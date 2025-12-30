#!/usr/bin/env python3
import json
import paramiko
from datetime import datetime
import sys
import os

CONFIG_FILE = os.path.expanduser('./gpu_servers.json')


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)


def ssh_connect(server):
    """建立 SSH 连接"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        connect_kwargs = {
            'hostname': server['host'],
            'username': server['user'],
            'timeout': 15,
            'banner_timeout': 30
        }

        if server['auth_type'] == 'password':
            connect_kwargs['password'] = server['password']
            connect_kwargs['allow_agent'] = False
            connect_kwargs['look_for_keys'] = False

        elif server['auth_type'] == 'key':
            key_file = os.path.expanduser(server['key_file'])

            if not os.path.exists(key_file):
                print(f"  ✗ Key file not found: {key_file}")
                return None

            connect_kwargs['key_filename'] = key_file

            if 'passphrase' in server and server['passphrase']:
                connect_kwargs['passphrase'] = server['passphrase']

            connect_kwargs['allow_agent'] = False
            connect_kwargs['look_for_keys'] = False
        else:
            raise ValueError(f"Unknown auth_type: {server['auth_type']}")

        ssh.connect(**connect_kwargs)
        return ssh

    except Exception as e:
        print(
            f"  ✗ Connection error for {server.get('name', server['host'])}: {e}")
        return None


def exec_command(ssh, command):
    """执行远程命令"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8').strip()

        return output if exit_status == 0 else ""
    except Exception:
        return ""


def get_gpu_status(server):
    """获取单个服务器的 GPU 状态"""
    server_name = server.get('name', server['host'])

    print(f"Collecting from {server_name}...")

    ssh = ssh_connect(server)
    if not ssh:
        # 连接失败时的显示格式
        if 'name' in server and server['name']:
            display_name = f"{server['name']} ({server['host']})"
        else:
            display_name = server['host']
        return f"{display_name:<40} Connection failed"

    try:
        # 获取实际主机名
        actual_hostname = exec_command(ssh, 'hostname')

        # 构建显示名称
        if 'name' in server and server['name']:
            # 如果配置中有 name，格式为 "name (实际主机名)"
            display_name = f"{server['name']} ({actual_hostname})"
        else:
            # 如果没有 name，直接使用主机名
            display_name = actual_hostname or server['host']

        # 获取远程服务器时间
        remote_time = exec_command(ssh, 'date "+%a %b %d %H:%M:%S %Y"')
        if not remote_time:
            remote_time = datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        # 获取驱动版本
        driver_version = exec_command(ssh,
                                      'nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1')

        # 第一行：服务器信息（左对齐40字符，增加宽度以容纳更长的名称）
        output = [f"{display_name:<40} {remote_time}  {driver_version}"]

        # 获取 GPU 基本信息
        gpu_info = exec_command(ssh,
                                'nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null')

        if not gpu_info:
            ssh.close()
            return f"{display_name:<40} No GPU found"

        # 获取进程信息
        process_info = exec_command(ssh,
                                    'nvidia-smi --query-compute-apps=gpu_uuid,pid,used_gpu_memory --format=csv,noheader,nounits 2>/dev/null')

        # 获取 GPU UUID 映射
        uuid_map_raw = exec_command(ssh,
                                    'nvidia-smi --query-gpu=index,gpu_uuid --format=csv,noheader 2>/dev/null')

        uuid_map = {}
        for line in uuid_map_raw.split('\n'):
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 2:
                    uuid_map[parts[1].strip()] = parts[0].strip()

        # 收集每个 GPU 的进程
        gpu_processes = {}

        if process_info:
            for proc_line in process_info.split('\n'):
                if proc_line.strip():
                    parts = [p.strip() for p in proc_line.split(',')]
                    if len(parts) >= 3:
                        gpu_uuid = parts[0]
                        pid = parts[1]
                        mem = parts[2]

                        gpu_idx = uuid_map.get(gpu_uuid, '?')

                        # 获取用户名和程序名
                        username = exec_command(
                            ssh, f'ps -o user= -p {pid} 2>/dev/null') or "unknown"
                        cmdname = exec_command(
                            ssh, f'ps -o comm= -p {pid} 2>/dev/null') or "unknown"

                        proc_info = f"{username}:{cmdname}/{pid}({mem}M)"

                        if gpu_idx not in gpu_processes:
                            gpu_processes[gpu_idx] = []
                        gpu_processes[gpu_idx].append(proc_info)

        # 格式化输出每个 GPU
        for line in gpu_info.split('\n'):
            if line.strip():
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    idx = parts[0]
                    name = parts[1]
                    temp = parts[2]
                    util = parts[3]
                    mem_used = parts[4]
                    mem_total = parts[5]

                    gpu_line = (f"[{idx}] {name:<26} | "
                                f"{int(temp):>2}'C, "
                                f"{int(util):>3} % | "
                                f"{int(mem_used):>5} / {int(mem_total):>5} MB |")

                    # 添加进程信息
                    if idx in gpu_processes:
                        gpu_line += " " + " ".join(gpu_processes[idx])

                    output.append(gpu_line)

        ssh.close()
        return '\n'.join(output)

    except Exception as e:
        ssh.close()
        display_name = server.get('name', server['host'])
        return f"{display_name:<40} Error: {e}"


def get_daily_log_filename(log_dir):
    """生成当天的日志文件名"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"gpu-status_{today}.log")


def save_to_log(content, log_dir):
    """追加内容到当天的日志文件"""
    try:
        # 确保日志目录存在
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 获取当天的日志文件名
        log_file = get_daily_log_filename(log_dir)

        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 打开日志文件（追加模式）
        with open(log_file, 'a', encoding='utf-8') as f:
            # 写入分隔线和时间戳
            f.write('\n')
            f.write('=' * 80 + '\n')
            f.write(f'Collection Time: {timestamp}\n')
            f.write('=' * 80 + '\n')
            # 写入实际内容
            f.write(content)
            f.write('\n')

        return log_file
    except Exception as e:
        print(f"⚠ Failed to save to log file: {e}")
        return None


def cleanup_old_logs(log_dir, keep_days=30):
    """清理超过指定天数的旧日志文件"""
    try:
        if not os.path.exists(log_dir):
            return

        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        for filename in os.listdir(log_dir):
            if filename.startswith('gpu-status_') and filename.endswith('.log'):
                filepath = os.path.join(log_dir, filename)

                # 检查文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

                if file_mtime < cutoff_date:
                    os.remove(filepath)
                    print(f"✓ Cleaned up old log: {filename}")
    except Exception as e:
        print(f"⚠ Failed to cleanup old logs: {e}")


def main():
    config = load_config()
    servers = config['servers']
    output_file = config.get('output_file', './gpu-status.txt')
    log_dir = config.get('log_dir', './logs')
    keep_days = config.get('keep_logs_days', 30)  # 保留30天的日志

    all_status = []

    for server in servers:
        status = get_gpu_status(server)
        all_status.append(status)

    # 整合所有状态
    combined_output = '\n\n'.join(all_status)

    # 1. 保存到当前状态文件（覆盖）
    try:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_output)
        print(f"✓ Status saved to {output_file}")
    except Exception as e:
        print(f"✗ Error writing to file: {e}")

    # 2. 追加到当天的日志文件
    log_file = save_to_log(combined_output, log_dir)
    if log_file:
        print(f"✓ Status logged to {log_file}")

    # 3. 清理旧日志（可选，每次运行时检查）
    cleanup_old_logs(log_dir, keep_days)


if __name__ == "__main__":
    main()
