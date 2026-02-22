#!/usr/bin/env python3
"""Update Jenkins plugins to latest available versions."""

import urllib.request
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_URL_SCHEMES = {"http", "https"}


def _validate_url_scheme(url):
    """Allow only HTTP(S) URLs."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")


def fetch_update_center():
    """Fetch Jenkins Update Center data."""
    url = "https://updates.jenkins.io/current/update-center.json"
    _validate_url_scheme(url)

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "jenkinsapi-update-checker")
    opener = urllib.request.build_opener(
        urllib.request.HTTPHandler(),
        urllib.request.HTTPSHandler(),
    )

    try:
        with opener.open(req, timeout=30) as response:
            _validate_url_scheme(response.geturl())
            content = response.read().decode("utf-8")
            # Remove JSON wrapper
            json_content = re.sub(r"^[^{]*\{", "{", content, count=1)
            json_content = re.sub(r"\}[^}]*$", "}", json_content)
            return json.loads(json_content)
    except Exception as e:
        print(f"Error fetching update center: {e}")
        sys.exit(1)


def read_plugins():
    """Read current plugins from ci/plugins.txt."""
    plugins_file = Path("ci/plugins.txt")
    current_plugins = {}
    plugins_lines = []

    print("Reading current plugins from ci/plugins.txt...")
    with open(plugins_file, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                if ":" in line:
                    plugin_id, version = line.split(":", 1)
                    current_plugins[plugin_id] = version
            plugins_lines.append(line)

    return current_plugins, plugins_lines, plugins_file


def get_available_versions(data):
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
            if current_version != available_version:
                updates[plugin_id] = {
                    "current": current_version,
                    "available": available_version,
                }
    return updates


def apply_updates(plugins_lines, updates, plugins_file):
    """Apply plugin updates to ci/plugins.txt."""
    updated_lines = []
    for line in plugins_lines:
        if line and not line.startswith("#"):
            if ":" in line:
                plugin_id, _ = line.split(":", 1)
                if plugin_id in updates:
                    updated_lines.append(
                        f"{plugin_id}:{updates[plugin_id]['available']}"
                    )
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Write updated plugins.txt
    with open(plugins_file, "w") as f:
        f.write("\n".join(updated_lines))


def main():
    """Main function."""
    # Read current plugins
    current_plugins, plugins_lines, plugins_file = read_plugins()
    print(f"Found {len(current_plugins)} plugins\n")

    # Fetch available versions
    print("Querying Jenkins Update Center for available versions...")
    data = fetch_update_center()
    available = get_available_versions(data)
    print(f"Update center has {len(available)} plugins\n")

    # Find updates
    updates = find_updates(current_plugins, available)

    if updates:
        print("=" * 60)
        print(f"Found {len(updates)} plugin updates:")
        print("=" * 60)
        print()
        for plugin_id in sorted(updates.keys()):
            versions = updates[plugin_id]
            current = versions["current"]
            available = versions["available"]
            print(f"  {plugin_id:40} {current:30} → {available}")

        # Apply updates
        print()
        print("=" * 60)
        print("Updating ci/plugins.txt...")
        print("=" * 60)
        print()

        apply_updates(plugins_lines, updates, plugins_file)

        print(f"✓ Updated {len(updates)} plugins in ci/plugins.txt")
        print()
        print("Next steps:")
        print("  1. Review the changes: git diff ci/plugins.txt")
        print("  2. Test the new image: make docker-build")
        print("  3. Run tests: make coverage-parallel")
        print("  4. Commit and push the changes")
    else:
        print("=" * 60)
        print("All plugins are up to date!")
        print("=" * 60)


if __name__ == "__main__":
    main()
