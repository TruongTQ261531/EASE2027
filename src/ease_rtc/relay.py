"""An ephemeral TURN/TCP relay restricted to loopback peers; no Internet relay route."""

import os
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from ease_rtc.io import sha256


@contextmanager
def local_turn(relay_ports: tuple[int, int] | None = None, relay_ip: str = "127.0.0.1"):
    prefix = Path(os.environ.get("EASE_TURN_PREFIX", "/workspace/.local/ease-turn/root"))
    binary = shutil.which("turnserver") or str(prefix / "usr/bin/turnserver")
    if not Path(binary).is_file():
        raise RuntimeError("coturn missing: install coturn or run bash scripts/setup_cloud.sh")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    credential = secrets.token_urlsafe(24)
    with tempfile.TemporaryDirectory(prefix="ease-turn-") as directory:
        base = Path(directory)
        config = base / "turn.conf"
        config.write_text(
            "\n".join(
                [
                    "listening-ip=127.0.0.1",
                    f"relay-ip={relay_ip}",
                    f"listening-port={port}",
                    "no-udp",
                    "no-tls",
                    "no-dtls",
                    "no-cli",
                    "no-multicast-peers",
                    "allow-loopback-peers",
                    "denied-peer-ip=0.0.0.0-255.255.255.255",
                    "denied-peer-ip=::-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
                    "allowed-peer-ip=127.0.0.1",
                    f"allowed-peer-ip={relay_ip}",
                    "lt-cred-mech",
                    "realm=ease.local",
                    f"user=pilot:{credential}",
                    "relay-threads=1",
                    "no-dynamic-ip-list",
                    "no-auth-pings",
                    f"pidfile={base / 'turn.pid'}",
                    "log-file=stdout",
                ]
                + (
                    [f"min-port={relay_ports[0]}", f"max-port={relay_ports[1]}"]
                    if relay_ports is not None
                    else []
                )
            )
            + "\n"
        )
        config.chmod(0o600)
        env = os.environ.copy()
        libraries = prefix / "usr/lib/x86_64-linux-gnu"
        if Path(binary).is_relative_to(prefix) and libraries.is_dir():
            env["LD_LIBRARY_PATH"] = str(libraries) + (
                ":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else ""
            )
        with (base / "turn.log").open("w") as log:
            process = subprocess.Popen(
                [binary, "-c", str(config)], stdout=log, stderr=subprocess.STDOUT, env=env
            )
            try:
                deadline = time.monotonic() + 8
                while True:
                    if process.poll() is not None:
                        raise RuntimeError(
                            "Local coturn exited before startup; inspect coturn installation"
                        )
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Local coturn startup timed out") from None
                        time.sleep(0.1)
                yield (
                    {
                        "iceServers": [
                            {
                                "urls": f"turn:127.0.0.1:{port}?transport=tcp",
                                "username": "pilot",
                                "credential": credential,
                            }
                        ],
                        "iceTransportPolicy": "relay",
                    },
                    sha256(Path(binary)),
                )
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
