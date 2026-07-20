"""
serial_parser.py - Protocol parser for ESP32 serial data.

This module is responsible ONLY for parsing raw serial strings
received from ESP32 into structured Python dictionaries.

It does NOT import any ROS2 modules. Pure data parsing.

Protocol format:
  <TAG,value1,value2,...>

Examples:
  <ENC,120,118>       -> {'type': 'ENC', 'values': [120, 118]}
  <IMU,0.02,-0.01,9.81> -> {'type': 'IMU', 'values': [0.02, -0.01, 9.81]}
  <BAT,15.63>         -> {'type': 'BAT', 'values': [15.63]}
  <RPM,120,121>       -> {'type': 'RPM', 'values': [120, 121]}
  <STATUS,OK>         -> {'type': 'STATUS', 'values': ['OK']}

Author: robot
License: Apache-2.0
"""

from typing import Optional, Dict, List, Any


# Valid message types expected from ESP32
VALID_TAGS = {'ENC', 'IMU', 'BAT', 'RPM', 'STATUS'}


class SerialParser:
    """
    Parses raw serial lines into structured dictionaries.

    Thread-safe: no internal state beyond configuration.
    Each parse() call is independent.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        pass

    def parse(self, raw_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single raw line from serial into a structured dict.

        Args:
            raw_line: Raw string from serial (e.g. "<ENC,120,118>")

        Returns:
            Dictionary with 'type' and 'values' keys if valid,
            None if the line is invalid or should be ignored.

        Example:
            >>> parser = SerialParser()
            >>> parser.parse("<ENC,120,118>")
            {'type': 'ENC', 'values': [120, 118]}
            >>> parser.parse("noise")
            None
        """
        # Strip whitespace and newline
        line = raw_line.strip()

        # Ignore empty lines
        if not line:
            return None

        # Check for valid frame: must start with '<' and end with '>'
        if not (line.startswith('<') and line.endswith('>')):
            return None

        # Remove angle brackets
        content = line[1:-1]

        # Split by comma
        parts = content.split(',')

        # Must have at least a tag
        if len(parts) < 1:
            return None

        # Extract tag (first element)
        tag = parts[0].strip().upper()

        # Validate tag
        if tag not in VALID_TAGS:
            return None

        # Parse values (remaining elements)
        values = self._parse_values(tag, parts[1:])

        if values is None:
            return None

        return {
            'type': tag,
            'values': values
        }

    def _parse_values(self, tag: str, raw_values: List[str]) -> Optional[List[Any]]:
        """
        Parse the value fields based on message type.

        Args:
            tag: Message type tag (ENC, IMU, BAT, etc.)
            raw_values: List of raw string values

        Returns:
            List of parsed values, or None if parsing fails.
        """
        try:
            if tag == 'ENC':
                # Encoder: <ENC,left,right> - integers
                if len(raw_values) < 2:
                    return None
                return [int(raw_values[0].strip()), int(raw_values[1].strip())]

            elif tag == 'IMU':
                # IMU: <IMU,ax,ay,az> - floats
                if len(raw_values) < 3:
                    return None
                return [
                    float(raw_values[0].strip()),
                    float(raw_values[1].strip()),
                    float(raw_values[2].strip())
                ]

            elif tag == 'BAT':
                # Battery: <BAT,voltage> - float
                if len(raw_values) < 1:
                    return None
                return [float(raw_values[0].strip())]

            elif tag == 'RPM':
                # RPM: <RPM,left,right> - integers
                if len(raw_values) < 2:
                    return None
                return [int(raw_values[0].strip()), int(raw_values[1].strip())]

            elif tag == 'STATUS':
                # Status: <STATUS,text> - string
                if len(raw_values) < 1:
                    return None
                return [','.join(v.strip() for v in raw_values)]

            else:
                # Unknown tag - return raw strings
                return [v.strip() for v in raw_values]

        except (ValueError, IndexError) as exc:
            # Parsing failed (e.g. non-numeric value where number expected)
            return None

    def parse_buffer(self, buffer: str) -> List[Dict[str, Any]]:
        """
        Parse a buffer containing multiple lines.

        Splits by newline and parses each line.
        Returns list of successfully parsed messages.

        Args:
            buffer: Multi-line string from serial

        Returns:
            List of parsed message dictionaries.
        """
        results = []
        lines = buffer.split('\n')

        for line in lines:
            parsed = self.parse(line)
            if parsed is not None:
                results.append(parsed)

        return results
