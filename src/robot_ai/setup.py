from setuptools import setup
import os
from glob import glob

package_name = 'robot_ai'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name, package_name + '.autonomy', package_name + '.mode_manager'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=[
        'setuptools',
        'pyttsx3',
        'openai',
        'SpeechRecognition',
    ],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='robot@todo.todo',
    description='Cloud-backed dialogue and TTS support for ROS2 Humble',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
     'console_scripts': [
        'dialogue_tts_node = robot_ai.dialogue_tts_node:main',
        'stt_node = robot_ai.stt_node:main',
        'command_node = robot_ai.command_node:main',
        'http_bridge_node = robot_ai.http_bridge_node:main',
        'video_stream_server = robot_ai.video_stream_server:main',
        'audio_stream_server = robot_ai.audio_stream_server:main',
        'autonomy_node = robot_ai.autonomy_node:main',
        'mode_manager_node = robot_ai.mode_manager_node:main',
    ]
  }
)
