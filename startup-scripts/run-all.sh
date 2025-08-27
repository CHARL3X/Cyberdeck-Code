#!/bin/bash
# Cyberdeck Master Startup Script
# Runs all cyberdeck components without requiring terminal input
# Can be added to autorun/startup applications

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Cyberdeck Components..."

# Function to run a Python script in background
run_component() {
    local script_name=$1
    local component_name=$2
    
    if [ -f "$SCRIPT_DIR/$script_name" ]; then
        echo "Starting $component_name..."
        python3 "$SCRIPT_DIR/$script_name" &
        echo "$component_name started (PID: $!)"
    else
        echo "Warning: $script_name not found"
    fi
}

# Start OLED spectrum analyzer
run_component "oled-spectrum.py" "OLED Spectrum Analyzer"

# Add small delay to ensure OLED starts first
sleep 2

# Start screen tilt control
run_component "screen-tilt.py" "Screen Tilt Control"

echo ""
echo "All components started successfully!"
echo "Components are running in background."
echo ""
echo "To stop all components, run: pkill -f 'python3.*Cyberdeck-Code'"
echo ""

# Keep the script running if needed (optional)
# Uncomment the following line if you want the script to wait
# wait