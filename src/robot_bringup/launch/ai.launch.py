#!/usr/bin/env python3
"""Launch the local dialogue/TTS AI node as an optional bringup component."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    enable_ai_arg = DeclareLaunchArgument(
        'enable_ai',
        default_value='false',
        description='Launch the dialogue AI node when true',
    )
    openai_enabled_arg = DeclareLaunchArgument(
        'openai_enabled',
        default_value='false',
        description='Enable ChatGPT/OpenAI for response generation',
    )
    openai_model_arg = DeclareLaunchArgument(
        'openai_model',
        default_value='gpt-3.5-turbo',
        description='OpenAI model name used for responses',
    )

    dialogue_tts_node = Node(
        package='robot_ai',
        executable='dialogue_tts_node',
        name='dialogue_tts_node',
        output='screen',
        parameters=[
            {
                'openai_enabled': LaunchConfiguration('openai_enabled'),
                'openai_model': LaunchConfiguration('openai_model'),
            },
        ],
        condition=IfCondition(LaunchConfiguration('enable_ai')),
    )

    return LaunchDescription([
        enable_ai_arg,
        openai_enabled_arg,
        openai_model_arg,
        dialogue_tts_node,
    ])
