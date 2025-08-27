#!/usr/bin/env python3
"""
Servo Hardware Diagnostic Tool
Checks for PCA9685 servo controller connectivity
"""

import smbus2
import time
import subprocess
import sys

def check_direct_connection():
    """Check if PCA9685 is directly connected (no multiplexer)"""
    print("\n1. Checking direct I2C connection...")
    result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
    
    if '40' in result.stdout:
        print("✓ PCA9685 found directly at 0x40!")
        return True
    else:
        print("✗ PCA9685 not found on direct I2C bus")
        return False

def check_multiplexer_channels():
    """Check all multiplexer channels for PCA9685"""
    print("\n2. Checking multiplexer channels...")
    
    try:
        bus = smbus2.SMBus(1)
        mux_address = 0x70
        
        # Check if multiplexer exists
        try:
            bus.read_byte(mux_address)
            print(f"✓ Multiplexer found at 0x{mux_address:02x}")
        except:
            print(f"✗ No multiplexer at 0x{mux_address:02x}")
            return False
        
        # Scan each channel
        for channel in range(8):
            try:
                # Select channel
                bus.write_byte(mux_address, 1 << channel)
                time.sleep(0.05)
                
                # Try to read from PCA9685 at 0x40
                try:
                    bus.read_byte(0x40)
                    print(f"✓ PCA9685 found on multiplexer channel {channel}!")
                    bus.close()
                    return channel
                except:
                    pass
                    
            except Exception as e:
                print(f"  Error checking channel {channel}: {e}")
        
        bus.close()
        print("✗ PCA9685 not found on any multiplexer channel")
        return None
        
    except Exception as e:
        print(f"Error accessing I2C: {e}")
        return None

def test_servo_initialization(channel=None):
    """Try to initialize servo with adafruit library"""
    print("\n3. Testing servo initialization...")
    
    try:
        from adafruit_servokit import ServoKit
        
        if channel is not None:
            # Use multiplexer
            print(f"  Switching to multiplexer channel {channel}...")
            bus = smbus2.SMBus(1)
            bus.write_byte(0x70, 1 << channel)
            time.sleep(0.05)
            bus.close()
        
        # Try to initialize
        kit = ServoKit(channels=16, address=0x40)
        print("✓ ServoKit initialized successfully!")
        
        # Try to move servo
        print("  Testing servo movement on channel 0...")
        kit.servo[0].angle = 90
        time.sleep(0.5)
        kit.servo[0].angle = 180
        time.sleep(0.5)
        kit.servo[0].angle = 135
        print("✓ Servo commands sent successfully!")
        
        return True
        
    except ImportError:
        print("✗ adafruit_servokit not installed")
        print("  Install with: pip3 install adafruit-circuitpython-servokit")
        return False
    except Exception as e:
        print(f"✗ Failed to initialize servo: {e}")
        return False

def main():
    print("=" * 50)
    print("SERVO HARDWARE DIAGNOSTIC")
    print("=" * 50)
    
    # Check direct connection
    direct = check_direct_connection()
    
    # Check multiplexer channels
    mux_channel = check_multiplexer_channels()
    
    # Test initialization
    if direct:
        test_servo_initialization()
    elif mux_channel is not None:
        test_servo_initialization(mux_channel)
    
    # Troubleshooting guide
    print("\n" + "=" * 50)
    print("TROUBLESHOOTING GUIDE")
    print("=" * 50)
    
    if not direct and mux_channel is None:
        print("\n⚠️  PCA9685 servo controller not detected!")
        print("\nPlease check:")
        print("1. POWER:")
        print("   - PCA9685 V+ connected to 5V")
        print("   - PCA9685 VCC connected to 3.3V")
        print("   - PCA9685 GND connected to ground")
        print("   - External servo power connected to servo power terminals")
        print("\n2. I2C CONNECTIONS:")
        print("   - PCA9685 SDA connected to Pi SDA (GPIO 2)")
        print("   - PCA9685 SCL connected to Pi SCL (GPIO 3)")
        print("   OR if using multiplexer:")
        print("   - PCA9685 connected to multiplexer channel (SD1/SC1, SD2/SC2, etc)")
        print("\n3. ADDRESS JUMPERS:")
        print("   - Default address is 0x40 (no jumpers)")
        print("   - Check A0-A5 jumpers aren't accidentally bridged")
        print("\n4. HARDWARE:")
        print("   - Try different I2C cables")
        print("   - Check for loose connections")
        print("   - Verify PCA9685 board isn't damaged")
    
    elif mux_channel is not None:
        print(f"\n✓ PCA9685 detected on multiplexer channel {mux_channel}")
        print(f"\nUpdate your code to use channel {mux_channel}:")
        print(f"  bus.write_byte(0x70, 1 << {mux_channel})")
    
    else:
        print("\n✓ PCA9685 detected and working!")

if __name__ == "__main__":
    main()