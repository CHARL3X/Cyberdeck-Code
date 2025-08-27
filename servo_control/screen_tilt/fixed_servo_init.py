#!/usr/bin/env python3
"""
Fixed servo initialization that properly handles multiplexer
The key is to monkey-patch the I2C bus to maintain mux channel
"""

import smbus2
import time
import busio
import board
from adafruit_servokit import ServoKit

class MuxPersistentI2C:
    """I2C wrapper that maintains multiplexer channel"""
    
    def __init__(self, mux_address=0x70, mux_channel=1):
        self.mux_address = mux_address
        self.mux_channel = mux_channel
        self._ensure_channel()
    
    def _ensure_channel(self):
        """Ensure mux is on correct channel"""
        try:
            bus = smbus2.SMBus(1)
            bus.write_byte(self.mux_address, 1 << self.mux_channel)
            bus.close()
            time.sleep(0.01)
        except:
            pass

def initialize_servo_with_mux(mux_channel=1, servo_channel=0):
    """Initialize servo through multiplexer"""
    
    # First, set the multiplexer channel
    print(f"Setting mux to channel {mux_channel}...")
    bus = smbus2.SMBus(1)
    bus.write_byte(0x70, 1 << mux_channel)
    bus.close()
    time.sleep(0.1)
    
    # Verify PCA9685 is visible
    bus = smbus2.SMBus(1)
    try:
        bus.read_byte(0x40)
        print("✓ PCA9685 detected at 0x40")
    except Exception as e:
        print(f"✗ PCA9685 not found: {e}")
        bus.close()
        return None
    bus.close()
    
    # Now initialize ServoKit
    # The trick is that busio.I2C will use the currently selected mux channel
    try:
        # Create I2C bus (will use currently selected mux channel)
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Small delay to ensure bus is ready
        time.sleep(0.1)
        
        # Initialize ServoKit with our I2C bus
        kit = ServoKit(channels=16, i2c=i2c, address=0x40)
        
        # Configure servo
        kit.servo[servo_channel].actuation_range = 270
        kit.servo[servo_channel].set_pulse_width_range(500, 2500)
        
        print(f"✓ Servo initialized on channel {servo_channel}")
        
        # Return mux to OLED channel after init
        bus = smbus2.SMBus(1)
        bus.write_byte(0x70, 1 << 0)  # Channel 0 for OLED
        bus.close()
        time.sleep(0.01)
        
        # Return a wrapper that maintains mux channel for operations
        return ServoKitWithMux(kit, mux_channel, servo_channel)
        
    except Exception as e:
        print(f"✗ Failed to initialize ServoKit: {e}")
        return None

class ServoKitWithMux:
    """Wrapper that ensures mux channel before servo operations"""
    
    def __init__(self, kit, mux_channel, servo_channel):
        self.kit = kit
        self.mux_channel = mux_channel
        self.servo_channel = servo_channel
        self.mux_address = 0x70
    
    def ensure_mux_channel(self):
        """Ensure mux is on our channel"""
        try:
            bus = smbus2.SMBus(1)
            bus.write_byte(self.mux_address, 1 << self.mux_channel)
            bus.close()
            time.sleep(0.002)
        except:
            pass
    
    def set_angle(self, angle):
        """Set servo angle with mux management"""
        try:
            # Switch to servo channel
            self.ensure_mux_channel()
            
            # Set servo angle
            self.kit.servo[self.servo_channel].angle = angle
            time.sleep(0.005)  # Small delay after move
            
            return True
        except Exception as e:
            print(f"Failed to set angle: {e}")
            return False
        finally:
            # ALWAYS return to OLED channel, even on error
            try:
                bus = smbus2.SMBus(1)
                bus.write_byte(self.mux_address, 1 << 0)  # Channel 0 for OLED
                bus.close()
            except:
                pass

if __name__ == "__main__":
    # Test the initialization
    servo = initialize_servo_with_mux(mux_channel=1, servo_channel=0)
    if servo:
        print("Testing servo movement...")
        servo.set_angle(180)
        time.sleep(1)
        servo.set_angle(90)
        time.sleep(1)
        servo.set_angle(135)
        print("✓ Test complete!")
    else:
        print("✗ Failed to initialize servo")