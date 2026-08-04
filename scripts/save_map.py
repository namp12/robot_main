#!/usr/bin/env python3
"""
Robust ROS 2 SLAM Map Saver Script for Raspberry Pi 4.
Saves map to ~/robot_ws/src/robot_bringup/maps/<map_name>.yaml and .pgm
"""
import sys
import os
import time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
import numpy as np


class RobustMapSaver(Node):
    def __init__(self, map_name):
        super().__init__('robust_map_saver')
        self.map_name = map_name
        self.saved = False
        
        # Subscribe with both TRANSIENT_LOCAL and VOLATILE QoS
        for dur in [QoSDurabilityPolicy.TRANSIENT_LOCAL, QoSDurabilityPolicy.VOLATILE]:
            for rel in [QoSReliabilityPolicy.RELIABLE, QoSReliabilityPolicy.BEST_EFFORT]:
                qos = QoSProfile(depth=10, reliability=rel, durability=dur)
                self.create_subscription(OccupancyGrid, '/map', self.map_callback, qos)
                
        self.get_logger().info(f"💾 Searching for active /map topic to save map: '{map_name}'...")

    def map_callback(self, msg: OccupancyGrid):
        if self.saved:
            return
        self.saved = True
        
        w = msg.info.width
        h = msg.info.height
        res = msg.info.resolution
        ox = msg.info.origin.position.x
        oy = msg.info.origin.position.y
        
        self.get_logger().info(f"📊 Received OccupancyGrid map frame ({w}x{h}, resolution {res}m/cell)")
        
        # Reshape grid data
        data = np.array(msg.data, dtype=np.int8).reshape((h, w))
        
        # Convert to PGM grayscale format (0=white/free, 100=black/occupied, -1=unknown 205)
        img = np.full((h, w), 205, dtype=np.uint8)
        img[data == 0] = 254
        img[data > 0] = 0
        img = np.flipud(img)
        
        # Prepare output target paths
        target_dir = os.path.expanduser("~/robot_ws/src/robot_bringup/maps")
        os.makedirs(target_dir, exist_ok=True)
        
        pgm_filename = f"{self.map_name}.pgm"
        pgm_path = os.path.join(target_dir, pgm_filename)
        yaml_path = os.path.join(target_dir, f"{self.map_name}.yaml")
        
        # Write PGM (Binary P5 format - zero dependencies needed)
        with open(pgm_path, 'wb') as f:
            header = f"P5\n{w} {h}\n255\n".encode('ascii')
            f.write(header + img.tobytes())
            
        # Write YAML metadata
        yaml_content = f"""image: {pgm_filename}
mode: trinary
resolution: {res}
origin: [{ox:.6f}, {oy:.6f}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
"""
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
            
        self.get_logger().info(f"✅ MAP SAVED SUCCESSFULLY!")
        print(f"\n=======================================================")
        print(f"  🎉 LƯU BẢN ĐỒ THÀNH CÔNG THÀNH 2 FILE:")
        print(f"  📄 YAML: {yaml_path}")
        print(f"  🖼️ PGM:  {pgm_path}")
        print(f"=======================================================\n")
        rclpy.shutdown()


def main():
    map_name = sys.argv[1] if len(sys.argv) > 1 else f"map_{int(time.time())}"
    rclpy.init()
    node = RobustMapSaver(map_name)
    try:
        rclpy.spin(node)
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
