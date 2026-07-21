#!/usr/bin/env python3
"""
Test script to simulate ESP32 sending data via USB serial.
This requires socat on Linux or similar tool to create virtual serial port pairs.

For testing without virtual ports, you can manually send data to the serial port:
  python3 -c "import serial; s=serial.Serial('/dev/ttyUSB0',115200); s.write(b'Hello Pi\\r\\n')"

Or use screen/minicom to manually interact with /dev/ttyACM0
"""

import serial
import time
import argparse


def send_test_data(port='/dev/ttyACM0', baudrate=115200, delay=2):
    """Send test data to serial port."""
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(0.5)  # Wait for connection
        
        test_messages = [
            b'Hello Pi\r\n',
            b'{"battery": 12.4}\r\n',
            b'Status: OK\r\n',
            b'Sensor data: 123,456,789\r\n',
        ]
        
        print(f"Connected to {port} at {baudrate} baud")
        print("Sending test messages...\n")
        
        for msg in test_messages:
            print(f"Sending: {msg.decode().strip()}")
            ser.write(msg)
            time.sleep(delay)
        
        ser.close()
        print("\nTest complete!")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send test data to serial port')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port (default: /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baudrate (default: 115200)')
    parser.add_argument('--delay', type=float, default=2, help='Delay between messages in seconds (default: 2)')
    
    args = parser.parse_args()
    
    send_test_data(args.port, args.baud, args.delay)
