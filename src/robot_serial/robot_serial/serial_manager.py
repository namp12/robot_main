import glob
import os
import struct
from typing import Optional, Callable

import serial


class SerialManager:
    """Manages serial connection to ESP32 device."""
    
    # Prioritized list of serial ports to check
    SERIAL_PORTS = [
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
        '/dev/ttyUSB2',
        '/dev/ttyACM0',
        '/dev/ttyACM1',
        '/dev/ttyACM2',
    ]
    
    BAUDRATE = 115200
    TIMEOUT_MS = 100
    
    # Binary protocol markers
    BINARY_HEADER_1 = 0xFF
    BINARY_HEADER_2 = 0xFE
    BINARY_TAIL = 0xFD
    
    def __init__(self, on_data_received: Optional[Callable[[str], None]] = None,
                 on_connected: Optional[Callable[[str], None]] = None,
                 on_disconnected: Optional[Callable[[], None]] = None,
                 port: Optional[str] = None,
                 baudrate: int = 115200):
        """
        Initialize SerialManager.
        
        Args:
            on_data_received: Callback when data is received
            on_connected: Callback when successfully connected
            on_disconnected: Callback when disconnected
            port: Specific port path or 'auto'
            baudrate: Baudrate for serial connection
        """
        self.serial_port = None
        self.connected = False
        self.current_port = None
        self.target_port = port if (port and port != 'auto') else None
        self.baudrate = baudrate
        self.last_error = ""
        
        self.on_data_received = on_data_received
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        
        # Buffer for handling mixed text/binary data
        self.read_buffer = bytearray()
    
    def find_serial_port(self) -> Optional[str]:
        """
        Find available serial port in priority order (Smart Auto-Detection).
        """
        # 1. Nếu chỉ định target_port và cổng tồn tại -> Dùng ngay
        if self.target_port and self.target_port != 'auto' and os.path.exists(self.target_port):
            return self.target_port

        # 2. Ưu tiên Udev symlink /dev/esp32
        if os.path.exists('/dev/esp32'):
            return '/dev/esp32'

        # Tìm đường dẫn thực của mắt thần LiDAR (nếu có /dev/rplidar)
        lidar_path = None
        if os.path.exists('/dev/rplidar'):
            try:
                lidar_path = os.path.realpath('/dev/rplidar')
            except Exception:
                pass

        all_acm = sorted(glob.glob('/dev/ttyACM*'))
        all_usb = sorted(glob.glob('/dev/ttyUSB*'))
        print(f"🔎 [SERIAL SCAN] target_port='{self.target_port}', ACM={all_acm}, USB={all_usb}, LiDAR='{lidar_path}'", flush=True)

        # 3. Thử tất cả cổng /dev/ttyACM*
        for p in all_acm:
            if lidar_path is None or os.path.realpath(p) != lidar_path:
                return p

        # 4. Thử các cổng /dev/ttyUSB* ngoại trừ USB0 (để nhường LiDAR)
        non_usb0 = [p for p in all_usb if 'USB0' not in p.upper() and (lidar_path is None or os.path.realpath(p) != lidar_path)]
        if non_usb0:
            return non_usb0[0]

        # 5. Nếu chỉ có 1 cổng USB và không bị LiDAR chiếm giữ
        for p in all_usb:
            if lidar_path is None or os.path.realpath(p) != lidar_path:
                return p

        return None
    
    def connect(self) -> bool:
        """
        Connect to serial port.
        
        Returns:
            True if connected successfully, False otherwise
        """
        port = self.find_serial_port()
        
        if port is None:
            if self.target_port:
                self.last_error = f"Specified serial port not found: {self.target_port}"
            else:
                self.last_error = "No serial device found on /dev/ttyUSB* or /dev/ttyACM*"
            return False
        
        # Convert symlink like /dev/esp32 to real device path like /dev/ttyACM0
        real_port = os.path.realpath(port)

        try:
            self.serial_port = serial.Serial()
            self.serial_port.port = real_port
            self.serial_port.baudrate = self.baudrate
            self.serial_port.timeout = self.TIMEOUT_MS / 1000.0
            self.serial_port.write_timeout = 0.5
            self.serial_port.dtr = False
            self.serial_port.rts = False
            self.serial_port.open()
            self.serial_port.dtr = False
            self.serial_port.rts = False
            self.connected = True
            self.current_port = real_port
            self.last_error = ""
            
            if self.on_connected:
                self.on_connected(real_port)
            
            return True
        
        except Exception as e:
            self.connected = False
            self.serial_port = None
            self.last_error = f"Failed to open {real_port} (raw: {port}): {e}"
            print(f"❌ [SERIAL ERROR] {self.last_error}", flush=True)
            return False
    
    def disconnect(self):
        """Disconnect from serial port."""
        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass
        
        self.serial_port = None
        self.connected = False
        self.current_port = None
        self.read_buffer = bytearray()
        
        if self.on_disconnected:
            self.on_disconnected()

    def write_data(self, data: bytes) -> bool:
        """Write raw bytes to the serial port."""
        if not self.connected or self.serial_port is None:
            return False
        try:
            self.serial_port.write(data)
            self.serial_port.flush()
            return True
        except Exception:
            self.disconnect()
            return False

    def write_line(self, line: str) -> bool:
        """Write a text line to the serial port, appending \\r\\n matching Arduino Serial Monitor."""
        if not line:
            return False
        clean_line = line.strip('\r\n') + '\r\n'
        payload = clean_line.encode('utf-8', errors='replace')
        return self.write_data(payload)

    def send(self, line: str) -> bool:
        """Alias for write_line."""
        return self.write_line(line)
    
    def read_line(self) -> Optional[str]:
        """
        Read data from serial port with support for both text and binary protocols.
        
        Supports:
        1. Text mode: Lines ending with \\n (debug output, boot messages)
        2. Binary mode: Frames starting with 0xFF 0xFE (telemetry protocol)
        
        Returns:
            Decoded line/data if available, None otherwise
        """
        if not self.connected or self.serial_port is None:
            return None
        
        try:
            # Read available bytes from serial port
            if self.serial_port.in_waiting > 0:
                new_bytes = self.serial_port.read(self.serial_port.in_waiting)
                self.read_buffer.extend(new_bytes)
            
            # Process buffer: look for complete messages
            while len(self.read_buffer) > 0:
                # Try to find text line (ends with \\n)
                newline_pos = self.read_buffer.find(b'\n')
                if newline_pos != -1:
                    # Found a complete text line
                    line_bytes = bytes(self.read_buffer[:newline_pos])
                    self.read_buffer = self.read_buffer[newline_pos + 1:]
                    
                    # Decode and clean
                    line = line_bytes.decode('utf-8', errors='replace').rstrip('\r\n')
                    if line:  # Only return non-empty lines
                        if self.on_data_received:
                            self.on_data_received(line)
                        return line
                    continue
                
                # Try to find binary frame (0xFF 0xFE ... 0xFD)
                if len(self.read_buffer) >= 2:
                    header_pos = -1
                    for i in range(len(self.read_buffer) - 1):
                        if self.read_buffer[i] == self.BINARY_HEADER_1 and \
                           self.read_buffer[i + 1] == self.BINARY_HEADER_2:
                            header_pos = i
                            break
                    
                    if header_pos != -1:
                        # Found binary header, look for tail
                        frame_start = header_pos
                        tail_pos = self.read_buffer.find(self.BINARY_TAIL, frame_start + 4)
                        
                        if tail_pos != -1 and tail_pos > frame_start + 4:
                            # Found complete binary frame
                            frame_bytes = bytes(self.read_buffer[frame_start:tail_pos + 1])
                            self.read_buffer = self.read_buffer[tail_pos + 1:]
                            
                            # Try to parse binary frame
                            frame_info = self._parse_binary_frame(frame_bytes)
                            if frame_info:
                                if self.on_data_received:
                                    self.on_data_received(frame_info)
                                return frame_info
                            continue
                        elif len(self.read_buffer) > 256:
                            # Frame too long, skip this header
                            self.read_buffer = self.read_buffer[frame_start + 2:]
                            continue
                    else:
                        # No header found, remove garbage bytes before potential header
                        if len(self.read_buffer) > 1 and \
                           not (self.read_buffer[0] == self.BINARY_HEADER_1 or \
                                (len(self.read_buffer) > 1 and self.read_buffer[0] >= 32 and self.read_buffer[0] < 127)):
                            # Remove invalid byte
                            self.read_buffer = self.read_buffer[1:]
                            continue
                
                # No complete message found yet
                break
            
            return None
        
        except serial.SerialException:
            # Connection lost
            self.disconnect()
            return None
        except Exception as e:
            # Other errors
            return None
    
    def _parse_binary_frame(self, frame_bytes: bytes) -> Optional[str]:
        """
        Parse binary protocol frame and return formatted string.
        
        Frame format: [0xFF, 0xFE, MsgID, Length, Payload..., CRC16_L, CRC16_H, 0xFD]
        
        Returns:
            Formatted string with frame info, or None if invalid
        """
        try:
            if len(frame_bytes) < 8:
                return None
            
            if frame_bytes[0] != self.BINARY_HEADER_1 or \
               frame_bytes[1] != self.BINARY_HEADER_2 or \
               frame_bytes[-1] != self.BINARY_TAIL:
                return None
            
            msg_id = frame_bytes[2]
            length = frame_bytes[3]
            
            if len(frame_bytes) < 8 + length:
                return None
            
            payload = frame_bytes[4:4+length]
            crc_bytes = frame_bytes[4+length:4+length+2]
            
            if len(crc_bytes) < 2:
                return None
            
            rx_crc = struct.unpack('<H', crc_bytes)[0]
            
            # Calculate CRC over [MsgID + Length + Payload]
            crc_data = bytes([msg_id, length]) + payload
            calc_crc = self._calculate_crc16(crc_data)
            
            msg_type = {0x01: 'TELEMETRY', 0x02: 'CMD_VEL', 0x03: 'SET_MODE', 0x04: 'RESET_YAW'}.get(msg_id, f'UNKNOWN(0x{msg_id:02x})')
            
            if rx_crc == calc_crc:
                return f'[BINARY] {msg_type} ({length} bytes) CRC:✓'
            else:
                return f'[BINARY] {msg_type} ({length} bytes) CRC:✗ (exp={calc_crc:04x}, got={rx_crc:04x})'
        
        except Exception:
            return None
    
    def _calculate_crc16(self, data: bytes) -> int:
        """Calculate CRC16-MODBUS checksum."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF
    
    def is_connected(self) -> bool:
        """Check if currently connected."""
        if not self.connected or self.serial_port is None:
            return False
        
        try:
            # Try to check port status
            return self.serial_port.is_open
        except Exception:
            return False
    
    def get_current_port(self) -> Optional[str]:
        """Get currently connected port name."""
        return self.current_port if self.connected else None
