#!/bin/bash
# Cyberdeck Safe Startup Script
# Runs components with proper mux coordination and timing
# Adds delays and ensures OLED has priority

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Cyberdeck Components (Safe Mode)..."
echo "========================================="
echo ""

# Kill any existing instances
echo "Cleaning up any existing processes..."
pkill -f "oled-spectrum.py" 2>/dev/null
pkill -f "screen-tilt.py" 2>/dev/null
sleep 2

# Function to run a Python script in background with logging
run_component() {
    local script_name=$1
    local component_name=$2
    local log_file="/tmp/${script_name%.py}.log"
    
    if [ -f "$SCRIPT_DIR/$script_name" ]; then
        echo "Starting $component_name..."
        # Run with output to log file for debugging
        python3 "$SCRIPT_DIR/$script_name" > "$log_file" 2>&1 &
        local pid=$!
        echo "$component_name started (PID: $pid, Log: $log_file)"
        echo "$pid"
    else
        echo "Warning: $script_name not found"
        echo "0"
    fi
}

# Start OLED spectrum analyzer FIRST and give it time to stabilize
OLED_PID=$(run_component "oled-spectrum.py" "OLED Spectrum Analyzer")

# Important: Give OLED plenty of time to initialize and claim channel 0
echo "Waiting for OLED to initialize..."
sleep 5

# Now start screen tilt control
SERVO_PID=$(run_component "screen-tilt.py" "Screen Tilt Control")

# Give servo time to initialize
sleep 3

echo ""
echo "========================================="
echo "All components started successfully!"
echo "========================================="
echo ""
echo "Component PIDs:"
echo "  OLED Spectrum:  $OLED_PID"
echo "  Screen Tilt:    $SERVO_PID"
echo ""
echo "Logs available at:"
echo "  OLED: /tmp/oled-spectrum.log"
echo "  Servo: /tmp/screen-tilt.log"
echo ""
echo "To stop all: pkill -f 'python3.*Cyberdeck-Code'"
echo ""

# Monitor processes
monitor_processes() {
    while true; do
        # Check if OLED is still running
        if ! kill -0 $OLED_PID 2>/dev/null; then
            echo "WARNING: OLED process died! Check /tmp/oled-spectrum.log"
            break
        fi
        
        # Check if Servo is still running
        if ! kill -0 $SERVO_PID 2>/dev/null; then
            echo "WARNING: Servo process died! Check /tmp/screen-tilt.log"
            # Don't break - OLED can continue without servo
        fi
        
        sleep 5
    done
}

# Optional: Monitor in background
monitor_processes &

# Wait for processes
wait