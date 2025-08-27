#!/usr/bin/env python3
"""
Multiplexer-aware servo initialization
Maintains mux channel during ServoKit initialization
"""

import smbus2
import time
from adafruit_servokit import ServoKit
from contextlib import contextmanager

class MuxAwareServoKit:
    """ServoKit wrapper that maintains multiplexer channel"""
    
    def __init__(self, mux_channel=1, mux_address=0x70, pca_address=0x40, channels=16):
        self.mux_channel = mux_channel
        self.mux_address = mux_address
        self.pca_address = pca_address
        self.channels = channels
        self.kit = None
        self.mux_bus = None
        
    def initialize(self, retries=5):
        """Initialize servo with multiplexer management"""
        for attempt in range(retries):
            try:
                # Open bus and keep it open
                self.mux_bus = smbus2.SMBus(1)
                
                # Select the mux channel
                self.mux_bus.write_byte(self.mux_address, 1 << self.mux_channel)
                time.sleep(0.05)  # Wait for mux to stabilize
                
                # Verify PCA9685 is visible
                try:
                    self.mux_bus.read_byte(self.pca_address)
                except:
                    raise Exception(f"PCA9685 not found at 0x{self.pca_address:02X} on mux channel {self.mux_channel}")
                
                # Initialize ServoKit while mux is set
                # The key is the mux stays on channel during init
                self.kit = ServoKit(channels=self.channels, address=self.pca_address)
                
                print(f"✓ Servo initialized via mux channel {self.mux_channel} (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                if self.mux_bus:
                    self.mux_bus.close()
                    self.mux_bus = None
                
                if attempt < retries - 1:
                    print(f"Servo init attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(0.5)
                else:
                    print(f"Failed to initialize servo after {retries} attempts: {e}")
                    return False
        
        return False
    
    @contextmanager
    def mux_channel_selected(self):
        """Context manager to ensure mux channel is selected for operations"""
        if self.mux_bus:
            try:
                # Select channel
                self.mux_bus.write_byte(self.mux_address, 1 << self.mux_channel)
                time.sleep(0.002)
                yield
            finally:
                # Return to OLED channel
                try:
                    self.mux_bus.write_byte(self.mux_address, 1 << 0)
                    time.sleep(0.002)
                except:
                    pass
        else:
            yield
    
    def set_servo_angle(self, servo_num, angle):
        """Set servo angle with mux management"""
        if not self.kit:
            return False
            
        with self.mux_channel_selected():
            try:
                self.kit.servo[servo_num].angle = angle
                return True
            except Exception as e:
                print(f"Failed to set servo angle: {e}")
                return False
    
    def configure_servo(self, servo_num, actuation_range=270, min_pulse=500, max_pulse=2500):
        """Configure servo parameters with mux management"""
        if not self.kit:
            return False
            
        with self.mux_channel_selected():
            try:
                self.kit.servo[servo_num].actuation_range = actuation_range
                self.kit.servo[servo_num].set_pulse_width_range(min_pulse, max_pulse)
                return True
            except Exception as e:
                print(f"Failed to configure servo: {e}")
                return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.mux_bus:
            try:
                # Return to OLED channel before closing
                self.mux_bus.write_byte(self.mux_address, 1 << 0)
                self.mux_bus.close()
            except:
                pass
            self.mux_bus = None