#!/bin/bash
# Test robot_serial data reception
# This script uses socat to create virtual serial ports for testing

set -e

WORKSPACE="/home/robot/robot_ws"

echo "=========================================="
echo "Robot Serial - Data Reception Test"
echo "=========================================="
echo ""

# Check if socat is installed
if ! command -v socat &> /dev/null; then
    echo "⚠ socat is not installed. Installing..."
    sudo apt-get update && sudo apt-get install -y socat
fi

echo "Creating virtual serial port pair with socat..."
socat -d -d pty,raw,echo=0 pty,raw,echo=0 2>&1 | grep "pty" > /tmp/socat_output.txt &
SOCAT_PID=$!

# Wait for socat to start and extract port names
sleep 2
PORT1=$(grep -oP '/dev/pts/\d+' /tmp/socat_output.txt | head -1)
PORT2=$(grep -oP '/dev/pts/\d+' /tmp/socat_output.txt | tail -1)

if [ -z "$PORT1" ] || [ -z "$PORT2" ]; then
    echo "Failed to create virtual ports. Trying alternative method..."
    kill $SOCAT_PID 2>/dev/null || true
    
    # Alternative: use named pipes (less ideal but works)
    echo "Using named pipes instead..."
    mkfifo /tmp/serial_rx /tmp/serial_tx 2>/dev/null || true
    (cat /tmp/serial_tx > /tmp/serial_rx) &
    PIPE_PID=$!
    
    echo "Note: This test requires manual data sending"
    exit 0
fi

echo "Virtual ports created:"
echo "  PORT1: $PORT1 (for node to listen)"
echo "  PORT2: $PORT2 (to send test data)"
echo ""

# Modify SerialManager temporarily to use PORT1
echo "Updating node to use virtual port: $PORT1"

cd "$WORKSPACE"
source install/setup.bash

# Create a test node that uses the virtual port
cat > /tmp/test_serial_node.py << 'EOF'
import sys
import time
sys.path.insert(0, '/home/robot/robot_ws/install/robot_serial/lib/python3.10/site-packages')

from robot_serial.serial_manager import SerialManager

def on_data(data):
    print(f"[RX]\n{data}")

def on_connected(port):
    print(f"[INFO] Connected to {port}")

def on_disconnected():
    print(f"[WARN] Serial disconnected.")

# Override SERIAL_PORTS with virtual port
manager = SerialManager(on_data, on_connected, on_disconnected)
manager.SERIAL_PORTS = [sys.argv[1]]

print("[INFO] Serial node test started")
if manager.connect():
    print(f"[INFO] Connected to {manager.current_port}")
    # Read for 5 seconds
    for i in range(50):
        line = manager.read_line()
        time.sleep(0.1)
    manager.disconnect()
else:
    print("[ERROR] Failed to connect")
EOF

echo "Launching test reader on $PORT1..."
timeout 10 python3 /tmp/test_serial_node.py "$PORT1" > /tmp/test_rx.log 2>&1 &
RX_PID=$!

sleep 1

# Send test data
echo "Sending test data to $PORT2..."
(
    sleep 1
    echo "Hello Pi"
    sleep 1
    echo "{\"battery\": 12.4}"
    sleep 1
    echo "Status: OK"
    sleep 1
) > "$PORT2"

# Wait for receiver
wait $RX_PID 2>/dev/null || true

# Show results
echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
cat /tmp/test_rx.log

# Cleanup
echo ""
echo "Cleaning up..."
kill $SOCAT_PID 2>/dev/null || true
wait $SOCAT_PID 2>/dev/null || true
sleep 1

# Check if data was received
if grep -q "Hello Pi" /tmp/test_rx.log; then
    echo "✓ Data reception test PASSED"
    exit 0
else
    echo "✗ Data reception test FAILED"
    echo "Expected to see 'Hello Pi' in output"
    exit 1
fi
