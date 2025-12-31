"""Async SSH client for parallel data collection."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

try:
    import asyncssh
    HAS_ASYNCSSH = True
except ImportError:
    HAS_ASYNCSSH = False

import paramiko

from .commands import COMBINED_COMMAND, parse_sections
from .config import ServerConfig


@dataclass
class CollectionResult:
    """Result from collecting data from a single server."""
    server_name: str
    host: str
    success: bool
    sections: Dict[str, str]
    error: Optional[str] = None
    collected_at: Optional[datetime] = None


class SSHCollector:
    """SSH collector with support for both sync and async execution."""

    def __init__(self, servers: List[ServerConfig], timeout: int = 30, max_retries: int = 3):
        self.servers = servers
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = 2  # seconds between retries

    def collect_all_sync(self) -> List[CollectionResult]:
        """
        Collect data from all servers using synchronous paramiko.
        Uses threading for parallel execution.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        with ThreadPoolExecutor(max_workers=len(self.servers)) as executor:
            futures = {
                executor.submit(self._collect_sync, server): server
                for server in self.servers
            }
            for future in as_completed(futures):
                results.append(future.result())

        return results

    def _collect_sync(self, server: ServerConfig) -> CollectionResult:
        """Collect data from a single server using paramiko with retry logic."""
        import time
        last_error = None

        for attempt in range(self.max_retries):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                connect_kwargs = {
                    'hostname': server.host,
                    'port': server.port,
                    'username': server.user,
                    'timeout': self.timeout,
                    'banner_timeout': self.timeout,
                    'allow_agent': False,
                    'look_for_keys': False,
                }

                if server.key_path:
                    connect_kwargs['key_filename'] = server.key_path
                    if server.key_passphrase:
                        connect_kwargs['passphrase'] = server.key_passphrase

                ssh.connect(**connect_kwargs)

                # Execute combined command
                stdin, stdout, stderr = ssh.exec_command(
                    COMBINED_COMMAND,
                    timeout=self.timeout
                )
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8')

                ssh.close()

                if exit_status != 0:
                    last_error = f"Command failed with exit status {exit_status}"
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return CollectionResult(
                        server_name=server.name,
                        host=server.host,
                        success=False,
                        sections={},
                        error=last_error,
                        collected_at=datetime.now(),
                    )

                # Parse output into sections
                sections = parse_sections(output)

                return CollectionResult(
                    server_name=server.name,
                    host=server.host,
                    success=True,
                    sections=sections,
                    collected_at=datetime.now(),
                )

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

        # All retries failed
        return CollectionResult(
            server_name=server.name,
            host=server.host,
            success=False,
            sections={},
            error=f"Failed after {self.max_retries} attempts: {last_error}",
            collected_at=datetime.now(),
        )

    async def collect_all_async(self) -> List[CollectionResult]:
        """
        Collect data from all servers using async SSH.
        Requires asyncssh package.
        """
        if not HAS_ASYNCSSH:
            raise ImportError("asyncssh is required for async collection")

        tasks = [self._collect_async(server) for server in self.servers]
        return await asyncio.gather(*tasks)

    async def _collect_async(self, server: ServerConfig) -> CollectionResult:
        """Collect data from a single server using asyncssh."""
        try:
            connect_opts = {
                'host': server.host,
                'port': server.port,
                'username': server.user,
                'known_hosts': None,
                'connect_timeout': self.timeout,
            }

            if server.key_path:
                connect_opts['client_keys'] = [server.key_path]
                if server.key_passphrase:
                    connect_opts['passphrase'] = server.key_passphrase

            async with asyncssh.connect(**connect_opts) as conn:
                result = await asyncio.wait_for(
                    conn.run(COMBINED_COMMAND),
                    timeout=self.timeout
                )

                if result.exit_status != 0:
                    return CollectionResult(
                        server_name=server.name,
                        host=server.host,
                        success=False,
                        sections={},
                        error=f"Command failed with exit status {result.exit_status}",
                        collected_at=datetime.now(),
                    )

                sections = parse_sections(result.stdout)

                return CollectionResult(
                    server_name=server.name,
                    host=server.host,
                    success=True,
                    sections=sections,
                    collected_at=datetime.now(),
                )

        except Exception as e:
            return CollectionResult(
                server_name=server.name,
                host=server.host,
                success=False,
                sections={},
                error=str(e),
                collected_at=datetime.now(),
            )
