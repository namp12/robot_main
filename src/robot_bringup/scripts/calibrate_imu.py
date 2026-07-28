#!/usr/bin/env python3
"""
calibrate_imu.py - Automated IMU calibration tool.
Fills the gap for Level 5 (Sensor Calibration).

This node:
1. Subscribes to /imu/data while the robot is stationary.
2. Collects N samples of angular velocity and linear acceleration.
3. Computes the mean (bias) and variance (noise covariance).
4. Outputs the recommended parameter configurations for your EKF.
"""

import sys
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class ImuCalibrator(Node):
    def __init__(self, num_samples=300):
        super().__init__('imu_calibrator')
        self.num_samples = num_samples
        self.samples_collected = 0
        
        self.gyro_z = []
        self.acc_x = []
        self.acc_y = []
        
        self.subscription = self.create_subscription(
            Imu,
            '/imu/data',
            self.listener_callback,
            10
        )
        
        self.get_logger().info(
            f"IMU Calibrator initialized. Please ensure the robot is COMPLETELY stationary."
        )
        self.get_logger().info(f"Collecting {self.num_samples} samples...")

    def listener_callback(self, msg):
        if self.samples_collected >= self.num_samples:
            return
            
        self.gyro_z.append(msg.angular_velocity.z)
        self.acc_x.append(msg.linear_acceleration.x)
        self.acc_y.append(msg.linear_acceleration.y)
        
        self.samples_collected += 1
        
        if self.samples_collected % 50 == 0:
            self.get_logger().info(f"Collected {self.samples_collected}/{self.num_samples} samples...")
            
        if self.samples_collected == self.num_samples:
            self.calculate_calibration()
            # Shutdown node safely
            self.get_logger().info("Calibration finished. Shutting down...")
            sys.exit(0)

    def calculate_calibration(self):
        self.get_logger().info("--- CALIBRATION RESULTS ---")
        
        # Calculate statistics
        gyro_z_mean = np.mean(self.gyro_z)
        gyro_z_var = np.var(self.gyro_z)
        
        acc_x_mean = np.mean(self.acc_x)
        acc_x_var = np.var(self.acc_x)
        
        acc_y_mean = np.mean(self.acc_y)
        acc_y_var = np.var(self.acc_y)
        
        print("\n" + "="*50)
        print("1. GYROSCOPE BIAS (wz offset):")
        print(f"   Mean (Bias)   : {gyro_z_mean:.8f} rad/s")
        print(f"   Variance      : {gyro_z_var:.8f} (rad/s)^2")
        print(f"   Std Dev (Noise): {np.sqrt(gyro_z_var):.8f} rad/s")
        
        print("\n2. ACCELEROMETER COVARIANCE:")
        print(f"   Acc X Var     : {acc_x_var:.8f} (m/s^2)^2")
        print(f"   Acc Y Var     : {acc_y_var:.8f} (m/s^2)^2")
        print("="*50)
        
        print("\nRECOMMENDED EKF COVARIANCE CONFIGURATION:")
        print("Copy the following values into your EKF configuration file:")
        print("-" * 50)
        
        # Print covariance matrices representation
        imu_covariance = [0.0] * 9
        imu_covariance[0] = acc_x_var
        imu_covariance[4] = acc_y_var
        imu_covariance[8] = gyro_z_var
        
        print(f"imu0_pose_rejection_threshold: 5.0")
        print(f"imu0_twist_rejection_threshold: 5.0")
        print("\nRecommended noise diagonal in process_noise_covariance:")
        print(f"imu0_gyro_noise_covariance_z  : {gyro_z_var:.8f}")
        print(f"imu0_acc_noise_covariance_x   : {acc_x_var:.8f}")
        print(f"imu0_acc_noise_covariance_y   : {acc_y_var:.8f}")
        print("-" * 50 + "\n")

def main(args=None):
    rclpy.init(args=args)
    node = ImuCalibrator()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
