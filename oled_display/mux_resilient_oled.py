#!/usr/bin/env python3
"""
Multiplexer-resilient OLED wrapper
Periodically ensures the mux is on the correct channel
Recovers from channel switches by other components
"""

import smbus2
import time
import threading
from luma.oled.device import ssd1306

class ResilientMuxOLED:
    """OLED wrapper that's resilient to mux channel changes"""
    
    def __init__(self, device, mux_addr=0x70, mux_channel=0, recovery_interval=0.5):
        """
        Initialize resilient OLED wrapper
        
        Args:
            device: The actual OLED device
            mux_addr: Multiplexer I2C address
            mux_channel: Channel where OLED is connected
            recovery_interval: How often to ensure correct channel (seconds)
        """
        self.device = device
        self.mux_channel = mux_channel
        self.mux_addr = mux_addr
        self.recovery_interval = recovery_interval
        self.last_ensure_time = 0
        self.operation_count = 0
        self.bus_lock = threading.Lock()
        
        # Try to detect if mux is present
        self._mux_available = self._check_mux()
        
        if self._mux_available:
            print(f"Resilient OLED: Mux detected at 0x{mux_addr:02X}, using channel {mux_channel}")
            self._ensure_channel()
        else:
            print("Resilient OLED: No mux detected, using direct connection")
    
    def _check_mux(self):
        """Check if multiplexer is available"""
        try:
            with smbus2.SMBus(1) as bus:
                bus.read_byte(self.mux_addr)
                return True
        except:
            return False
    
    def _ensure_channel(self, force=False):
        """
        Ensure multiplexer is on the correct channel
        
        Args:
            force: Force channel selection even if recently done
        """
        if not self._mux_available:
            return True
            
        current_time = time.time()
        
        # Only ensure channel if enough time has passed or forced
        if not force and (current_time - self.last_ensure_time) < self.recovery_interval:
            return True
        
        with self.bus_lock:
            retries = 3
            for attempt in range(retries):
                try:
                    with smbus2.SMBus(1) as bus:
                        # Select our channel
                        bus.write_byte(self.mux_addr, 1 << self.mux_channel)
                    time.sleep(0.002)  # 2ms for mux to stabilize
                    self.last_ensure_time = current_time
                    return True
                except Exception as e:
                    if attempt == retries - 1:
                        print(f"Resilient OLED: Failed to ensure channel: {e}")
                        return False
                    time.sleep(0.01)
        return False
    
    def _with_channel(self, func, *args, **kwargs):
        """Execute function with channel ensured"""
        # Periodically ensure we're on the right channel
        self.operation_count += 1
        
        # Force channel check every N operations
        force_check = (self.operation_count % 10 == 0)
        
        if not self._ensure_channel(force=force_check):
            print("Warning: Could not ensure OLED channel")
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # On error, try to recover by forcing channel selection
            print(f"OLED operation failed: {e}, attempting recovery...")
            if self._ensure_channel(force=True):
                try:
                    return func(*args, **kwargs)
                except:
                    pass
            raise
    
    def display(self, image):
        """Display image with mux protection"""
        return self._with_channel(self.device.display, image)
    
    def clear(self):
        """Clear display with mux protection"""
        return self._with_channel(self.device.clear)
    
    def show(self):
        """Show display with mux protection"""
        if hasattr(self.device, 'show'):
            return self._with_channel(self.device.show)
    
    def hide(self):
        """Hide display with mux protection"""
        if hasattr(self.device, 'hide'):
            return self._with_channel(self.device.hide)
    
    def contrast(self, value):
        """Set contrast with mux protection"""
        if hasattr(self.device, 'contrast'):
            return self._with_channel(self.device.contrast, value)
    
    def __getattr__(self, name):
        """Pass through other attributes to the device"""
        attr = getattr(self.device, name)
        if callable(attr):
            return lambda *args, **kwargs: self._with_channel(attr, *args, **kwargs)
        return attr