import re
from typing import Dict, Any


def parse_sensor_line(line: str) -> Dict[str, Any]:
    """Parse sensor lines from ESP32 into a structured dictionary.

    Supports several formats, including:
    - ESP32_DATA front=... ax=... ay=... az=... gx=... gy=... gz=... roll=... pitch=... yaw=...
    - IMU: ax=... ay=... az=... gx=... gy=... gz=...
    - SENSORS: front=... rear=... battery=...
    - generic key=value pairs.
    """
    text = line.strip()
    result: Dict[str, Any] = {
        'imu': {},
        'distance': {},
        'battery': None,
        'raw': text,
    }

    if not text:
        return result

    # New ESP32_DATA format: prefix + key=value pairs
    esp32_data_match = re.search(r'ESP32_DATA\s+(.*)', text, re.IGNORECASE)
    if esp32_data_match:
        payload = esp32_data_match.group(1)
        for token in re.split(r'[,;\s]+', payload):
            if '=' not in token:
                continue
            key, value = token.split('=', 1)
            key = key.lower()
            value_clean = value.strip('(),')
            try:
                value_num = float(value_clean)
            except ValueError:
                continue

            if key in {'front', 'front_dist', 'frontdistance', 'distance_front'}:
                result['distance']['front'] = value_num
            elif key in {'rear', 'rear_dist', 'reardistance', 'distance_rear'}:
                result['distance']['rear'] = value_num
            elif key in {'battery', 'bat', 'voltage'}:
                result['battery'] = value_num
            elif key in {'ax', 'accelx'}:
                result['imu']['ax'] = value_num
            elif key in {'ay', 'accely'}:
                result['imu']['ay'] = value_num
            elif key in {'az', 'accelz'}:
                result['imu']['az'] = value_num
            elif key in {'gx', 'gyrox'}:
                result['imu']['gx'] = value_num
            elif key in {'gy', 'gyroy'}:
                result['imu']['gy'] = value_num
            elif key in {'gz', 'gyroz'}:
                result['imu']['gz'] = value_num
            elif key in {'roll'}:
                result['imu']['roll'] = value_num
            elif key in {'pitch'}:
                result['imu']['pitch'] = value_num
            elif key in {'yaw'}:
                result['imu']['yaw'] = value_num

    # Generic key=value parsing for common sensor labels
    for token in re.split(r'[,;\s]+', text):
        if '=' not in token:
            continue
        key, value = token.split('=', 1)
        key = key.lower()
        value_clean = value.strip('(),')
        try:
            value_num = float(value_clean)
        except ValueError:
            continue

        if key.startswith('ax') or key.startswith('accelx'):
            result['imu']['ax'] = value_num
        elif key.startswith('ay') or key.startswith('accely'):
            result['imu']['ay'] = value_num
        elif key.startswith('az') or key.startswith('accelz'):
            result['imu']['az'] = value_num
        elif key.startswith('gx') or key.startswith('gyrox'):
            result['imu']['gx'] = value_num
        elif key.startswith('gy') or key.startswith('gyroy'):
            result['imu']['gy'] = value_num
        elif key.startswith('gz') or key.startswith('gyroz'):
            result['imu']['gz'] = value_num
        elif key in {'front', 'front_dist', 'frontdistance', 'distance_front'}:
            result['distance']['front'] = value_num
        elif key in {'rear', 'rear_dist', 'reardistance', 'distance_rear'}:
            result['distance']['rear'] = value_num
        elif key in {'battery', 'bat', 'voltage'}:
            result['battery'] = value_num

    # Handle explicit IMU prefix
    imu_match = re.search(r'IMU[:\s]+(.*)', text, re.IGNORECASE)
    if imu_match:
        payload = imu_match.group(1)
        for token in re.split(r'[,;\s]+', payload):
            if '=' not in token:
                continue
            key, value = token.split('=', 1)
            key = key.lower()
            try:
                result['imu'][key] = float(value)
            except ValueError:
                continue

    # Handle explicit sensors prefix
    sensors_match = re.search(r'SENSORS?[:\s]+(.*)', text, re.IGNORECASE)
    if sensors_match:
        payload = sensors_match.group(1)
        for token in re.split(r'[,;\s]+', payload):
            if '=' not in token:
                continue
            key, value = token.split('=', 1)
            key = key.lower()
            try:
                value_f = float(value)
            except ValueError:
                continue
            if key in {'front', 'front_dist', 'frontdistance', 'distance_front'}:
                result['distance']['front'] = value_f
            elif key in {'rear', 'rear_dist', 'reardistance', 'distance_rear'}:
                result['distance']['rear'] = value_f
            elif key in {'battery', 'bat', 'voltage'}:
                result['battery'] = value_f

    return result
