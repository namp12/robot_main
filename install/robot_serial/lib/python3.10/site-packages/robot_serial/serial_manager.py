import serial
import time
import os
from typing import Optional, Callable


class SerialManager:
    """Manages serial connection to ESP32 device."""
    
    # Prioritized list of serial ports to check
    SERIAL_PORTS = [
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
        '/dev/ttyACM0',
        '/dev/ttyACM1',
    ]
    
    BAUDRATE = 115200
    TIMEOUT_MS = 100
    
    def __init__(self, on_data_received: Optional[Callable[[str], None]] = None,
                 on_connected: Optional[Callable[[str], None]] = None,
                 on_disconnected: Optional[Callable[[], None]] = None):
        """
        Initialize SerialManager.
        
        Args:
            on_data_received: Callback when data is received
            on_connected: Callback when successfully connected
            on_disconnected: Callback when disconnected
        """
        self.serial_port = None
        self.connected = False
        self.current_port = None
        
        self.on_data_received = on_data_received
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
    
    def find_serial_port(self) -> Optional[str]:
        """
        Find available serial port in priority order.
        
        Returns:
            Port name if found, None otherwise
        """
        for port in self.SERIAL_PORTS:
            if os.path.exists(port):
                return port
        return None
    
    def connect(self) -> bool:
        """
        Connect to serial port.
        
        Returns:
            True if connected successfully, False otherwise
        """
        port = self.find_serial_port()
        
        if port is None:
            return False
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.BAUDRATE,
                timeout=self.TIMEOUT_MS / 1000.0
            )
            self.connected = True
            self.current_port = port
            
            if self.on_connected:
                self.on_connected(port)
            
            return True
        
        except Exception as e:
            self.connected = False
            self.serial_port = None
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
        
        if self.on_disconnected:
            self.on_disconnected()
    
    def read_line(self) -> Optional[str]:
        """
        Read one line from serial port (non-blocking if timeout is set).
        
        Returns:
            Line of data (without newline) if available, None otherwise
        """
        if not self.connected or self.serial_port is None:
            return None
        
        try:
            # Check if data is available
            if self.serial_port.in_waiting > 0:
                data = self.serial_port.readline()
                if data:
                    line = data.decode('utf-8', errors='replace').rstrip('\r\n')
                    if line:  # Only return non-empty lines
                        if self.on_data_received:
                            self.on_data_received(line)
                        return line
            
            return None
        
        except serial.SerialException:
            # Connection lost
            self.disconnect()
            return None
        except Exception as e:
            # Other errors
            return None
    
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
