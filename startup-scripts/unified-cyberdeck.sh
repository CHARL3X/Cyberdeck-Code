#!/bin/bash
# Unified Cyberdeck Startup Script
# Single process managing both OLED and servo

echo "Starting Unified Cyberdeck Controller..."
echo "====================================="

# Change to Cyberdeck-Code directory for proper imports
cd /home/morph/01_Code/Cyberdeck-Code

# Kill any existing processes
pkill -f unified_cyberdeck_controller.py 2>/dev/null
pkill -f oled-spectrum 2>/dev/null  
pkill -f screen-tilt 2>/dev/null
sleep 1

# Run unified controller
exec /usr/bin/python3 unified_cyberdeck_controller.py