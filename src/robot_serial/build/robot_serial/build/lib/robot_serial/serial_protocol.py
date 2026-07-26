"""
serial_protocol.py - Protocol builder for commands sent to ESP32.

This module is responsible ONLY for formatting commands that will
be sent to the ESP32 over serial.

It does NOT import any ROS2 modules. Pure command formatting.

Protocol format:
  <TAG,value1,value2,...>\n

Examples:
  build_cmd_vel(0.25, 0.0)  -> "<CMD,0.25,0.00>\n"
  build_pid(1.0, 0.1, 0.01) -> "<PID,1.00,0.10,0.01>\n"
  build_led(True)           -> "<LED,1>\n"
  build_stop()              -> "<STOP>\n"
  build_reset()             -> "<RESET>\n"

Author: robot
License: Apache-2.0
"""

from typing import Optional


class SerialProtocol:
    """
    Builds serial protocol commands for ESP32.

    All methods are static (no instance state needed).
    Each method returns a properly formatted string
    ready to be written to serial.
    """

    # Frame delimiters
    FRAME_START = '<'
    FRAME_END = '>'
    LINE_END = '\n'

    @staticmethod
    def _format_frame(tag: str, *values) -> str:
        """
        Format a command frame.

        Args:
            tag: Command tag (CMD, PID, LED, etc.)
            *values: Variable number of values to include

        Returns:
            Formatted frame string with newline terminator.

        Example:
            _format_frame("CMD", 0.25, 0.0) -> "<CMD,0.25,0.00>\n"
        """
        if values:
            # Format values: floats with 2 decimal places, others as-is
            formatted_values = []
            for v in values:
                if isinstance(v, float):
                    formatted_values.append(f'{v:.2f}')
                else:
                    formatted_values.append(str(v))
            content = f'{tag},{",".join(formatted_values)}'
        else:
            content = tag

        return f'{SerialProtocol.FRAME_START}{content}{SerialProtocol.FRAME_END}{SerialProtocol.LINE_END}'

    @staticmethod
    def build_cmd_vel(linear: float, angular: float) -> str:
        """
        Build velocity command for differential drive.

        Args:
            linear: Linear velocity in m/s (forward positive)
            angular: Angular velocity in rad/s (counter-clockwise positive)

        Returns:
            Formatted command string.

        Example:
            build_cmd_vel(0.25, 0.0) -> "<CMD,0.25,0.00>\n"
        """
        return SerialProtocol._format_frame('CMD', linear, angular)

    @staticmethod
    def build_pid(kp: float, ki: float, kd: float) -> str:
        """
        Build PID tuning command.

        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain

        Returns:
            Formatted command string.

        Example:
            build_pid(1.0, 0.1, 0.01) -> "<PID,1.00,0.10,0.01>\n"
        """
        return SerialProtocol._format_frame('PID', kp, ki, kd)

    @staticmethod
    def build_led(state: bool) -> str:
        """
        Build LED control command.

        Args:
            state: True = ON, False = OFF

        Returns:
            Formatted command string.

        Example:
            build_led(True) -> "<LED,1>\n"
            build_led(False) -> "<LED,0>\n"
        """
        return SerialProtocol._format_frame('LED', 1 if state else 0)

    @staticmethod
    def build_stop() -> str:
        """
        Build emergency stop command.

        Returns:
            Formatted command string.

        Example:
            build_stop() -> "<STOP>\n"
        """
        return SerialProtocol._format_frame('STOP')

    @staticmethod
    def build_reset() -> str:
        """
        Build ESP reset command.

        Returns:
            Formatted command string.

        Example:
            build_reset() -> "<RESET>\n"
        """
        return SerialProtocol._format_frame('RESET')

    @staticmethod
    def build_custom(tag: str, *values) -> Optional[str]:
        """
        Build a custom command with arbitrary tag and values.

        Use this for extending the protocol without modifying this file.

        Args:
            tag: Custom command tag
            *values: Variable number of values

        Returns:
            Formatted command string, or None if tag is empty.

        Example:
            build_custom("SERVO", 90) -> "<SERVO,90>\n"
        """
        if not tag:
            return None
        return SerialProtocol._format_frame(tag.upper(), *values)
