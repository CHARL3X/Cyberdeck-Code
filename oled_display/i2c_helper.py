#!/usr/bin/env python3
"""
I2C Helper Module - Support for TCA9548A I2C Multiplexer
Handles both direct I2C connections and multiplexed connections
"""

import time
import smbus2
from typing import Optional, Tuple
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306


class I2CMultiplexer:
    """TCA9548A I2C Multiplexer control"""
    
    def __init__(self, bus: int = 1, address: int = 0x70):
        """
        Initialize multiplexer connection
        
        Args:
            bus: I2C bus number (default 1 for RPi)
            address: Multiplexer I2C address (default 0x70)
        """
        self.bus = smbus2.SMBus(bus)
        self.address = address
        self.current_channel = None
        
    def select_channel(self, channel: int) -> bool:
        """
        Select a specific channel on the multiplexer
        
        Args:
            channel: Channel number (0-7)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0 <= channel <= 7:
            print(f"Invalid channel: {channel}. Must be 0-7")
            return False
            
        try:
            # Write the channel selection byte
            # Each bit represents a channel (bit 0 = channel 0, etc.)
            channel_byte = 1 << channel
            self.bus.write_byte(self.address, channel_byte)
            self.current_channel = channel
            time.sleep(0.01)  # Small delay for channel switch
            return True
        except Exception as e:
            print(f"Failed to select multiplexer channel {channel}: {e}")
            return False
    
    def disable_all_channels(self):
        """Disable all multiplexer channels"""
        try:
            self.bus.write_byte(self.address, 0x00)
            self.current_channel = None
        except Exception as e:
            print(f"Failed to disable multiplexer channels: {e}")
    
    def is_available(self) -> bool:
        """Check if multiplexer is available at expected address"""
        try:
            # Try to read from the multiplexer
            self.bus.read_byte(self.address)
            return True
        except:
            return False


def scan_i2c_bus(bus: int = 1) -> list:
    """
    Scan I2C bus for connected devices
    
    Args:
        bus: I2C bus number
        
    Returns:
        List of detected I2C addresses
    """
    devices = []
    try:
        with smbus2.SMBus(bus) as i2c_bus:
            for address in range(0x03, 0x78):
                try:
                    i2c_bus.read_byte(address)
                    devices.append(address)
                except:
                    pass
    except Exception as e:
        print(f"Error scanning I2C bus: {e}")
    
    return devices


def detect_oled_direct(port: int = 1, address: int = 0x3C) -> Optional[ssd1306]:
    """
    Try to detect and initialize OLED directly (no multiplexer)
    
    Args:
        port: I2C port number
        address: OLED I2C address
        
    Returns:
        Initialized OLED device or None
    """
    try:
        serial = i2c(port=port, address=address)
        device = ssd1306(serial, width=128, height=64)
        print(f"✓ OLED found directly at 0x{address:02X}")
        return device
    except Exception as e:
        return None


def detect_oled_multiplexed(port: int = 1, mux_address: int = 0x70, 
                           mux_channel: int = 0, oled_address: int = 0x3C) -> Optional[ssd1306]:
    """
    Try to detect and initialize OLED through multiplexer
    
    Args:
        port: I2C port number
        mux_address: Multiplexer I2C address
        mux_channel: Multiplexer channel where OLED is connected
        oled_address: OLED I2C address
        
    Returns:
        Initialized OLED device or None
    """
    try:
        # Initialize multiplexer
        mux = I2CMultiplexer(port, mux_address)
        
        if not mux.is_available():
            return None
        
        # Select the channel
        if not mux.select_channel(mux_channel):
            return None
        
        # Try to initialize OLED on selected channel
        serial = i2c(port=port, address=oled_address)
        device = ssd1306(serial, width=128, height=64)
        print(f"✓ OLED found via multiplexer (0x{mux_address:02X}) on channel {mux_channel} at 0x{oled_address:02X}")
        return device
        
    except Exception as e:
        return None


def auto_detect_oled(port: int = 1, oled_address: int = 0x3C, 
                     mux_address: int = 0x70, mux_channel: int = 0) -> Tuple[Optional[ssd1306], str]:
    """
    Auto-detect OLED with fallback from direct to multiplexed connection
    
    Args:
        port: I2C port number
        oled_address: Expected OLED I2C address
        mux_address: Multiplexer I2C address (if present)
        mux_channel: Multiplexer channel to check
        
    Returns:
        Tuple of (device, connection_type) where connection_type is 'direct', 'multiplexed', or 'none'
    """
    print("Detecting OLED display...")
    
    # First try direct connection
    device = detect_oled_direct(port, oled_address)
    if device:
        return device, 'direct'
    
    print(f"No direct OLED at 0x{oled_address:02X}, checking for multiplexer...")
    
    # Try multiplexed connection
    device = detect_oled_multiplexed(port, mux_address, mux_channel, oled_address)
    if device:
        return device, 'multiplexed'
    
    # Scan bus to help with debugging
    print("\nI2C bus scan results:")
    devices = scan_i2c_bus(port)
    if devices:
        for addr in devices:
            print(f"  Device found at 0x{addr:02X}")
    else:
        print("  No I2C devices found")
    
    return None, 'none'


def initialize_display_with_fallback(config) -> Optional[ssd1306]:
    """
    Initialize display with automatic fallback support
    
    Args:
        config: AnimationConfig object with display settings
        
    Returns:
        Initialized OLED device or None
    """
    device, connection_type = auto_detect_oled(
        port=config.i2c_port,
        oled_address=config.i2c_address
    )
    
    if device and hasattr(config, 'rotation') and config.rotation:
        # Apply rotation if specified
        device.rotate = config.rotation
    
    if not device:
        print(f"Failed to initialize display at 0x{config.i2c_address:02X}")
        print("Please check connections and I2C configuration")
    else:
        # If device is multiplexed, wrap it in MuxSafeOLED
        if connection_type == 'multiplexed':
            try:
                from .mux_safe_oled import MuxSafeOLED
                device = MuxSafeOLED(device, mux_channel=0)
                print("Wrapped OLED in multiplexer-safe wrapper")
            except ImportError:
                pass  # Continue without wrapper
    
    return device