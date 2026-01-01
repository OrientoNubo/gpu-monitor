# Research Server Monitor

A server monitoring system for NTUST HISLab, tracking GPU, CPU, memory, and disk usage via SSH. Hosted on GitHub Pages for public access.

**Live Demo**: https://orientonubo.github.io/gpu-monitor/

[中文版](README_CN.md)

## Features

### Monitoring
- **GPU Monitoring**: Temperature, utilization, VRAM, running processes
- **System Monitoring**: CPU usage, memory usage, disk space
- **Multi-Server**: Monitor multiple servers with parallel SSH collection
- **Auto Update**: Collect and push data to GitHub every minute
- **Retry Logic**: Auto-retry SSH connections up to 3 times on failure

### Frontend
- **Dark/Light Theme**: One-click toggle with preference persistence
- **Collapse/Expand**: Click server header to collapse details
- **History Charts**: View CPU/Memory/Disk and per-GPU trends
- **Process History**: Display GPU process records over time
- **Responsive Design**: Desktop and mobile friendly
- **Offline Alert**: Prominent display when servers are offline

### Deployment
- **Public Access**: Hosted on GitHub Pages, no VPN needed
- **Auto Deploy**: Website updates automatically on push

## Architecture

```
┌─────────────────┐     SSH      ┌─────────────────┐
│  Research       │◄────────────►│  Collector      │
│  Servers        │  (parallel)  │  (local cron)   │
│  - DDC node0    │              │                 │
│  - DDC node1    │              │  python -m      │
│  - ASUS H100    │              │  collector.main │
└─────────────────┘              └────────┬────────┘
                                          │ git push
                                          ▼
                                 ┌─────────────────┐
                                 │  GitHub Pages   │
                                 │  (public)       │
                                 │                 │
                                 │  status.json    │
                                 │  index.html     │
                                 └─────────────────┘
```

## Directory Structure

```
.
├── collector/              # Python data collection module
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration loader
│   ├── ssh_client.py      # Parallel SSH collection
│   ├── commands.py        # Shell command definitions
│   ├── requirements.txt   # Python dependencies
│   └── parsers/           # Data parsers
│       ├── cpu.py
│       ├── memory.py
│       ├── disk.py
│       ├── gpu.py
│       └── process.py
│
├── docs/                   # GitHub Pages website
│   ├── index.html         # Main page (live monitoring)
│   ├── history.html       # History charts page
│   └── data/
│       ├── status.json    # Live monitoring data
│       └── history.json   # Historical data (7-day rolling)
│
├── scripts/
│   └── cron_collect.sh    # Cron job script
│
├── logs/                   # Log directory
│   └── cron.log
│
├── .github/workflows/
│   └── static.yml         # GitHub Pages deployment
│
├── servers.example.json   # Server configuration example
├── README.md              # English documentation
└── README_CN.md           # Chinese documentation
```

## Installation & Configuration

### 1. Clone the Repository

```bash
git clone git@github.com:OrientoNubo/gpu-monitor.git
cd gpu-monitor
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r collector/requirements.txt
```

### 3. Configure Server List

Create config file (**do NOT commit to Git**):

```bash
mkdir -p ~/.config/gpu-monitor
cp servers.example.json ~/.config/gpu-monitor/servers.json
```

Edit `~/.config/gpu-monitor/servers.json`:

```json
{
  "servers": [
    {
      "name": "Server 1",
      "host": "192.168.1.100",
      "port": 22,
      "username": "your_username",
      "auth": {
        "type": "key",
        "key_path": "~/.ssh/id_ed25519",
        "passphrase_env": "SSH_KEY_PASSPHRASE"
      }
    },
    {
      "name": "Server 2",
      "host": "192.168.1.101",
      "port": 22,
      "username": "your_username",
      "auth": {
        "type": "password",
        "password_env": "SSH_PASSWORD"
      }
    }
  ]
}
```

### 4. Configure SSH Authentication

**Option 1: SSH Key (Recommended)**

```bash
# Generate key (if not exists)
ssh-keygen -t ed25519

# Copy public key to target server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
```

**Option 2: Password Authentication**

Use `password_env` in config to specify environment variable name:

```bash
export SSH_PASSWORD="your_password"
```

### 5. Test Collection

```bash
source venv/bin/activate
python -m collector.main --verbose
```

On success, data will be generated at `docs/data/status.json`.

### 6. Configure Cron Job

```bash
# Edit crontab
crontab -e

# Add following line (runs every minute)
* * * * * SSH_KEY_PASSPHRASE="your_passphrase" /path/to/scripts/cron_collect.sh >> /path/to/logs/cron.log 2>&1
```

**Note**: Replace paths with your actual paths.

### 7. Enable GitHub Pages

1. Go to GitHub repo Settings → Pages
2. Source: select "GitHub Actions"
3. Wait for deployment

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SSH_KEY_PASSPHRASE` | SSH private key passphrase (if any) |
| `SSH_PASSWORD` | SSH password (if using password auth) |
| `GPU_MONITOR_CONFIG` | Custom config file path (optional) |

## Manual Operations

### Manual Data Collection

```bash
cd /path/to/gpu-monitor
source venv/bin/activate
python -m collector.main --verbose
```

### Manual Push to GitHub

```bash
git add docs/data/
git commit -m "Manual update"
git push
```

### View Cron Logs

```bash
tail -f logs/cron.log
```

### List Current Cron Jobs

```bash
crontab -l
```

## Data Format

`docs/data/status.json` structure:

```json
{
  "timestamp": "2025-12-31T12:00:00+08:00",
  "collector_version": "2.0.0",
  "servers": [
    {
      "name": "Server Name",
      "host": "192.168.1.100",
      "hostname": "actual-hostname",
      "status": "online",
      "system": {
        "cpu": { "usage_percent": 15.2, "cores": 32 },
        "memory": {
          "total_bytes": 540322783232,
          "used_bytes": 165695700992,
          "usage_percent": 30.7
        },
        "disks": [...]
      },
      "gpus": [
        {
          "index": 0,
          "name": "NVIDIA RTX 6000 Ada Generation",
          "temperature_celsius": 40,
          "utilization_percent": 0,
          "memory": { "used_mb": 15, "total_mb": 49140, "usage_percent": 0.0 },
          "driver_version": "580.95.05",
          "processes": []
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Cron Not Running

1. Check cron service: `systemctl status cron`
2. Check cron logs: `grep CRON /var/log/syslog`
3. Ensure script is executable: `chmod +x scripts/cron_collect.sh`

### SSH Connection Failed

1. Test SSH manually: `ssh user@server`
2. Check key permissions: `chmod 600 ~/.ssh/id_ed25519`
3. Ensure target server is in `known_hosts`

### GitHub Push Failed

1. Ensure SSH key is added to GitHub
2. Check repository write permissions
3. View error logs: `tail logs/cron.log`

### Page Not Updating

1. Check GitHub Actions status
2. Hard refresh browser: Ctrl+Shift+R
3. Check `docs/data/status.json` timestamp

## Tech Stack

- **Backend**: Python 3, Paramiko (SSH), Pexpect
- **Frontend**: Pure HTML/CSS/JavaScript, Chart.js
- **Deployment**: GitHub Pages + GitHub Actions
- **Scheduling**: Linux Cron

## Page Preview

### Main Page
- Two-column layout for all servers
- Real-time CPU/Memory/Disk and GPU status
- Click header to collapse/expand details
- Theme toggle in top-right corner

### History Page
- Select server and time range (1H/6H/24H/7D)
- System Metrics: CPU, Memory, Disk trend charts
- Per-GPU: Utilization, Temperature, VRAM charts
- Process history within selected time range

## License

MIT License

---

**NTUST HISLab 3DVis** | National Taiwan University of Science and Technology
