import re
from typing import Any, Dict, Optional


def _extract_unit_value(text: str, unit: str):
    pattern = rf'([-+]?\d*\.?\d+)\s*{re.escape(unit)}'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _extract_key_value(text: str, key: str):
    pattern = rf'{re.escape(key)}\s*=\s*([-+]?\d*\.?\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_sensor_line(line: str) -> Dict[str, Any]:
    text = line.strip()
    result: Dict[str, Any] = {
        'imu': {},
        'distance': {},
        'battery': None,
        'mode': None,
        'status': None,
        'encoder_distance': None,
        'raw': text,
    }

    if not text:
        return result

    upper = text.upper()

    # 0) Space-separated tagged lines (from esp32_mecanum.ino firmware)
    parts = text.split()
    if len(parts) >= 2:
        tag = parts[0].upper()
        if tag == "STATUS":
            result['status'] = parts[1].upper()
            return result
        elif tag == "BATTERY" and len(parts) >= 3:
            try:
                # Part 1 is pct, Part 2 is voltage, Part 3 is current
                result['battery'] = float(parts[2])
                return result
            except ValueError:
                pass
        elif tag == "RANGE" and len(parts) >= 3:
            try:
                result['distance']['front'] = float(parts[1])
                result['distance']['rear'] = float(parts[2])
                return result
            except ValueError:
                pass
        elif tag == "IMU" and len(parts) >= 5:
            try:
                import math
                qx = float(parts[1])
                qy = float(parts[2])
                qz = float(parts[3])
                qw = float(parts[4])
                
                # Convert quaternion to Euler angles in degrees
                sinr_cosp = 2.0 * (qw * qx + qy * qz)
                cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
                roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

                sinp = 2.0 * (qw * qy - qz * qx)
                if abs(sinp) >= 1.0:
                    pitch = math.degrees(math.copysign(math.pi / 2.0, sinp))
                else:
                    pitch = math.degrees(math.asin(sinp))

                siny_cosp = 2.0 * (qw * qz + qx * qy)
                cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
                yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))
                
                result['imu']['roll'] = roll
                result['imu']['pitch'] = pitch
                result['imu']['yaw'] = yaw
                return result
            except ValueError:
                pass
        elif tag == "ENCODER":
            try:
                vals = [float(p) for p in parts[1:]]
                if len(vals) >= 4:
                    result['encoder_distance'] = sum(vals) / 4.0
                elif len(vals) >= 1:
                    result['encoder_distance'] = vals[0]
                return result
            except ValueError:
                pass

    # 1) [TELEMETRY] format from real Robot_Tu_Hanh firmware
    if upper.startswith('[TELEMETRY]'):
        mode_match = re.search(r'MODE:\s*([A-Z0-9_]+)', text, re.IGNORECASE)
        if mode_match:
            result['mode'] = mode_match.group(1).upper()

        status_match = re.search(r'STATUS:\s*([A-Z0-9_]+)', text, re.IGNORECASE)
        if status_match:
            result['status'] = status_match.group(1).upper()

        battery = _extract_unit_value(text, 'V')
        if battery is not None:
            result['battery'] = battery

        # Extract front distance: match FRONT or FRONT_DISTANCE prefix
        front_match = re.search(r'(?:FRONT|FRONT_DISTANCE)\s*:\s*([-+]?\d*\.?\d+)\s*cm', text, re.IGNORECASE)
        if front_match:
            try:
                result['distance']['front'] = float(front_match.group(1))
            except ValueError:
                pass

        # Extract rear distance: match REAR or REAR_DISTANCE prefix
        rear_match = re.search(r'(?:REAR|REAR_DISTANCE)\s*:\s*([-+]?\d*\.?\d+)\s*cm', text, re.IGNORECASE)
        if rear_match:
            try:
                result['distance']['rear'] = float(rear_match.group(1))
            except ValueError:
                pass

        yaw = _extract_key_value(text, 'Yaw')
        pitch = _extract_key_value(text, 'Pitch')
        roll = _extract_key_value(text, 'Roll')
        if yaw is not None:
            result['imu']['yaw'] = yaw
        if pitch is not None:
            result['imu']['pitch'] = pitch
        if roll is not None:
            result['imu']['roll'] = roll

        ax = _extract_key_value(text, 'Ax')
        ay = _extract_key_value(text, 'Ay')
        az = _extract_key_value(text, 'Az')
        gx = _extract_key_value(text, 'Gx')
        gy = _extract_key_value(text, 'Gy')
        gz = _extract_key_value(text, 'Gz')
        if ax is not None:
            result['imu']['ax'] = ax
        if ay is not None:
            result['imu']['ay'] = ay
        if az is not None:
            result['imu']['az'] = az
        if gx is not None:
            result['imu']['gx'] = gx
        if gy is not None:
            result['imu']['gy'] = gy
        if gz is not None:
            result['imu']['gz'] = gz

        dist_m = _extract_key_value(text, 'Dist')
        if dist_m is not None:
            result['encoder_distance'] = dist_m

        return result

    # 2) Simple key=value lines
    for token in re.split(r'[,;\s]+', text):
        if '=' not in token:
            continue
        key, value = token.split('=', 1)
        key = key.strip().upper()
        value_clean = value.strip().strip('(),').strip()
        try:
            value_num = float(value_clean)
        except ValueError:
            continue

        if key == 'FRONT_DISTANCE':
            result['distance']['front'] = value_num
        elif key == 'REAR_DISTANCE':
            result['distance']['rear'] = value_num
        elif key == 'BATTERY':
            result['battery'] = value_num
        elif key == 'ENCODER_DIST':
            result['encoder_distance'] = value_num
        elif key in {'IMU', 'IMU_RAW'}:
            continue

    # 3) Legacy single-key lines
    if upper.startswith('MODE='):
        result['mode'] = text.split('=', 1)[1].strip().upper()
        return result

    if upper.startswith('STATUS='):
        result['status'] = text.split('=', 1)[1].strip().upper()
        return result

    if upper.startswith('BATTERY='):
        try:
            result['battery'] = float(text.split('=', 1)[1].strip())
        except ValueError:
            pass
        return result

    if upper.startswith('FRONT_DISTANCE='):
        try:
            result['distance']['front'] = float(text.split('=', 1)[1].strip())
        except ValueError:
            pass
        return result

    if upper.startswith('REAR_DISTANCE='):
        try:
            result['distance']['rear'] = float(text.split('=', 1)[1].strip())
        except ValueError:
            pass
        return result

    return result
