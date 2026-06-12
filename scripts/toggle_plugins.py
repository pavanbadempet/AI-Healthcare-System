#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

PLUGINS_DIR = Path.home() / ".gemini" / "config" / "plugins"

def get_plugin_status():
    if not PLUGINS_DIR.exists():
        print(f"Error: Plugins directory not found at {PLUGINS_DIR}")
        return []

    plugins = []
    for item in PLUGINS_DIR.iterdir():
        if item.is_dir():
            name = item.name
            if name.startswith("_") and name.endswith("_DISABLED"):
                original_name = name[1:-9]
                plugins.append({"name": original_name, "enabled": False, "dir_name": name})
            else:
                plugins.append({"name": name, "enabled": True, "dir_name": name})

    # Sort by name
    plugins.sort(key=lambda x: x["name"])
    return plugins

def print_status():
    plugins = get_plugin_status()
    if not plugins:
        return

    print("\nAntigravity Plugins Status:")
    print("-" * 50)
    print(f"{'Plugin Name':<30} | {'Status':<15}")
    print("-" * 50)
    for p in plugins:
        status_str = "ENABLED" if p["enabled"] else "DISABLED"
        print(f"{p['name']:<30} | {status_str:<15}")
    print("-" * 50)
    print(f"Plugins folder: {PLUGINS_DIR}\n")

def toggle_plugin(name, enable=True):
    plugins = get_plugin_status()
    matching = [p for p in plugins if p["name"].lower() == name.lower()]

    if not matching:
        print(f"Error: Plugin '{name}' not found.")
        return False

    plugin = matching[0]

    if enable:
        if plugin["enabled"]:
            print(f"Plugin '{plugin['name']}' is already enabled.")
            return True
        old_path = PLUGINS_DIR / plugin["dir_name"]
        new_path = PLUGINS_DIR / plugin["name"]
        try:
            old_path.rename(new_path)
            print(f"Enabled plugin '{plugin['name']}'")
            return True
        except Exception as e:
            print(f"Error enabling plugin '{plugin['name']}': {e}")
            return False
    else:
        if not plugin["enabled"]:
            print(f"Plugin '{plugin['name']}' is already disabled.")
            return True
        old_path = PLUGINS_DIR / plugin["dir_name"]
        new_path = PLUGINS_DIR / f"_{plugin['name']}_DISABLED"
        try:
            old_path.rename(new_path)
            print(f"Disabled plugin '{plugin['name']}'")
            return True
        except Exception as e:
            print(f"Error disabling plugin '{plugin['name']}': {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Toggle Antigravity plugins on/off to optimize token usage.")
    parser.add_argument("--status", action="store_true", help="Show current status of all plugins")
    parser.add_argument("--disable", nargs="+", help="Disable one or more plugins by name")
    parser.add_argument("--enable", nargs="+", help="Enable one or more plugins by name")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        print_status()
        return

    if args.status:
        print_status()

    if args.disable:
        for name in args.disable:
            toggle_plugin(name, enable=False)
        print_status()

    if args.enable:
        for name in args.enable:
            toggle_plugin(name, enable=True)
        print_status()

if __name__ == "__main__":
    main()
