# Research Server Monitor

NTUST HISLab 實驗室伺服器監控測試系統，伺服器 GPU、CPU、記憶體、磁碟使用狀況，通過 GitHub Pages 提供公網訪問。

**線上訪問**: https://orientonubo.github.io/gpu-monitor/

[English](README.md)

## 功能特性

### 監控功能
- **GPU 監控**: 溫度、使用率、顯存、運行中的進程
- **系統監控**: CPU 使用率、記憶體用量、磁碟空間
- **多伺服器**: 同時監控多台伺服器，並行 SSH 收集
- **自動更新**: 每分鐘自動收集數據並推送到 GitHub
- **連接重試**: SSH 連接失敗自動重試 3 次

### 前端功能
- **深色/淺色主題**: 一鍵切換，自動記憶偏好
- **收起/展開**: 點擊伺服器標題可收起詳情，支持全部收起
- **歷史圖表**: 查看 CPU/Memory/Disk 和每張 GPU 的歷史趨勢
- **進程記錄**: 顯示 GPU 上運行過的進程歷史
- **響應式設計**: 支持桌面端和手機端瀏覽
- **離線提醒**: 伺服器離線時醒目顯示

### 部署
- **公網訪問**: 通過 GitHub Pages 托管，無需校內網
- **自動部署**: 推送後自動更新網站

## 架構

```
┌─────────────────┐     SSH      ┌─────────────────┐
│  Research       │◄────────────►│  Collector      │
│  Servers        │   (並行)      │  (本機 cron)     │
│  - DDC node0    │              │                 │
│  - DDC node1    │              │  python -m      │
│  - ASUS H100    │              │  collector.main │
└─────────────────┘              └────────┬────────┘
                                          │ git push
                                          ▼
                                 ┌─────────────────┐
                                 │  GitHub Pages   │
                                 │  (公網訪問)      │
                                 │                 │
                                 │  status.json    │
                                 │  index.html     │
                                 └─────────────────┘
```

## 目錄結構

```
.
├── collector/              # Python 數據收集模組
│   ├── __init__.py
│   ├── main.py            # 入口點
│   ├── config.py          # 配置載入
│   ├── ssh_client.py      # SSH 並行收集
│   ├── commands.py        # Shell 命令定義
│   ├── requirements.txt   # Python 依賴
│   └── parsers/           # 數據解析器
│       ├── cpu.py
│       ├── memory.py
│       ├── disk.py
│       ├── gpu.py
│       └── process.py
│
├── docs/                   # GitHub Pages 網站
│   ├── index.html         # 主頁面（即時監控）
│   ├── history.html       # 歷史圖表頁面
│   └── data/
│       ├── status.json    # 即時監控數據
│       └── history.json   # 歷史數據（7天滾動）
│
├── scripts/
│   └── cron_collect.sh    # Cron 定時任務腳本
│
├── logs/                   # 日誌目錄
│   └── cron.log
│
├── .github/workflows/
│   └── static.yml         # GitHub Pages 部署
│
├── servers.example.json   # 伺服器配置範例
└── README.md
```

## 安裝與配置

### 1. 克隆專案

```bash
git clone git@github.com:OrientoNubo/gpu-monitor.git
cd gpu-monitor
```

### 2. 創建 Python 虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r collector/requirements.txt
```

### 3. 配置伺服器列表

創建配置文件（**不要提交到 Git**）：

```bash
mkdir -p ~/.config/gpu-monitor
cp servers.example.json ~/.config/gpu-monitor/servers.json
```

編輯 `~/.config/gpu-monitor/servers.json`：

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

### 4. 配置 SSH 認證

**方式一：SSH 密鑰（推薦）**

```bash
# 生成密鑰（如果還沒有）
ssh-keygen -t ed25519

# 複製公鑰到目標伺服器
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
```

**方式二：密碼認證**

在配置中使用 `password_env` 指定環境變量名稱，然後設置環境變量：

```bash
export SSH_PASSWORD="your_password"
```

### 5. 測試收集

```bash
source venv/bin/activate
python -m collector.main --verbose
```

成功後會在 `docs/data/status.json` 生成數據。

### 6. 配置 Cron 定時任務

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每分鐘執行一次）
* * * * * SSH_KEY_PASSPHRASE="your_passphrase" /home/nubo/workspace/GPU_status_monitor_ssh/scripts/cron_collect.sh >> /home/nubo/workspace/GPU_status_monitor_ssh/logs/cron.log 2>&1
```

**注意**: 修改路徑為你的實際路徑。

### 7. 啟用 GitHub Pages

1. 進入 GitHub 倉庫 Settings → Pages
2. Source 選擇 "GitHub Actions"
3. 等待部署完成

## 環境變量

| 變量名 | 說明 |
|--------|------|
| `SSH_KEY_PASSPHRASE` | SSH 私鑰密碼（如果有） |
| `SSH_PASSWORD` | SSH 密碼（如果使用密碼認證） |
| `GPU_MONITOR_CONFIG` | 自定義配置文件路徑（可選） |

## 手動操作

### 手動收集數據

```bash
cd /path/to/gpu-monitor
source venv/bin/activate
python -m collector.main --verbose
```

### 手動推送到 GitHub

```bash
git add docs/data/
git commit -m "Manual update"
git push
```

### 查看 Cron 日誌

```bash
tail -f logs/cron.log
```

### 查看當前 Cron 任務

```bash
crontab -l
```

## 數據格式

`docs/data/status.json` 結構：

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
        "disks": [
          {
            "device": "/dev/nvme0n1p2",
            "mount_point": "/",
            "total_bytes": 2014574526464,
            "used_bytes": 212569665536,
            "usage_percent": 10.6
          }
        ]
      },
      "gpus": [
        {
          "index": 0,
          "name": "NVIDIA RTX 6000 Ada Generation",
          "temperature_celsius": 40,
          "utilization_percent": 0,
          "memory": {
            "used_mb": 15,
            "total_mb": 49140,
            "usage_percent": 0.0
          },
          "driver_version": "580.95.05",
          "processes": []
        }
      ]
    }
  ]
}
```

## 故障排除

### Cron 不執行

1. 檢查 cron 服務狀態：`systemctl status cron`
2. 檢查 cron 日誌：`grep CRON /var/log/syslog`
3. 確保腳本有執行權限：`chmod +x scripts/cron_collect.sh`

### SSH 連接失敗

1. 手動測試 SSH：`ssh user@server`
2. 檢查密鑰權限：`chmod 600 ~/.ssh/id_ed25519`
3. 確保 `known_hosts` 已添加目標伺服器

### GitHub Push 失敗

1. 確保 SSH 密鑰已添加到 GitHub
2. 檢查倉庫寫入權限
3. 查看錯誤日誌：`tail logs/cron.log`

### 頁面不更新

1. 檢查 GitHub Actions 是否成功
2. 強制刷新瀏覽器：Ctrl+Shift+R
3. 檢查 `docs/data/status.json` 時間戳

## 技術棧

- **後端**: Python 3, Paramiko (SSH), Pexpect
- **前端**: 純 HTML/CSS/JavaScript（無框架），Chart.js（圖表）
- **部署**: GitHub Pages + GitHub Actions
- **定時任務**: Linux Cron

## 頁面預覽

### 主頁面
- 雙欄佈局顯示所有伺服器
- 即時 CPU/Memory/Disk 和 GPU 狀態
- 點擊標題收起/展開詳情
- 右上角切換深色/淺色主題

### 歷史頁面
- 選擇伺服器和時間範圍（1H/6H/24H/7D）
- System Metrics：CPU、Memory、Disk 趨勢圖
- 每張 GPU：使用率、溫度、顯存趨勢圖
- 顯示該時段內運行過的進程記錄

## License

MIT License

---

**NTUST HISLab 3DVis** | National Taiwan University of Science and Technology
