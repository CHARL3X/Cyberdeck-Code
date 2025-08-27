#!/usr/bin/env python3
"""
Multiplexer-safe OLED wrapper
Ensures multiplexer is on correct channel before each OLED operation
"""

import smbus2
import time
from luma.oled.device import ssd1306

class MuxSafeOLED:
    """Wrapper for OLED device that handles multiplexer switching"""
    
    def __init__(self, device, mux_bus=None, mux_addr=0x70, mux_channel=0):
        """
        Initialize multiplexer-safe OLED wrapper
        
        Args:
            device: The actual OLED device
            mux_bus: SMBus instance (will create if None)
            mux_addr: Multiplexer I2C address
            mux_channel: Channel where OLED is connected
        """
        self.device = device
        self.mux_channel = mux_channel
        self.mux_addr = mux_addr
        self.mux_bus = mux_bus or smbus2.SMBus(1)
        self._needs_mux = self._check_mux_needed()
        
    def _check_mux_needed(self):
        """Check if we need to manage multiplexer"""
        try:
            self.mux_bus.read_byte(self.mux_addr)
            return True
        except:
            return False
    
    def _ensure_channel(self):
        """Ensure multiplexer is on the correct channel"""
        if self._needs_mux:
            try:
                # Select our channel
                self.mux_bus.write_byte(self.mux_addr, 1 << self.mux_channel)
                time.sleep(0.001)  # Small delay for channel switch
            except:
                pass  # Continue even if mux fails
    
    def display(self, image):
        """Display image with mux safety"""
        self._ensure_channel()
        return self.device.display(image)
    
    def clear(self):
        """Clear display with mux safety"""
        self._ensure_channel()
        return self.device.clear()
    
    def show(self):
        """Show display with mux safety"""
        self._ensure_channel()
        if hasattr(self.device, 'show'):
            return self.device.show()
    
    def hide(self):
        """Hide display with mux safety"""
        self._ensure_channel()
        if hasattr(self.device, 'hide'):
            return self.device.hide()
    
    def contrast(self, value):
        """Set contrast with mux safety"""
        self._ensure_channel()
        if hasattr(self.device, 'contrast'):
            return self.device.contrast(value)
    
    def __getattr__(self, name):
        """Pass through other attributes to the device"""
        return getattr(self.device, name)