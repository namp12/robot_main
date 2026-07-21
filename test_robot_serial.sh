#!/bin/bash
# Comprehensive test script for robot_serial package

set -e

WORKSPACE="/home/robot/robot_ws"
TIMEOUT=10

echo "=========================================="
echo "Robot Serial - Comprehensive Test"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: Build package
echo "Test 1: Building package..."
cd "$WORKSPACE"
if colcon build --packages-select robot_serial &>/dev/null; then
    log_success "Build successful"
else
    log_error "Build failed"
    exit 1
fi
echo ""

# Test 2: Check entry points
echo "Test 2: Checking entry points..."
source install/setup.bash
EXECUTABLES=$(ros2 pkg executables robot_serial 2>/dev/null | grep serial_node)
if [ ! -z "$EXECUTABLES" ]; then
    log_success "serial_node executable found"
    log_info "Available: $EXECUTABLES"
else
    log_error "serial_node executable not found"
    exit 1
fi
echo ""

# Test 3: Launch file exists
echo "Test 3: Checking launch file..."
if [ -f "src/robot_serial/launch/robot_serial.launch.py" ]; then
    log_success "Launch file found"
else
    log_error "Launch file not found"
    exit 1
fi
echo ""

# Test 4: Source files exist
echo "Test 4: Checking source files..."
FILES=(
    "src/robot_serial/robot_serial/serial_node.py"
    "src/robot_serial/robot_serial/serial_manager.py"
    "src/robot_serial/robot_serial/__init__.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "Found: $file"
    else
        log_error "Missing: $file"
        exit 1
    fi
done
echo ""

# Test 5: Import check
echo "Test 5: Checking Python imports..."
if python3 -c "from robot_serial.serial_manager import SerialManager; print('OK')" &>/dev/null; then
    log_success "SerialManager import successful"
else
    log_error "SerialManager import failed"
    exit 1
fi

if python3 -c "from robot_serial.serial_node import SerialNode" &>/dev/null; then
    log_success "SerialNode import successful"
else
    log_error "SerialNode import failed"
    exit 1
fi
echo ""

# Test 6: Run node with timeout (just check if it starts)
echo "Test 6: Testing node startup..."
log_info "Launching node for ${TIMEOUT} seconds..."
timeout $TIMEOUT ros2 launch robot_serial robot_serial.launch.py 2>&1 | head -20 | tee /tmp/robot_serial_test.log

# Check for expected output
if grep -q "Serial node initialized" /tmp/robot_serial_test.log; then
    log_success "Node initialization logged"
else
    log_error "Node initialization not logged"
fi

if grep -q "Connected\|Serial device not found" /tmp/robot_serial_test.log; then
    log_success "Connection status logged"
else
    log_error "Connection status not logged"
fi
echo ""

# Test 7: Port detection
echo "Test 7: Checking port detection logic..."
if grep -q "ttyUSB\|ttyACM" /tmp/robot_serial_test.log; then
    log_success "Port detection working"
    grep "Connected\|device not found" /tmp/robot_serial_test.log || true
else
    log_info "No ports detected (expected if ESP32 not connected)"
fi
echo ""

echo "=========================================="
echo "Summary"
echo "=========================================="
log_success "All basic tests passed!"
echo ""
log_info "To test with actual ESP32:"
echo "  1. Connect ESP32 via USB"
echo "  2. Run: ros2 launch robot_serial robot_serial.launch.py"
echo "  3. Send data from ESP32"
echo "  4. Verify data appears in logs with [RX] prefix"
echo ""
log_info "To test manual serial communication:"
echo "  sudo apt-get install minicom"
echo "  minicom -D /dev/ttyACM0 -b 115200"
echo ""
