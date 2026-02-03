#!/usr/bin/env python3
"""Check for available Jenkins plugin updates from the Update Center."""

import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def fetch_update_center():
    """Fetch Jenkins Update Center data."""
    url = "https://updates.jenkins.io/current/update-center.json"
    # Validate URL scheme for security
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "jenkinsapi-update-checker")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode("utf-8")
            # Remove JSON wrapper
            json_content = re.sub(r"^[^{]*\{", "{", content, count=1)
            json_content = re.sub(r"\}[^}]*$", "}", json_content)
            return json.loads(json_content)
    except Exception as e:
        print(f"Error fetching update center: {e}")
        sys.exit(1)


def read_current_plugins():
    """Read current plugins from ci/plugins.txt."""
    plugins_file = Path("ci/plugins.txt")
    current_plugins = {}

    with open(plugins_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if ":" in line:
                    plugin_id, version = line.split(":", 1)
                    current_plugins[plugin_id] = version
                else:
                    current_plugins[line] = None

    return current_plugins


def extract_available_versions(data):
    """Extract available plugin versions from update center."""
    available = {}
    if "plugins" in data:
        for plugin_id, plugin_info in data["plugins"].items():
            if "version" in plugin_info:
                available[plugin_id] = plugin_info["version"]
    return available


def find_updates(current_plugins, available):
    """Find plugins that have available updates."""
    updates = {}
    for plugin_id, current_version in current_plugins.items():
        if plugin_id in available:
            available_version = available[plugin_id]
            if current_version and current_version != available_version:
                updates[plugin_id] = {
                    "current": current_version,
                    "available": available_version,
                }
    return updates


def save_updates(updates):
    """Save updates to temporary file for next step."""
    temp_dir = tempfile.gettempdir()
    updates_file = Path(temp_dir) / "updates.json"
    updates_found_file = Path(temp_dir) / "updates_found.txt"

    with open(updates_file, "w") as f:
        json.dump(updates, f, indent=2)

    updates_found = "true" if updates else "false"
    with open(updates_found_file, "w") as f:
        f.write(updates_found)

    return updates_found == "true"


def main():
    """Main function."""
    current_plugins = read_current_plugins()
    print(f"Checking {len(current_plugins)} plugins for updates...")

    data = fetch_update_center()
    available = extract_available_versions(data)
    print(f"Found {len(available)} plugins in update center")

    updates = find_updates(current_plugins, available)

    if updates:
        print(f"\nFound {len(updates)} plugin updates:")
        for plugin_id in sorted(updates.keys()):
            versions = updates[plugin_id]
            print(
                f"  {plugin_id}: {versions['current']} → {versions['available']}"
            )

    has_updates = save_updates(updates)

    if has_updates:
        print("\n✓ Updates found and saved")
    else:
        print("\nNo plugin updates available")

    # Output for GitHub Actions
    print(f"::set-output name=updates-found::{str(has_updates).lower()}")


if __name__ == "__main__":
    main()
