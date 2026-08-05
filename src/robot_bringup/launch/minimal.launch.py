#!/usr/bin/env python3
"""Minimal robot compute stack for the Raspberry Pi."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_pkg = FindPackageShare('robot_bringup')
    description_pkg = FindPackageShare('robot_description')
    serial_pkg = FindPackageShare('robot_serial')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time if true',
    )
    publish_robot_description_arg = DeclareLaunchArgument(
        'publish_robot_description',
        default_value='true',
        description='Launch robot_state_publisher when true',
    )
    enable_lidar_arg = DeclareLaunchArgument(
        'enable_lidar',
        default_value='true',
        description='Launch the LiDAR driver when true',
    )
    enable_serial_arg = DeclareLaunchArgument(
        'enable_serial',
        default_value='true',
        description='Launch the ESP32 serial bridge when true',
    )
    enable_wheel_odom_arg = DeclareLaunchArgument(
        'enable_wheel_odom',
        default_value='false',
        description='Launch wheel odometry when true',
    )
    enable_ekf_arg = DeclareLaunchArgument(
        'enable_ekf',
        default_value='false',
        description='Launch EKF sensor fusion (robot_localization) when true',
    )
    enable_camera_arg = DeclareLaunchArgument(
        'enable_camera',
        default_value='true',
        description='Launch camera node when true',
    )
    serial_port_arg = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/rplidar',
        description='USB serial port for the LiDAR',
    )
    use_static_odom_arg = DeclareLaunchArgument(
        'use_static_odom',
        default_value='true',
        description='Use a static odom->base_footprint transform',
    )
    wheel_radius_arg = DeclareLaunchArgument(
        'wheel_radius',
        default_value='0.033',
        description='Wheel radius in meters',
    )
    wheel_separation_arg = DeclareLaunchArgument(
        'wheel_separation',
        default_value='0.30',
        description='Distance between left and right wheels in meters',
    )

    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([description_pkg, 'launch', 'robot_state_publisher.launch.py'])
        ),
        launch_arguments={
            'use_static_odom': LaunchConfiguration('use_static_odom'),
            'use_gazebo': 'false',
        }.items(),
        condition=IfCondition(LaunchConfiguration('publish_robot_description')),
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_pkg, 'launch', 'lidar.launch.py'])
        ),
        launch_arguments={
            'serial_port': LaunchConfiguration('serial_port'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('enable_lidar')),
    )

    serial_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([serial_pkg, 'launch', 'robot_serial.launch.py'])
        ),
        launch_arguments={
            'port': 'auto',
        }.items(),
        condition=IfCondition(LaunchConfiguration('enable_serial')),
    )

    wheel_odom_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([serial_pkg, 'launch', 'wheel_odom.launch.py'])
        ),
        launch_arguments={
            'wheel_radius': LaunchConfiguration('wheel_radius'),
            'wheel_separation': LaunchConfiguration('wheel_separation'),
            'odom_frame': 'odom',
            'base_frame': 'base_footprint',
            'publish_rate': '20.0',
            'publish_tf': PythonExpression(["'false' if '", LaunchConfiguration('enable_ekf'), "' == 'true' else 'true'"]),
        }.items(),
        condition=IfCondition(LaunchConfiguration('enable_wheel_odom')),
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            PathJoinSubstitution([bringup_pkg, 'config', 'ekf.yaml']),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ],
        condition=IfCondition(LaunchConfiguration('enable_ekf')),
    )

    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('camera_node'), 'launch', 'camera.launch.py'])
        ),
        condition=IfCondition(LaunchConfiguration('enable_camera')),
    )

    web_bridge_node = Node(
        package='web_bridge',
        executable='web_bridge',
        name='web_bridge_node',
        output='screen',
    )

    http_bridge_node = Node(
        package='robot_ai',
        executable='http_bridge_node',
        name='http_bridge_node',
        output='screen',
    )

    audio_stream_node = Node(
        package='robot_ai',
        executable='audio_stream_server',
        name='audio_stream_server',
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        publish_robot_description_arg,
        enable_lidar_arg,
        enable_serial_arg,
        enable_wheel_odom_arg,
        enable_ekf_arg,
        enable_camera_arg,
        serial_port_arg,
        use_static_odom_arg,
        wheel_radius_arg,
        wheel_separation_arg,
        robot_state_publisher_launch,
        lidar_launch,
        serial_launch,
        wheel_odom_launch,
        ekf_node,
        camera_launch,
        web_bridge_node,
        http_bridge_node,
        audio_stream_node,
    ])
