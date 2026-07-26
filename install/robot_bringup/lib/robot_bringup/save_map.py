#!/usr/bin/env python3
"""
save_map.py - Call SLAM Toolbox save_map service and copy result into package.

Usage:
  ros2 run robot_bringup save_map.py [map_name]

Default map_name: my_room
Result saved to: ~/robot_maps/<map_name>/
Also copied to: $(rospack find robot_bringup)/maps/<map_name>/
"""

import os
import sys
import subprocess
import shutil


def save_map(map_name: str) -> bool:
    home_dir = os.path.expanduser("~")
    source_dir = os.path.join(home_dir, "robot_maps", map_name)

    os.makedirs(source_dir, exist_ok=True)

    print(f"Calling SLAM save_map service for: {map_name}")
    result = subprocess.run(
        [
            "ros2", "service", "call", "/slam_toolbox/save_map",
            "slam_toolbox/srv/SaveMap",
            f"name: '{source_dir}'",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Failed to call save_map service: {result.stderr}")
        return False

    print(result.stdout)

    yaml_src = os.path.join(source_dir, "map.yaml")
    pgm_src = os.path.join(source_dir, "map.pgm")

    if not os.path.exists(yaml_src) or not os.path.exists(pgm_src):
        print(f"Map files not found in {source_dir}")
        return False

    try:
        pkg_share = subprocess.check_output(
            ["rospack", "find", "robot_bringup"], text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        print(f"rospack failed: {exc}")
        return False

    dest_dir = os.path.join(pkg_share, "maps", map_name)
    os.makedirs(dest_dir, exist_ok=True)

    shutil.copy2(yaml_src, os.path.join(dest_dir, "map.yaml"))
    shutil.copy2(pgm_src, os.path.join(dest_dir, "map.pgm"))

    print(f"Map saved to: {dest_dir}")
    print("Contents:")
    for f in os.listdir(dest_dir):
        print(f"  {f}")

    return True


def main() -> int:
    map_name = sys.argv[1] if len(sys.argv) > 1 else "my_room"
    ok = save_map(map_name)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
