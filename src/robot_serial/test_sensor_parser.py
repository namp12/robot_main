import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robot_serial.sensor_parser import parse_sensor_line


def test_parse_imu_line():
    data = parse_sensor_line('IMU: ax=0.1 ay=0.2 az=0.3 gx=1.0 gy=2.0 gz=3.0')
    assert data['imu']['ax'] == 0.1
    assert data['imu']['ay'] == 0.2
    assert data['imu']['az'] == 0.3
    assert data['imu']['gx'] == 1.0
    assert data['imu']['gy'] == 2.0
    assert data['imu']['gz'] == 3.0


def test_parse_distance_and_battery_line():
    data = parse_sensor_line('SENSORS: front=12.5 rear=8.0 battery=11.9')
    assert data['distance']['front'] == 12.5
    assert data['distance']['rear'] == 8.0
    assert data['battery'] == 11.9
