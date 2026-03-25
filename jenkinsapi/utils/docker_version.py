"""
Docker image versioning based on Dockerfile and plugins configuration.

Generates consistent image version tags based on content hashes of
Dockerfile and plugins.txt. Only rebuilds when these files change.
"""

import os
import hashlib
from typing import Tuple


def calculate_image_version(
    dockerfile_path: str, plugins_path: str = None
) -> str:
    """
    Calculate image version hash from Dockerfile and plugins.txt.

    Args:
        dockerfile_path: Path to Dockerfile
        plugins_path: Path to plugins.txt (optional)

    Returns:
        Short hash (first 8 chars of SHA256) for use in image tags
    """
    hasher = hashlib.sha256()

    # Hash Dockerfile content
    if not os.path.exists(dockerfile_path):
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")

    with open(dockerfile_path, "rb") as f:
        hasher.update(f.read())

    # Hash plugins.txt if provided
    if plugins_path and os.path.exists(plugins_path):
        with open(plugins_path, "rb") as f:
            hasher.update(f.read())

    full_hash = hasher.hexdigest()
    short_hash = full_hash[:8]
    return short_hash


def get_image_tags(
    base_image: str = "jenkinsapi",
    dockerfile_path: str = "Dockerfile",
    plugins_path: str = None,
) -> Tuple[str, str, str]:
    """
    Get image tags for building and tagging.

    Args:
        base_image: Base image name (e.g., 'jenkinsapi')
        dockerfile_path: Path to Dockerfile
        plugins_path: Path to plugins.txt (optional)

    Returns:
        Tuple of (versioned_tag, latest_tag, registry_tag)
        Example: ('jenkinsapi:abc12345', 'jenkinsapi:latest', 'ghcr.io/owner/jenkinsapi:abc12345')
    """
    version = calculate_image_version(dockerfile_path, plugins_path)
    versioned_tag = f"{base_image}:{version}"
    latest_tag = f"{base_image}:latest"
    return versioned_tag, latest_tag, version
