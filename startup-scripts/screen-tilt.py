#!/usr/bin/env python3
"""
Screen Tilt Control Startup Script
Runs the screen tilt servo control without any user input
Loads last saved position and mode automatically
"""

import sys
import os
import signal
import time

# Add parent directory and screen_tilt directory to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'servo_control', 'screen_tilt'))

# Import directly since we added the directory to path
from screen_tilt_control import ScreenTiltController

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutdown signal received, saving position...")
    if hasattr(signal_handler, 'controller'):
        signal_handler.controller.save_state()
    sys.exit(0)

def main():
    """Main entry point - runs screen tilt control"""
    print("Starting Screen Tilt Control...")
    print("Encoder control active - no terminal input required")
    
    # Create and initialize controller
    controller = ScreenTiltController()
    
    # Store controller reference for signal handler
    signal_handler.controller = controller
    
    # Setup signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Display startup info (but don't wait for input)
    print(f"Mode: {controller.mode}, Position: {controller.current_angle}°")
    print("Controls via rotary encoder:")
    print("- Rotate: Adjust screen angle")
    print("- Click: Home position")
    print("- Double-click: Change mode")
    print("- Long press: Save position")
    
    try:
        # Main control loop - runs forever
        while True:
            controller.check_encoder()
            time.sleep(0.001)  # 1ms polling rate
            
    except Exception as e:
        print(f"Error in screen tilt control: {e}")
        controller.save_state()
    finally:
        controller.save_state()
        print("Screen tilt control stopped")

if __name__ == "__main__":
    main()