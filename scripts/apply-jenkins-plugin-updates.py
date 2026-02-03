#!/usr/bin/env python3
"""Apply Jenkins plugin updates to ci/plugins.txt."""

import json
import sys
from pathlib import Path


def read_plugins_file():
    """Read current plugins.txt file."""
    plugins_file = Path("ci/plugins.txt")
    plugins_lines = []
    current_plugins = {}

    with open(plugins_file, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if line and not line.startswith("#"):
                if ":" in line:
                    plugin_id, version = line.split(":", 1)
                    current_plugins[plugin_id] = version
            plugins_lines.append(line)

    return plugins_file, plugins_lines, current_plugins


def load_updates():
    """Load updates from check script."""
    updates_file = Path("/tmp/updates.json")
    if not updates_file.exists():
        print("Error: No updates found. Run check script first.")
        sys.exit(1)

    with open(updates_file, "r") as f:
        return json.load(f)


def apply_updates(plugins_lines, updates):
    """Apply updates to plugins lines."""
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
                # Handle unpinned plugins
                if line in updates:
                    updated_lines.append(
                        f"{line}:{updates[line]['available']}"
                    )
                else:
                    updated_lines.append(line)
        else:
            updated_lines.append(line)

    return updated_lines


def save_plugins_file(plugins_file, updated_lines):
    """Save updated plugins to ci/plugins.txt."""
    with open(plugins_file, "w") as f:
        f.write("\n".join(updated_lines))


def main():
    """Main function."""
    plugins_file, plugins_lines, current_plugins = read_plugins_file()
    updates = load_updates()

    if not updates:
        print("No updates to apply")
        return

    print(f"Applying {len(updates)} plugin updates...")

    updated_lines = apply_updates(plugins_lines, updates)
    save_plugins_file(plugins_file, updated_lines)

    print(f"✓ Updated {len(updates)} plugins in ci/plugins.txt")

    # Show what was updated
    print("\nUpdated plugins:")
    for plugin_id in sorted(updates.keys()):
        versions = updates[plugin_id]
        print(
            f"  {plugin_id}: {versions['current']} → {versions['available']}"
        )


if __name__ == "__main__":
    main()
