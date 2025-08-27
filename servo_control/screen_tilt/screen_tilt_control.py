#!/usr/bin/env python3
"""
Screen Tilt Control System
Controls servo position using rotary encoder with button features
Based on working gpiozero implementation for Pi 5
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime

from gpiozero import Button
from adafruit_servokit import ServoKit
import smbus2
import board
import busio

# Try to import servo initialization helpers
try:
    from fixed_servo_init import initialize_servo_with_mux, ServoKitWithMux
    FIXED_SERVO_AVAILABLE = True
except ImportError:
    FIXED_SERVO_AVAILABLE = False
    print("Fixed servo init not available")

try:
    from mux_aware_servo import MuxAwareServoKit
    MUX_AWARE_AVAILABLE = True
except ImportError:
    MUX_AWARE_AVAILABLE = False

# GPIO Pin Configuration
ENCODER_CLK = 17
ENCODER_DT = 27
ENCODER_SW = 22

# File paths
CONFIG_FILE = Path(__file__).parent / "config.json"
STATE_FILE = Path(__file__).parent / "position_state.json"

class ScreenTiltController:
    """Main controller for screen tilt system"""
    
    def __init__(self):
        self.config = self.load_config()
        self.state = self.load_state()
        
        # Initialize servo with multiplexer support
        self.using_mux = False
        self.kit = None
        self.mux_servo = None
        self.fixed_servo = None
        
        # Try fixed servo initialization first (most reliable)
        if FIXED_SERVO_AVAILABLE:
            try:
                self.servo_channel = self.config['servo_channel']
                self.fixed_servo = initialize_servo_with_mux(
                    mux_channel=1, 
                    servo_channel=self.servo_channel
                )
                if self.fixed_servo:
                    self.using_mux = True
                    print(f"✓ Servo ready using fixed mux init")
                else:
                    print("Fixed servo init returned None")
            except Exception as e:
                print(f"Error with fixed servo init: {e}")
                self.fixed_servo = None
        
        # Try mux-aware initialization if fixed didn't work
        if not self.fixed_servo and MUX_AWARE_AVAILABLE:
            try:
                self.mux_servo = MuxAwareServoKit(mux_channel=1, mux_address=0x70)
                if self.mux_servo.initialize(retries=5):
                    self.servo_channel = self.config['servo_channel']
                    self.mux_servo.configure_servo(
                        self.servo_channel,
                        actuation_range=270,
                        min_pulse=500,
                        max_pulse=2500
                    )
                    self.using_mux = True
                    print(f"✓ Servo ready on channel {self.servo_channel} via mux-aware wrapper")
                else:
                    print("Failed to initialize servo with mux-aware wrapper")
                    self.mux_servo = None
            except Exception as e:
                print(f"Error with mux-aware servo init: {e}")
                self.mux_servo = None
        
        # Fallback to standard approach if mux-aware failed
        if not self.mux_servo:
            mux_address = 0x70
            for attempt in range(3):
                try:
                    # Try direct connection (no mux)
                    self.kit = ServoKit(channels=16, address=0x40)
                    self.servo_channel = self.config['servo_channel']
                    self.kit.servo[self.servo_channel].actuation_range = 270
                    self.kit.servo[self.servo_channel].set_pulse_width_range(500, 2500)
                    print(f"Servo initialized directly (no mux)")
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"Direct servo init attempt {attempt + 1} failed: {e}")
                        time.sleep(0.5)
                    else:
                        print(f"Warning: Could not initialize servo: {e}")
                        print("Running in simulation mode - encoder input will be tracked but no servo movement")
                        self.kit = None
        
        # Setup GPIO pins with proper pull-ups
        self.clk_pin = Button(ENCODER_CLK, pull_up=True, bounce_time=0.01)
        self.dt_pin = Button(ENCODER_DT, pull_up=True, bounce_time=0.01)
        self.sw_pin = Button(ENCODER_SW, pull_up=True, bounce_time=0.1)
        
        # Control variables
        self.current_angle = self.state.get('last_position', self.config['center_angle'])
        self.encoder_pos = 0
        self.mode = self.state.get('mode', self.config['default_mode'])
        self.last_clk_state = self.clk_pin.is_pressed
        
        # Button handling
        self.button_press_time = 0
        self.click_count = 0
        self.click_timer = None
        
        # Set initial position (if servo is connected)
        if self.fixed_servo:
            self.fixed_servo.set_angle(self.current_angle)
        elif self.mux_servo:
            self.mux_servo.set_servo_angle(self.servo_channel, self.current_angle)
        elif self.kit:
            try:
                self.kit.servo[self.servo_channel].angle = self.current_angle
            except:
                pass
        
        # Attach button handler
        self.sw_pin.when_pressed = self._button_pressed
        self.sw_pin.when_released = self._button_released
        
        print(f"Screen Tilt Controller initialized")
        print(f"Mode: {self.mode}, Position: {self.current_angle}°")
    
    def load_config(self):
        """Load or create configuration"""
        default_config = {
            "servo_channel": 0,
            "default_mode": "direct",
            "modes": {
                "direct": {"sensitivity": 5.0},  # Increased from 2.0
                "fine": {"sensitivity": 1.0},
                "range": {"sensitivity": 5.0, "min_angle": 90, "max_angle": 180}
            },
            "acceleration": True,
            "acceleration_threshold": 5,
            "acceleration_multiplier": 2.0,
            "min_angle": 0,
            "max_angle": 270,
            "center_angle": 250,
            "smooth_movement": False,  # Disabled for now
            "movement_speed": 0.01
        }
        
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # Save default config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def load_state(self):
        """Load saved state"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_state(self):
        """Save current state"""
        state = {
            "last_position": self.current_angle,
            "mode": self.mode,
            "timestamp": datetime.now().isoformat()
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    def update_servo(self):
        """Update servo based on encoder position"""
        # Get sensitivity based on mode
        if self.mode == "direct":
            sensitivity = self.config['modes']['direct']['sensitivity']
        elif self.mode == "fine":
            sensitivity = self.config['modes']['fine']['sensitivity']
        elif self.mode == "range":
            sensitivity = self.config['modes']['range']['sensitivity']
        else:
            sensitivity = 5.0
        
        # Calculate new angle
        new_angle = self.config['center_angle'] + (self.encoder_pos * sensitivity)
        
        # Apply mode-specific limits
        if self.mode == "range":
            range_config = self.config['modes']['range']
            new_angle = max(range_config['min_angle'], min(range_config['max_angle'], new_angle))
        else:
            new_angle = max(self.config['min_angle'], min(self.config['max_angle'], new_angle))
        
        # Update if changed
        if new_angle != self.current_angle:
            self.current_angle = new_angle
            
            # Use fixed servo if available (most reliable)
            if self.fixed_servo:
                if not self.fixed_servo.set_angle(self.current_angle):
                    print(f"Failed to set servo angle via fixed wrapper")
            elif self.mux_servo:
                if not self.mux_servo.set_servo_angle(self.servo_channel, self.current_angle):
                    print(f"Failed to set servo angle via mux wrapper")
            elif self.kit:
                # Direct servo control (no mux)
                try:
                    self.kit.servo[self.servo_channel].angle = self.current_angle
                except Exception as e:
                    print(f"Failed to set servo angle: {e}")
            
            print(f"Position: {self.encoder_pos} → Angle: {self.current_angle}°")
    
    def check_encoder(self):
        """Poll encoder state"""
        clk_state = self.clk_pin.is_pressed
        
        if clk_state != self.last_clk_state and clk_state == False:
            # CLK went from high to low
            if self.dt_pin.is_pressed != clk_state:
                self.encoder_pos += 1
            else:
                self.encoder_pos -= 1
            self.update_servo()
        
        self.last_clk_state = clk_state
    
    def _button_pressed(self):
        """Handle button press"""
        self.button_press_time = time.time()
    
    def _button_released(self):
        """Handle button release"""
        # Double-check it's really released (not noise)
        time.sleep(0.05)
        if not self.sw_pin.is_pressed:
            press_duration = time.time() - self.button_press_time
            
            if press_duration > 1.0:  # Long press
                self._handle_long_press()
            else:  # Short press
                self.click_count += 1
                
                # Cancel previous timer
                if self.click_timer:
                    self.click_timer.cancel()
                
                # Start new timer to detect end of clicks
                self.click_timer = threading.Timer(0.3, self._process_clicks)
                self.click_timer.start()
    
    def _process_clicks(self):
        """Process accumulated clicks"""
        if self.click_count == 1:
            self._handle_single_click()
        elif self.click_count == 2:
            self._handle_double_click()
        
        self.click_count = 0
    
    def _handle_single_click(self):
        """Single click - go to home position"""
        print(f"Going to home position ({self.config['center_angle']}°)")
        self.encoder_pos = 0
        self.update_servo()
    
    def _handle_double_click(self):
        """Double click - change mode"""
        modes = ['direct', 'fine', 'range']
        current_index = modes.index(self.mode)
        self.mode = modes[(current_index + 1) % len(modes)]
        print(f"Mode changed to: {self.mode}")
        
        # Reset encoder position when changing modes
        self.encoder_pos = int((self.current_angle - self.config['center_angle']) / self.config['modes'][self.mode]['sensitivity'])
    
    def _handle_long_press(self):
        """Long press - save position"""
        self.save_state()
        print(f"Position saved: {self.current_angle}°")
    
    def run(self):
        """Main run loop"""
        print("\nControls:")
        print("- Rotate encoder to tilt screen")
        print("- Single click: Go to home position")
        print("- Double click: Change mode (direct → fine → range)")
        print("- Long press: Save position")
        print("- Ctrl+C to exit\n")
        
        try:
            while True:
                self.check_encoder()
                time.sleep(0.001)  # 1ms polling rate
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.save_state()
            print("Position saved. Goodbye!")


if __name__ == "__main__":
    controller = ScreenTiltController()
    controller.run()