"""Configuration loading with security best practices."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ServerConfig:
    """Configuration for a single server."""
    name: str
    host: str
    user: str
    port: int = 22
    key_path: Optional[str] = None
    key_passphrase: Optional[str] = None

    def __post_init__(self):
        # Expand user home directory in key path
        if self.key_path:
            self.key_path = os.path.expanduser(self.key_path)


@dataclass
class CollectorConfig:
    """Main collector configuration."""
    servers: List[ServerConfig] = field(default_factory=list)
    output_file: str = "./docs/data/status.json"
    timeout: int = 30
    ssh_key_path: Optional[str] = None
    ssh_key_passphrase: Optional[str] = None

    def __post_init__(self):
        if self.ssh_key_path:
            self.ssh_key_path = os.path.expanduser(self.ssh_key_path)


def get_config_paths() -> List[Path]:
    """Get list of possible config file paths in order of priority."""
    paths = []

    # 1. Environment variable
    env_path = os.environ.get('GPU_MONITOR_CONFIG')
    if env_path:
        paths.append(Path(env_path))

    # 2. User config directory
    paths.append(Path.home() / '.config' / 'gpu-monitor' / 'servers.json')

    # 3. Current directory (for development)
    paths.append(Path('./servers.json'))

    # 4. Legacy location (for migration)
    paths.append(Path('./gpu_servers.json'))

    return paths


def load_config() -> CollectorConfig:
    """
    Load configuration from file or environment variables.

    Priority:
    1. Environment variable GPU_MONITOR_CONFIG (path to config file)
    2. ~/.config/gpu-monitor/servers.json
    3. ./servers.json
    4. ./gpu_servers.json (legacy)

    SSH credentials:
    - SSH_KEY_PATH: Path to SSH private key
    - SSH_KEY_PASSPHRASE: Passphrase for SSH key (optional)

    Returns:
        CollectorConfig object

    Raises:
        FileNotFoundError: If no config file is found
    """
    config_data = None
    config_path = None

    # Try each config path
    for path in get_config_paths():
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            config_path = path
            break

    if config_data is None:
        raise FileNotFoundError(
            "No configuration file found. Please create one at:\n"
            "  ~/.config/gpu-monitor/servers.json\n"
            "Or set GPU_MONITOR_CONFIG environment variable."
        )

    # Get SSH key settings from environment or config
    ssh_key_path = os.environ.get('SSH_KEY_PATH') or config_data.get('ssh_key_path', '~/.ssh/id_ed25519')
    ssh_key_passphrase = os.environ.get('SSH_KEY_PASSPHRASE') or config_data.get('ssh_key_passphrase')

    # Parse servers
    servers = []
    for server_data in config_data.get('servers', []):
        server = ServerConfig(
            name=server_data.get('name', server_data.get('host')),
            host=server_data['host'],
            user=server_data.get('user', 'root'),
            port=server_data.get('port', 22),
            key_path=server_data.get('key_file') or ssh_key_path,
            key_passphrase=server_data.get('passphrase') or ssh_key_passphrase,
        )
        servers.append(server)

    return CollectorConfig(
        servers=servers,
        output_file=config_data.get('output_file', './docs/data/status.json'),
        timeout=config_data.get('timeout', 30),
        ssh_key_path=ssh_key_path,
        ssh_key_passphrase=ssh_key_passphrase,
    )


def create_example_config(path: Optional[Path] = None) -> Path:
    """Create an example configuration file."""
    if path is None:
        path = Path.home() / '.config' / 'gpu-monitor' / 'servers.json'

    path.parent.mkdir(parents=True, exist_ok=True)

    example_config = {
        "servers": [
            {
                "name": "Server-1",
                "host": "192.168.1.100",
                "user": "username",
                "port": 22
            }
        ],
        "output_file": "./docs/data/status.json",
        "timeout": 30,
        "_comment": "SSH key is read from SSH_KEY_PATH environment variable or ~/.ssh/id_ed25519"
    }

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2)

    return path
