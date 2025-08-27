#!/usr/bin/env python3
"""
Unified Cyberdeck Controller
Single process managing both OLED display and servo control
Eliminates multiplexer conflicts by coordinating all I2C access
"""

import sys
import time
import threading
import signal
import json
import smbus2
from pathlib import Path
from queue import Queue, Empty
from dataclasses import dataclass
from typing import Optional, Any

# Hardware imports
from gpiozero import Button
from adafruit_servokit import ServoKit
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw

# Animation imports
from oled_display.oled_controller_pro import (
    AnimationType,
    AnimationConfig,
    SpectrumAnalyzerAnimation,
    OscilloscopeAnimation,
    SignalWaveAnimation,
    NeuralNetworkAnimation
)

# GPIO Pin Configuration
ENCODER_CLK = 17
ENCODER_DT = 27
ENCODER_SW = 22

# I2C Configuration
MUX_ADDRESS = 0x70
OLED_CHANNEL = 0
SERVO_CHANNEL = 1
OLED_ADDRESS = 0x3C
PCA9685_ADDRESS = 0x40


@dataclass
class EncoderEvent:
    """Event from encoder thread"""
    type: str  # 'rotation', 'click', 'double_click', 'long_press'
    value: int = 0  # For rotation: delta position


class UnifiedCyberdeckController:
    """Main controller managing both OLED and servo through single mux"""
    
    def __init__(self):
        """Initialize all hardware components"""
        print("Initializing Unified Cyberdeck Controller...")
        
        # Threading and control
        self.running = False
        self.mux_lock = threading.Lock()
        self.servo_lock = threading.Lock()
        self.encoder_queue = Queue()
        
        # Load configuration
        self.config = self.load_config()
        self.state = self.load_state()
        
        # Multiplexer management
        self.mux_bus = None
        self.current_mux_channel = None
        self.init_multiplexer()
        
        # Initialize OLED
        self.oled_device = None
        self.animation = None
        self.animation_config = None
        self.init_oled()
        
        # Initialize Servo
        self.servo_kit = None
        self.servo_channel = 0
        self.current_angle = self.state.get('last_position', 145.0)
        self.encoder_pos = 0
        self.mode = self.state.get('mode', 'direct')
        self.init_servo()
        
        # Initialize Encoder
        self.encoder_thread = None
        self.encoder_running = False
        self.init_encoder()
        
        # Signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("✓ Unified controller ready")
    
    def init_multiplexer(self):
        """Initialize I2C multiplexer"""
        try:
            self.mux_bus = smbus2.SMBus(1)
            # Test multiplexer availability
            self.mux_bus.read_byte(MUX_ADDRESS)
            print(f"✓ Multiplexer found at 0x{MUX_ADDRESS:02X}")
        except Exception as e:
            print(f"✗ No multiplexer found: {e}")
            print("  Attempting direct I2C connections...")
            self.mux_bus = None
    
    def switch_mux_channel(self, channel: int) -> bool:
        """
        Switch multiplexer to specified channel
        Thread-safe with lock protection
        """
        if not self.mux_bus:
            return True  # No mux, assume direct connection
        
        with self.mux_lock:
            if self.current_mux_channel == channel:
                return True  # Already on correct channel
            
            try:
                # Switch channel
                self.mux_bus.write_byte(MUX_ADDRESS, 1 << channel)
                self.current_mux_channel = channel
                time.sleep(0.002)  # 2ms stabilization
                return True
            except Exception as e:
                print(f"Failed to switch mux to channel {channel}: {e}")
                return False
    
    def init_oled(self):
        """Initialize OLED display on channel 0"""
        print("Initializing OLED display...")
        
        # Switch to OLED channel
        if not self.switch_mux_channel(OLED_CHANNEL):
            print("✗ Failed to switch to OLED channel")
            return
        
        try:
            # Initialize OLED
            serial = i2c(port=1, address=OLED_ADDRESS)
            self.oled_device = ssd1306(serial, width=128, height=64)
            
            # Setup animation
            self.animation_config = AnimationConfig(
                width=128,
                height=64,
                i2c_address=OLED_ADDRESS,
                i2c_port=1,
                fps=20
            )
            
            # Default to spectrum analyzer
            self.animation = SpectrumAnalyzerAnimation(self.animation_config)
            
            print(f"✓ OLED initialized at 0x{OLED_ADDRESS:02X}")
            
        except Exception as e:
            print(f"✗ Failed to initialize OLED: {e}")
            self.oled_device = None
    
    def init_servo(self):
        """Initialize servo controller on channel 1"""
        print("Initializing servo controller...")
        
        # Switch to servo channel
        if not self.switch_mux_channel(SERVO_CHANNEL):
            print("✗ Failed to switch to servo channel")
            return
        
        try:
            # Initialize ServoKit
            self.servo_kit = ServoKit(channels=16, address=PCA9685_ADDRESS)
            self.servo_channel = self.config.get('servo_channel', 0)
            
            # Configure servo
            self.servo_kit.servo[self.servo_channel].actuation_range = 270
            self.servo_kit.servo[self.servo_channel].set_pulse_width_range(500, 2500)
            
            # Set initial position
            self.servo_kit.servo[self.servo_channel].angle = self.current_angle
            
            print(f"✓ Servo initialized at 0x{PCA9685_ADDRESS:02X}")
            print(f"  Initial position: {self.current_angle}°")
            
        except Exception as e:
            print(f"✗ Failed to initialize servo: {e}")
            print("  Servo control disabled")
            self.servo_kit = None
        
        # Return to OLED channel
        self.switch_mux_channel(OLED_CHANNEL)
    
    def init_encoder(self):
        """Initialize rotary encoder GPIO"""
        try:
            self.clk_pin = Button(ENCODER_CLK, pull_up=True, bounce_time=0.01)
            self.dt_pin = Button(ENCODER_DT, pull_up=True, bounce_time=0.01)
            self.sw_pin = Button(ENCODER_SW, pull_up=True, bounce_time=0.1)
            
            print(f"✓ Encoder initialized on GPIO {ENCODER_CLK}/{ENCODER_DT}/{ENCODER_SW}")
        except Exception as e:
            print(f"✗ Failed to initialize encoder: {e}")
            print("  Encoder control disabled")
    
    def encoder_polling_thread(self):
        """Background thread polling encoder state"""
        last_clk_state = self.clk_pin.is_pressed
        button_press_time = 0
        click_count = 0
        click_timer = None
        
        while self.encoder_running:
            try:
                # Check rotation
                clk_state = self.clk_pin.is_pressed
                
                if clk_state != last_clk_state and clk_state == False:
                    # CLK went from high to low
                    if self.dt_pin.is_pressed != clk_state:
                        self.encoder_queue.put(EncoderEvent('rotation', 1))
                    else:
                        self.encoder_queue.put(EncoderEvent('rotation', -1))
                
                last_clk_state = clk_state
                
                # Check button (simplified for now)
                if self.sw_pin.is_pressed:
                    if button_press_time == 0:
                        button_press_time = time.time()
                else:
                    if button_press_time > 0:
                        duration = time.time() - button_press_time
                        if duration > 1.0:
                            self.encoder_queue.put(EncoderEvent('long_press'))
                        else:
                            self.encoder_queue.put(EncoderEvent('click'))
                        button_press_time = 0
                
                time.sleep(0.001)  # 1ms polling rate
                
            except Exception as e:
                print(f"Encoder thread error: {e}")
                time.sleep(0.1)
    
    def update_servo_angle(self, delta: int):
        """Update servo angle from encoder rotation"""
        if not self.servo_kit:
            return
        
        with self.servo_lock:
            # Update position based on mode
            sensitivity = self.config['modes'][self.mode]['sensitivity']
            self.encoder_pos += delta
            
            # Calculate new angle
            new_angle = self.config['center_angle'] + (self.encoder_pos * sensitivity)
            
            # Apply limits
            if self.mode == 'range':
                range_config = self.config['modes']['range']
                new_angle = max(range_config['min_angle'], 
                              min(range_config['max_angle'], new_angle))
            else:
                new_angle = max(self.config['min_angle'], 
                              min(self.config['max_angle'], new_angle))
            
            # Only update if changed
            if new_angle != self.current_angle:
                self.current_angle = new_angle
                
                # Switch to servo channel, update, switch back
                if self.switch_mux_channel(SERVO_CHANNEL):
                    try:
                        self.servo_kit.servo[self.servo_channel].angle = self.current_angle
                        print(f"Servo: {self.encoder_pos} → {self.current_angle}°")
                    except Exception as e:
                        print(f"Servo update failed: {e}")
                    finally:
                        # Always return to OLED channel
                        self.switch_mux_channel(OLED_CHANNEL)
    
    def process_encoder_events(self):
        """Process queued encoder events"""
        try:
            while True:
                event = self.encoder_queue.get_nowait()
                
                if event.type == 'rotation':
                    self.update_servo_angle(event.value)
                elif event.type == 'click':
                    # Go to home position
                    print("Encoder: Home position")
                    self.encoder_pos = 0
                    self.update_servo_angle(0)
                elif event.type == 'long_press':
                    # Save state
                    print("Encoder: Saving state")
                    self.save_state()
                    
        except Empty:
            pass  # No more events
    
    def update_oled_frame(self):
        """Update OLED animation frame"""
        if not self.oled_device or not self.animation:
            return
        
        # Ensure we're on OLED channel
        if not self.switch_mux_channel(OLED_CHANNEL):
            return
        
        try:
            # Update animation
            self.animation.update(1.0 / self.animation_config.fps)
            
            # Create frame
            image = Image.new('1', (128, 64))
            draw = ImageDraw.Draw(image)
            
            # Render animation
            self.animation.render(draw)
            
            # Display frame
            self.oled_device.display(image)
            
        except Exception as e:
            print(f"OLED update error: {e}")
    
    def run(self):
        """Main loop - handles OLED animation and encoder events"""
        self.running = True
        self.encoder_running = True
        
        # Start encoder thread
        self.encoder_thread = threading.Thread(target=self.encoder_polling_thread)
        self.encoder_thread.daemon = True
        self.encoder_thread.start()
        
        print("\nCyberdeck running - Press Ctrl+C to stop")
        print(f"Mode: {self.mode}, Position: {self.current_angle}°")
        
        # Main animation loop
        frame_time = 1.0 / self.animation_config.fps
        
        while self.running:
            try:
                loop_start = time.time()
                
                # Process encoder events
                self.process_encoder_events()
                
                # Update OLED frame
                self.update_oled_frame()
                
                # Maintain frame rate
                elapsed = time.time() - loop_start
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(0.1)
        
        self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        print("\nShutting down...")
        
        # Stop threads
        self.running = False
        self.encoder_running = False
        
        if self.encoder_thread:
            self.encoder_thread.join(timeout=1)
        
        # Save state
        self.save_state()
        
        # Clear OLED
        if self.oled_device:
            try:
                self.switch_mux_channel(OLED_CHANNEL)
                self.oled_device.clear()
            except:
                pass
        
        # Close I2C
        if self.mux_bus:
            try:
                self.mux_bus.close()
            except:
                pass
        
        print("✓ Shutdown complete")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.running = False
    
    def load_config(self) -> dict:
        """Load servo configuration"""
        config_file = Path(__file__).parent / "servo_control" / "screen_tilt" / "config.json"
        
        default_config = {
            "servo_channel": 0,
            "default_mode": "direct",
            "modes": {
                "direct": {"sensitivity": 10.0},  # Increased from 5.0 to 10.0
                "fine": {"sensitivity": 2.0},     # Increased from 1.0 to 2.0
                "range": {"sensitivity": 10.0, "min_angle": 90, "max_angle": 180}  # Increased
            },
            "min_angle": 0,
            "max_angle": 270,
            "center_angle": 145
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return default_config
    
    def load_state(self) -> dict:
        """Load saved state"""
        state_file = Path(__file__).parent / "servo_control" / "screen_tilt" / "position_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {}
    
    def save_state(self):
        """Save current state"""
        state_file = Path(__file__).parent / "servo_control" / "screen_tilt" / "position_state.json"
        
        state = {
            "last_position": self.current_angle,
            "mode": self.mode,
            "timestamp": time.time()
        }
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"State saved: {self.current_angle}° in {self.mode} mode")
        except Exception as e:
            print(f"Failed to save state: {e}")


def main():
    """Main entry point"""
    controller = UnifiedCyberdeckController()
    controller.run()


if __name__ == "__main__":
    main()