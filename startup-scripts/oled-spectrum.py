#!/usr/bin/env python3
"""
OLED Spectrum Analyzer Startup Script
Runs the spectrum analyzer animation continuously without any user input
Perfect for autorun on boot
"""

import sys
import os

# Add parent directory to path to import oled modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the controller
from oled_display.oled_controller_pro import OLEDController, AnimationConfig, AnimationType

def main():
    """Main entry point - runs spectrum animation in loop"""
    print("Starting OLED Spectrum Analyzer...")
    
    # Create configuration with default settings
    config = AnimationConfig(
        i2c_address=0x3C,
        i2c_port=1,
        fps=20,
        rotation=0
    )
    
    # Create controller
    controller = OLEDController(config)
    
    # Initialize display
    if not controller.initialize():
        print("Failed to initialize OLED display")
        sys.exit(1)
    
    try:
        # Run spectrum animation in continuous loop
        print("Running Spectrum animation (will run continuously)")
        while True:
            controller.run_single(AnimationType.SPECTRUM)
    except KeyboardInterrupt:
        print("\nStopping spectrum animation...")
    except Exception as e:
        print(f"Error running spectrum animation: {e}")
    finally:
        controller.stop()
        print("OLED display cleared")

if __name__ == "__main__":
    main()