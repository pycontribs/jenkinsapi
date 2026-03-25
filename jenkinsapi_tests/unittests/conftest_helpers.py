"""Helper utilities for Docker test fixtures."""

import socket
import logging
from typing import Tuple

log = logging.getLogger(__name__)


def find_free_port(start_port: int = 8100) -> int:
    port = start_port
    for _ in range(100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise RuntimeError(
        f"Could not find a free port starting from {start_port}"
    )


def parse_worker_id(worker_id: str) -> Tuple[int, str]:
    if worker_id == "master":
        return 0, "master"
    try:
        if "gw" in worker_id:
            worker_num = int(worker_id.split("gw")[1])
            return worker_num, f"worker-{worker_num}"
    except (IndexError, ValueError):
        pass
    return 0, worker_id


def generate_container_name(
    worker_id: str, base_name: str = "jenkinsapi-test"
) -> str:
    _, display_name = parse_worker_id(worker_id)
    if display_name == "master":
        return base_name
    return f"{base_name}-{display_name}"
