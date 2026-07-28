#!/usr/bin/env python3
"""
validate_odom.py - Automated Odometry Validation tool.
Fills the gap for Level 8 (Odometry Validation).

Usage:
1. Run the script: python3 validate_odom.py
2. Press ENTER to start recording the baseline.
3. Physically push/drive the robot in a straight line (e.g., 2.0 meters).
4. Press ENTER to stop recording.
5. Enter the actual measured distance.
6. The script computes translation error and yaw drift.
"""

import sys
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

class OdomValidator(Node):
    def __init__(self):
        super().__init__('odom_validator')
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        self.current_pose = None
        self.get_logger().info("Odometry Validator initialized.")

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose

def get_yaw_from_quaternion(q):
    siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)

def run_test(node):
    print("\n" + "="*50)
    print("ODOMETRY ACCURACY VALIDATION PROTOCOL")
    print("="*50)
    
    # Wait for first message
    print("Waiting for /odom topic...")
    while rclpy.ok() and node.current_pose is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        
    print("Connected to /odom!")
    input("\n[STEP 1] Place the robot at the start line. Press ENTER to record start pose...")
    
    rclpy.spin_once(node, timeout_sec=0.1)
    start_x = node.current_pose.position.x
    start_y = node.current_pose.position.y
    start_yaw = get_yaw_from_quaternion(node.current_pose.orientation)
    
    print(f"Recorded Start Pose: X={start_x:.4f}m, Y={start_y:.4f}m, Yaw={math.degrees(start_yaw):.2f}°")
    
    input("\n[STEP 2] Drive or push the robot (e.g., 2.0 meters). Press ENTER when stopped...")
    
    rclpy.spin_once(node, timeout_sec=0.1)
    end_x = node.current_pose.position.x
    end_y = node.current_pose.position.y
    end_yaw = get_yaw_from_quaternion(node.current_pose.orientation)
    
    print(f"Recorded End Pose  : X={end_x:.4f}m, Y={end_y:.4f}m, Yaw={math.degrees(end_yaw):.2f}°")
    
    # Calculations
    odom_dist = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    yaw_drift = end_yaw - start_yaw
    # normalize yaw drift
    yaw_drift = math.atan2(math.sin(yaw_drift), math.cos(yaw_drift))
    
    print(f"\nDistance calculated by Odometry: {odom_dist:.4f} meters")
    print(f"Angle drifted by Odometry     : {math.degrees(yaw_drift):.2f} degrees")
    
    try:
        real_dist = float(input("\nEnter the actual measured physical distance (meters): "))
    except ValueError:
        print("Invalid input. Exiting.")
        return
        
    error_m = abs(odom_dist - real_dist)
    error_pct = (error_m / real_dist) * 100.0
    
    print("\n" + "="*50)
    print("VALIDATION REPORT:")
    print(f"   Actual Distance : {real_dist:.4f} m")
    print(f"   Odometry Dist   : {odom_dist:.4f} m")
    print(f"   Absolute Error  : {error_m:.4f} m ({error_m*100.0:.2f} cm)")
    print(f"   Relative Error  : {error_pct:.2f} %")
    print(f"   Heading Drift   : {math.degrees(yaw_drift):.2f}°")
    print("="*50)
    
    if error_pct <= 3.0 and abs(math.degrees(yaw_drift)) <= 5.0:
        print("\n>>> RESULT: PASS (Excellent accuracy!)")
    else:
        print("\n>>> RESULT: FAIL (Odometry needs recalibration of wheel_radius or track width.)")
    print("="*50 + "\n")

def main(args=None):
    rclpy.init(args=args)
    node = OdomValidator()
    try:
        run_test(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
