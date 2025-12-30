#!/usr/bin/env python3
import time
import subprocess
import sys

SCRIPT_PATH = './collect_gpu_status.py'
INTERVAL = 10  # 秒


def main():
    print(f"GPU Monitor Daemon started. Update interval: {INTERVAL}s")
    print("Press Ctrl+C to stop")

    while True:
        try:
            print(
                f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running collector...")
            subprocess.run([sys.executable, SCRIPT_PATH])
            print(f"Sleeping for {INTERVAL} seconds...")
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\nDaemon stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
