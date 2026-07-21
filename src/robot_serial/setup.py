from setuptools import setup

package_name = 'robot_serial'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/robot_serial.launch.py']),
        ('share/' + package_name + '/config',
            ['config/serial.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='robot@todo.todo',
    description='Serial bridge between ESP32 and ROS2',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'serial_node = robot_serial.serial_node:main',
        ],
    },
)
