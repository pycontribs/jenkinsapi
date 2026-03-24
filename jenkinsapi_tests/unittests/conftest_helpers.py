"""Helper utilities for Docker test fixtures."""

import socket
import logging
from typing import Tuple

log = logging.getLogger(__name__)


def find_free_port(start_port: int = 8100) -> int:
    """
    Find a free port starting from start_port.

    Args:
        start_port: Starting port to search from

    Returns:
        First available port found
    """
    port = start_port
    max_attempts = 100
    for _ in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            sock.close()
            log.debug(f"Found free port: {port}")
            return port
        except OSError:
            port += 1
    raise RuntimeError(
        f"Could not find a free port starting from {start_port}"
    )


def parse_worker_id(worker_id: str) -> Tuple[int, str]:
    """
    Parse pytest-xdist worker_id to extract worker number and display name.

    Args:
        worker_id: pytest-xdist worker identifier (e.g., "gw0", "gw1", "master")

    Returns:
        Tuple of (worker_num: int, display_name: str)
        - worker_num: 0 for master, 0+ for xdist workers
        - display_name: "master" or "worker-0", "worker-1", etc.
    """
    if worker_id == "master":
        return 0, "master"

    # Extract number from worker_id (e.g., "gw0" -> 0, "gw1" -> 1)
    try:
        if "gw" in worker_id:
            worker_num = int(worker_id.split("gw")[1])
            return worker_num, f"worker-{worker_num}"
    except (IndexError, ValueError):
        pass

    # Fallback: use worker_id as-is
    log.warning(
        f"Could not parse worker_id '{worker_id}', using as display name"
    )
    return 0, worker_id


def generate_container_name(
    worker_id: str, base_name: str = "jenkinsapi-test"
) -> str:
    """
    Generate unique container name based on worker_id.

    Args:
        worker_id: pytest-xdist worker identifier
        base_name: Base name for the container

    Returns:
        Unique container name
    """
    _, display_name = parse_worker_id(worker_id)
    if display_name == "master":
        return base_name
    return f"{base_name}-{display_name}"
