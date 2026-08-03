from setuptools import setup

package_name = 'web_bridge'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            [package_name + '/launch/web_bridge.launch.py']),
    ],
    install_requires=['setuptools', 'websockets'],
    zip_safe=True,
    maintainer='robot',
    maintainer_email='robot@todo.todo',
    description='WebSocket bridge between ROS2 and web dashboard',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'web_bridge = web_bridge.web_bridge_node:main',
            'web_bridge_node = web_bridge.web_bridge_node:main',
        ],
    },
)
