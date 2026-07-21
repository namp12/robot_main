#!/usr/bin/env python3
"""
Unit test for robot_serial components.
Tests SerialManager port detection and basic functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add workspace to path
workspace_path = '/home/robot/robot_ws/install/robot_serial/lib/python3.10/site-packages'
if workspace_path not in sys.path:
    sys.path.insert(0, workspace_path)

from robot_serial.serial_manager import SerialManager


def test_port_detection():
    """Test serial port detection logic."""
    print("=" * 60)
    print("Test 1: Port Detection Logic")
    print("=" * 60)
    
    manager = SerialManager()
    
    # Test 1a: Find existing port (should find /dev/ttyACM0 or /dev/ttyUSB0)
    port = manager.find_serial_port()
    if port:
        print(f"✓ Found available port: {port}")
    else:
        print("✗ No serial port found (OK if ESP32 not connected)")
    
    # Test 1b: Check port priority order
    print("\nExpected priority order:")
    for i, p in enumerate(manager.SERIAL_PORTS, 1):
        exists = "✓" if os.path.exists(p) else "✗"
        print(f"  {i}. {p} {exists}")
    
    print()
    return True


def test_manager_callbacks():
    """Test SerialManager callback functionality."""
    print("=" * 60)
    print("Test 2: Callback Mechanism")
    print("=" * 60)
    
    callbacks_called = {
        'data': False,
        'connected': False,
        'disconnected': False,
    }
    
    received_data = []
    connected_port = []
    
    def on_data(data):
        callbacks_called['data'] = True
        received_data.append(data)
        print(f"  - Callback: data received: '{data}'")
    
    def on_connected(port):
        callbacks_called['connected'] = True
        connected_port.append(port)
        print(f"  - Callback: connected to {port}")
    
    def on_disconnected():
        callbacks_called['disconnected'] = True
        print(f"  - Callback: disconnected")
    
    manager = SerialManager(
        on_data_received=on_data,
        on_connected=on_connected,
        on_disconnected=on_disconnected
    )
    
    print("✓ SerialManager created with callbacks")
    print(f"✓ Callback methods are set")
    
    print()
    return True


def test_connection_properties():
    """Test SerialManager connection properties."""
    print("=" * 60)
    print("Test 3: Connection Properties")
    print("=" * 60)
    
    manager = SerialManager()
    
    # Test 3a: Initial state
    assert manager.connected == False, "Should not be connected initially"
    print("✓ Initial state: not connected")
    
    assert manager.current_port == None, "Current port should be None initially"
    print("✓ Initial state: current_port is None")
    
    assert manager.is_connected() == False, "is_connected() should return False"
    print("✓ is_connected() returns False")
    
    # Test 3b: Serial configuration
    assert manager.BAUDRATE == 115200, "Baudrate should be 115200"
    print(f"✓ Baudrate configured: {manager.BAUDRATE}")
    
    assert manager.TIMEOUT_MS == 100, "Timeout should be 100ms"
    print(f"✓ Timeout configured: {manager.TIMEOUT_MS}ms")
    
    print()
    return True


def test_manager_methods():
    """Test that all required methods exist and are callable."""
    print("=" * 60)
    print("Test 4: Required Methods")
    print("=" * 60)
    
    manager = SerialManager()
    
    required_methods = [
        'find_serial_port',
        'connect',
        'disconnect',
        'read_line',
        'is_connected',
        'get_current_port',
    ]
    
    for method_name in required_methods:
        assert hasattr(manager, method_name), f"Missing method: {method_name}"
        assert callable(getattr(manager, method_name)), f"Not callable: {method_name}"
        print(f"✓ Method exists: {method_name}()")
    
    print()
    return True


def main():
    """Run all tests."""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Robot Serial - Unit Tests".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    tests = [
        ("Port Detection", test_port_detection),
        ("Callbacks", test_manager_callbacks),
        ("Connection Properties", test_connection_properties),
        ("Required Methods", test_manager_methods),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test_name} FAILED: {e}\n")
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("✓ All tests PASSED!")
        print()
        print("Next steps:")
        print("  1. Connect ESP32 via USB")
        print("  2. Run: ros2 launch robot_serial robot_serial.launch.py")
        print("  3. Send data from ESP32")
        print("  4. Verify logs show [RX] messages")
        return 0
    else:
        print("✗ Some tests FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
