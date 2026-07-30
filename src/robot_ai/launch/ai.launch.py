#!/usr/bin/env python3
"""
ai.launch.py - Launch the robot_ai dialogue/TTS node.

Usage:
  ros2 launch robot_ai ai.launch.py

Node: dialogue_tts_node
  Subscribes: /speech/text (std_msgs/String)
  Publishes: /dialogue/response (std_msgs/String)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
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
    speech_engine_arg = DeclareLaunchArgument(
        'stt_engine',
        default_value='google',
        description='Speech-to-text engine: google, sphinx, whisper',
    )
    microphone_index_arg = DeclareLaunchArgument(
        'microphone_index',
        default_value='-1',
        description='Microphone device index for SpeechRecognition',
    )
    language_arg = DeclareLaunchArgument(
        'language',
        default_value='vi-VN',
        description='Speech recognition language code',
    )

    stt_node = Node(
        package='robot_ai',
        executable='stt_node',
        name='speech_to_text_node',
        output='screen',
        parameters=[
            {
                'stt_engine': LaunchConfiguration('stt_engine'),
                'microphone_index': LaunchConfiguration('microphone_index'),
                'language': LaunchConfiguration('language'),
            },
        ],
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
    )

    return LaunchDescription([
        openai_enabled_arg,
        openai_model_arg,
        speech_engine_arg,
        microphone_index_arg,
        language_arg,
        stt_node,
        dialogue_tts_node,
    ])
