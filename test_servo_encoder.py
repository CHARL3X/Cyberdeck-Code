#!/usr/bin/env python3
"""
Simple test script for servo control with rotary encoder
Tests basic functionality without GPIO conflicts
"""

from adafruit_servokit import ServoKit
import smbus2
import time
import lgpio

# Encoder pins
ENCODER_CLK = 17
ENCODER_DT = 27
ENCODER_SW = 22

# Initialize lgpio for Pi 5
h = lgpio.gpiochip_open(4)  # Pi 5 uses gpiochip4

# Initialize servo
print("Initializing servo...")
try:
    # Try direct connection first
    kit = ServoKit(channels=16, address=0x40)
    print("Servo connected directly")
    using_mux = False
except:
    try:
        # Try via multiplexer
        bus = smbus2.SMBus(1)
        bus.write_byte(0x70, 1 << 1)  # Channel 1
        time.sleep(0.05)
        bus.close()
        
        kit = ServoKit(channels=16, address=0x40)
        print("Servo connected via multiplexer")
        using_mux = True
    except Exception as e:
        print(f"Failed to initialize servo: {e}")
        exit(1)

# Configure servo
servo_channel = 0
kit.servo[servo_channel].actuation_range = 270
kit.servo[servo_channel].set_pulse_width_range(500, 2500)

# Setup GPIO with lgpio for Pi 5
lgpio.gpio_claim_input(h, ENCODER_CLK, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, ENCODER_DT, lgpio.SET_PULL_UP)
lgpio.gpio_claim_input(h, ENCODER_SW, lgpio.SET_PULL_UP)

# Variables
current_angle = 135
encoder_pos = 0
last_clk = lgpio.gpio_read(h, ENCODER_CLK)

def move_servo(angle):
    """Move servo to specified angle"""
    global using_mux
    
    if using_mux:
        # Switch to servo channel
        bus = smbus2.SMBus(1)
        bus.write_byte(0x70, 1 << 1)
        time.sleep(0.01)
        bus.close()
    
    kit.servo[servo_channel].angle = angle
    
    if using_mux:
        # Switch back to OLED channel
        bus = smbus2.SMBus(1)
        bus.write_byte(0x70, 1 << 0)
        bus.close()

print(f"Servo test ready! Current angle: {current_angle}°")
print("Controls:")
print("  Rotate encoder: Change angle")
print("  Press button: Reset to center (135°)")
print("  Ctrl+C: Exit")

# Set initial position
move_servo(current_angle)

try:
    while True:
        # Read encoder
        clk = lgpio.gpio_read(h, ENCODER_CLK)
        dt = lgpio.gpio_read(h, ENCODER_DT)
        sw = lgpio.gpio_read(h, ENCODER_SW)
        
        # Check rotation
        if clk != last_clk:
            if dt != clk:
                encoder_pos += 1
                current_angle = min(270, current_angle + 5)
            else:
                encoder_pos -= 1
                current_angle = max(0, current_angle - 5)
            
            print(f"Position: {encoder_pos} → Angle: {current_angle}°")
            move_servo(current_angle)
            
        last_clk = clk
        
        # Check button press
        if sw == 0:
            print("Button pressed - resetting to center")
            current_angle = 135
            encoder_pos = 0
            move_servo(current_angle)
            time.sleep(0.5)  # Debounce
        
        time.sleep(0.001)  # Small delay to reduce CPU usage
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    lgpio.gpiochip_close(h)
    print("GPIO cleaned up")