#!/usr/bin/env python3
"""
save_map.py - Call SLAM Toolbox save_map service and optionally copy result into package.

Usage:
  ros2 run robot_bringup save_map.py [map_name_or_custom_path]

Examples:
  ros2 run robot_bringup save_map.py my_room
    -> Saves to ~/robot_maps/my_room/map.yaml
    -> Copies to src/robot_bringup/maps/my_room/map.yaml

  ros2 run robot_bringup save_map.py /home/user/custom/path/map_name
    -> Saves directly to /home/user/custom/path/map_name.yaml (no copy to package)
"""

import os
import sys
import subprocess
import shutil


def save_map(target: str) -> bool:
    # Check if the user specified an absolute, relative, or home-relative path
    is_custom_path = "/" in target or target.startswith(".") or target.startswith("~")

    if is_custom_path:
        expanded_target = os.path.expanduser(target)
        if os.path.isdir(expanded_target):
            source_dir = expanded_target
            file_prefix = "map"
        else:
            source_dir = os.path.dirname(expanded_target)
            file_prefix = os.path.basename(expanded_target)
            if file_prefix.endswith(".yaml"):
                file_prefix = file_prefix[:-5]
            if not file_prefix:
                file_prefix = "map"
        
        yaml_name = f"{file_prefix}.yaml"
        pgm_name = f"{file_prefix}.pgm"
    else:
        # Standard workflow: saved under ~/robot_maps/<map_name>/map.yaml
        home_dir = os.path.expanduser("~")
        source_dir = os.path.join(home_dir, "robot_maps", target)
        file_prefix = "map"
        yaml_name = "map.yaml"
        pgm_name = "map.pgm"

    # Ensure target directory exists
    os.makedirs(source_dir, exist_ok=True)
    save_path = os.path.join(source_dir, file_prefix)

    print(f"Calling SLAM save_map service with prefix: {save_path}")
    result = subprocess.run(
        [
            "ros2", "service", "call", "/slam_toolbox/save_map",
            "slam_toolbox/srv/SaveMap",
            f"name: '{save_path}'",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Failed to call save_map service: {result.stderr}")
        return False

    print(result.stdout)

    yaml_src = os.path.join(source_dir, yaml_name)
    pgm_src = os.path.join(source_dir, pgm_name)

    if not os.path.exists(yaml_src) or not os.path.exists(pgm_src):
        print(f"Map files not found. Expected:")
        print(f"  YAML: {yaml_src}")
        print(f"  PGM:  {pgm_src}")
        return False

    print(f"[OK] Map successfully saved to: {source_dir}")
    print(f"  YAML: {yaml_src}")
    print(f"  PGM:  {pgm_src}")

    # Copy to package maps directory only for the standard simple name workflow
    if not is_custom_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pkg_share = os.path.dirname(script_dir)
        pkg_dest_dir = os.path.join(pkg_share, "maps", target)
        os.makedirs(pkg_dest_dir, exist_ok=True)

        shutil.copy2(yaml_src, os.path.join(pkg_dest_dir, "map.yaml"))
        shutil.copy2(pgm_src, os.path.join(pkg_dest_dir, "map.pgm"))
        print(f"[INFO] Copied to package share directory: {pkg_dest_dir}")

    return True


def main() -> int:
    # Use timestamp if no argument is provided to prevent overwriting/overlapping maps
    default_target = "my_room"
    target = sys.argv[1] if len(sys.argv) > 1 else default_target
    ok = save_map(target)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
