from setuptools import setup
import os
from glob import glob

package_name = 'vision_ai_node'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        # Ament index marker
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # Package manifest
        ('share/' + package_name, ['package.xml']),
        # Launch files
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
        # Config files
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),
        # Models directory (empty placeholder - user adds .pt files)
        (os.path.join('share', package_name, 'models'),
            glob(os.path.join('models', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='robot@todo.todo',
    description='AI Vision node with YOLO for ROS2 Humble',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'vision_ai_node = vision_ai_node.vision_ai_node:main',
        ],
    },
)
