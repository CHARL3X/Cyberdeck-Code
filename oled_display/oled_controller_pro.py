#!/usr/bin/env python3
"""
OLED Permanent Animation Controller - Professional Edition
Enhanced with BlackBox-quality waveform animations and visual standards
"""

import time
import math
import random
import argparse
import signal
import sys
import threading
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
from collections import deque

try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw, ImageFont
    try:
        from .i2c_helper import initialize_display_with_fallback
    except ImportError:
        # Fallback for direct execution
        from i2c_helper import initialize_display_with_fallback
except ImportError as e:
    print("Error: Required libraries not installed")
    print("Run: pip install luma.oled pillow smbus2")
    print(f"Details: {e}")
    sys.exit(1)


class AnimationType(Enum):
    """Available animation types"""
    OSCILLOSCOPE = "oscilloscope"
    SIGNAL_WAVE = "signal"
    STARFIELD = "starfield"
    CYLON = "cylon"
    BREATH = "breath"
    GEOMETRIC = "geometric"
    GLITCH = "glitch"
    MATRIX = "matrix"
    PARTICLES = "particles"
    WAVES = "waves"
    SPIRAL = "spiral"
    SPECTRUM = "spectrum"
    NEURAL = "neural"
    HORIZON = "horizon"
    THERMAL = "thermal"
    PLASMAFLOW = "plasmaflow"
    QUANTUMFIELD = "quantumfield"


@dataclass
class AnimationConfig:
    """Configuration for animations"""
    width: int = 128
    height: int = 64
    i2c_address: int = 0x3C
    i2c_port: int = 1
    fps: int = 20
    duration: Optional[float] = None
    rotation: int = 0


class BaseAnimation:
    """Base class for all animations"""
    
    def __init__(self, config: AnimationConfig):
        self.config = config
        self.frame_count = 0
        self.start_time = time.time()
        self.phase = 0.0
        self.last_update = time.time()
        
    def update(self, dt: float) -> bool:
        """Update animation state"""
        self.frame_count += 1
        self.phase += dt
        self.last_update = time.time()
        
        if self.config.duration and (time.time() - self.start_time) >= self.config.duration:
            return False
        return True
        
    def render(self, draw: ImageDraw) -> None:
        """Render animation frame"""
        pass


class OscilloscopeAnimation(BaseAnimation):
    """Professional oscilloscope visualization with persistence"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.wave_type = 'sine'
        self.wave_stack = deque(maxlen=8)  # Persistence stack
        self.grid_enabled = True
        self.trigger_level = config.height // 2
        self.time_scale = 1.0
        self.amplitude = 0.8
        self.glitch_timer = 0
        self.glitch_active = False
        
        # Wave components for complex signals
        self.wave_components = [
            {'type': 'sine', 'freq': 1.0, 'amp': 0.8, 'phase': 0},
            {'type': 'sine', 'freq': 2.3, 'amp': 0.2, 'phase': math.pi/4}
        ]
        
        # Grid buffer for efficiency
        self.grid_buffer = self._create_grid()
        
    def _create_grid(self) -> Image:
        """Create oscilloscope grid pattern"""
        img = Image.new('1', (self.config.width, self.config.height), 0)
        draw = ImageDraw.Draw(img)
        
        # Center lines (dotted)
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        
        for x in range(0, self.config.width, 2):
            draw.point((x, center_y), fill=1)
        for y in range(0, self.config.height, 2):
            draw.point((center_x, y), fill=1)
        
        # Grid divisions
        for x in range(0, self.config.width, 16):
            if x % 32 == 0:  # Major divisions
                for y in range(0, self.config.height, 4):
                    draw.point((x, y), fill=1)
        
        for y in range(0, self.config.height, 16):
            if y % 32 == 0:  # Major divisions
                for x in range(0, self.config.width, 4):
                    draw.point((x, y), fill=1)
        
        # Edge markers
        for i in range(0, self.config.width, 32):
            draw.line([(i, self.config.height-3), (i, self.config.height-1)], fill=1)
        
        return img
    
    def _generate_waveform(self) -> List[int]:
        """Generate complex waveform points"""
        points = []
        
        for x in range(self.config.width):
            y_val = 0
            
            # Handle glitch zones
            if self.glitch_active and random.random() < 0.1:
                y_val = random.uniform(-1, 1)
            else:
                # Sum wave components
                for comp in self.wave_components:
                    t = (x / self.config.width) * 2 * math.pi * comp['freq'] * self.time_scale
                    t += comp['phase']
                    
                    if comp['type'] == 'sine':
                        val = math.sin(t)
                    elif comp['type'] == 'square':
                        val = 1 if math.sin(t) > 0 else -1
                    elif comp['type'] == 'triangle':
                        val = 2 * abs(((t / (2 * math.pi)) % 1) - 0.5) - 1
                    elif comp['type'] == 'sawtooth':
                        val = 2 * ((t / (2 * math.pi)) % 1) - 1
                    else:
                        val = 0
                    
                    y_val += val * comp['amp']
            
            # Convert to screen coordinates
            y = int(self.config.height // 2 - y_val * self.config.height * 0.35 * self.amplitude)
            y = max(0, min(self.config.height - 1, y))
            points.append(y)
        
        return points
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Update wave component phases
        for comp in self.wave_components:
            comp['phase'] += dt * comp['freq'] * 0.5
        
        # Random glitch effects
        if random.random() < 0.01:
            self.glitch_active = True
            self.glitch_timer = random.randint(3, 10)
        
        if self.glitch_timer > 0:
            self.glitch_timer -= 1
        else:
            self.glitch_active = False
        
        # Change wave type occasionally
        if random.random() < 0.005:
            self.wave_components[0]['type'] = random.choice(['sine', 'square', 'triangle', 'sawtooth'])
        
        # Generate and store waveform
        waveform = self._generate_waveform()
        self.wave_stack.append(waveform)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw grid if enabled
        if self.grid_enabled:
            # Paste pre-rendered grid
            for y in range(self.config.height):
                for x in range(self.config.width):
                    if self.grid_buffer.getpixel((x, y)):
                        draw.point((x, y), fill=1)
        
        # Draw waveforms with persistence
        for i, waveform in enumerate(self.wave_stack):
            is_current = (i == len(self.wave_stack) - 1)
            
            if is_current:
                # Draw current waveform as connected line
                for x in range(1, len(waveform)):
                    draw.line([(x-1, waveform[x-1]), (x, waveform[x])], fill=1)
                    
                    # Add vertical lines for square waves
                    if abs(waveform[x] - waveform[x-1]) > 10:
                        draw.line([(x, min(waveform[x], waveform[x-1])),
                                  (x, max(waveform[x], waveform[x-1]))], fill=1)
            else:
                # Draw older waveforms as dots (persistence effect)
                step = len(self.wave_stack) - i
                for x in range(0, len(waveform), step * 2):
                    draw.point((x, waveform[x]), fill=1)
        
        # Draw trigger level indicator
        draw.line([(self.config.width - 5, self.trigger_level),
                  (self.config.width - 1, self.trigger_level)], fill=1)
        
        # Draw time scale indicator
        self._draw_text(draw, f"{self.time_scale:.1f}x", 
                       self.config.width - 20, self.config.height - 8)
        
        # Add glitch artifacts
        if self.glitch_active:
            for _ in range(self.glitch_timer):
                x = random.randint(0, self.config.width - 1)
                y = random.randint(0, self.config.height - 1)
                draw.rectangle([x, y, x+2, y+1], fill=1)
    
    def _draw_text(self, draw, text, x, y):
        """Simple text rendering using points"""
        for i, char in enumerate(text):
            char_x = x + i * 4
            if char == '.':
                draw.point((char_x, y + 3), fill=1)
            elif char == 'x':
                draw.line([(char_x, y), (char_x + 2, y + 4)], fill=1)
                draw.line([(char_x, y + 4), (char_x + 2, y)], fill=1)
            elif char.isdigit():
                # Simple digit representation
                d = int(char)
                if d in [0, 2, 3, 5, 6, 7, 8, 9]:
                    draw.point((char_x, y), fill=1)  # Top
                if d in [0, 4, 5, 6, 8, 9]:
                    draw.point((char_x, y + 2), fill=1)  # Middle
                if d in [0, 2, 3, 5, 6, 8]:
                    draw.point((char_x, y + 4), fill=1)  # Bottom


class SignalWaveAnimation(BaseAnimation):
    """Professional signal visualization with scanning beam"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.scan_position = 0
        self.scan_direction = 1
        self.scan_speed = 20
        self.wave_center = config.height // 2
        self.wave_amplitude = config.height // 4
        self.wave_frequency = 0.05
        
        # Data points for visualization
        self.data_points = []
        self.signal_history = deque(maxlen=config.width)
        
        # Initialize data points
        for _ in range(8):
            self.data_points.append({
                'x': random.randint(10, config.width - 10),
                'y': random.randint(10, config.height - 10),
                'size': random.choice([1, 2]),
                'blink_rate': random.uniform(0.5, 2.0),
                'phase': random.uniform(0, 2 * math.pi)
            })
        
        # Grid state
        self.show_grid = True
        self.grid_spacing = 16
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Update scan position
        self.scan_position += self.scan_speed * dt * self.scan_direction
        if self.scan_position >= self.config.width or self.scan_position <= 0:
            self.scan_direction *= -1
            self.show_grid = random.choice([True, False])
        
        # Update signal history
        wave = math.sin(self.phase * 2)
        y = self.wave_center + int(self.wave_amplitude * wave)
        self.signal_history.append(y)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw minimal grid
        if self.show_grid:
            for y in range(self.grid_spacing, self.config.height, self.grid_spacing):
                for x in range(0, self.config.width, self.grid_spacing):
                    if random.random() < 0.6:
                        draw.point((x, y), fill=1)
        
        # Draw signal wave
        points = []
        for x in range(self.config.width):
            wave = math.sin(x * self.wave_frequency + self.phase)
            y = self.wave_center + int(self.wave_amplitude * wave)
            points.append((x, y))
        
        # Draw wave as dashed line
        for i in range(1, len(points)):
            if i % 3 != 0:  # Skip every 3rd segment for dashed effect
                draw.line([points[i-1], points[i]], fill=1)
        
        # Draw scanning beam
        scan_x = int(self.scan_position)
        if 0 <= scan_x < self.config.width:
            draw.line([(scan_x, 5), (scan_x, self.config.height - 5)], fill=1)
            
            # Draw intensity at scan position
            if scan_x < len(self.signal_history):
                y = self.signal_history[scan_x]
                draw.ellipse([scan_x - 2, y - 2, scan_x + 2, y + 2], outline=1)
        
        # Draw data points
        for point in self.data_points:
            phase = self.phase * point['blink_rate'] + point['phase']
            if math.sin(phase) > 0.3:
                x, y = int(point['x']), int(point['y'])
                if point['size'] == 1:
                    draw.point((x, y), fill=1)
                else:
                    draw.ellipse([x-1, y-1, x+1, y+1], outline=1)
        
        # Draw corner indicators
        for i in range(3):
            draw.point((2 + i * 3, 2), fill=1)
            draw.point((self.config.width - 3 - i * 3, 2), fill=1)


class SpectrumAnalyzerAnimation(BaseAnimation):
    """Audio spectrum analyzer visualization"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.num_bars = 16
        self.bar_width = config.width // self.num_bars - 1
        self.bar_heights = [0] * self.num_bars
        self.target_heights = [0] * self.num_bars
        self.peak_heights = [0] * self.num_bars
        self.peak_decay = [0] * self.num_bars
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Generate new target heights (simulate audio input)
        for i in range(self.num_bars):
            # Simulate frequency response
            freq_factor = 1.0 - (i / self.num_bars) * 0.5
            base = math.sin(self.phase * (i + 1) * 0.3) * 0.5 + 0.5
            self.target_heights[i] = base * freq_factor * (self.config.height - 10)
        
        # Smooth transition to target heights
        for i in range(self.num_bars):
            diff = self.target_heights[i] - self.bar_heights[i]
            self.bar_heights[i] += diff * 0.3
            
            # Update peaks
            if self.bar_heights[i] > self.peak_heights[i]:
                self.peak_heights[i] = self.bar_heights[i]
                self.peak_decay[i] = 0
            else:
                self.peak_decay[i] += dt * 20
                self.peak_heights[i] = max(0, self.peak_heights[i] - self.peak_decay[i])
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw spectrum bars
        for i in range(self.num_bars):
            x = i * (self.bar_width + 1)
            height = int(self.bar_heights[i])
            
            if height > 0:
                # Draw main bar
                draw.rectangle([x, self.config.height - height,
                              x + self.bar_width - 1, self.config.height - 1], fill=1)
                
                # Draw peak indicator
                peak_y = self.config.height - int(self.peak_heights[i])
                if peak_y < self.config.height - 2:
                    draw.line([(x, peak_y), (x + self.bar_width - 1, peak_y)], fill=1)
        
        # Draw frequency labels (simplified)
        draw.line([(0, self.config.height - 1), (self.config.width - 1, self.config.height - 1)], fill=1)


class NeuralNetworkAnimation(BaseAnimation):
    """Enhanced neural network visualization with smooth signal propagation"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Neural network structure
        self.layers = [4, 6, 6, 3]  # Neurons per layer
        self.layer_positions = []
        self.connections = []
        self.connection_states = []  # Visual state of each connection
        self.neuron_states = []
        self.neuron_charge = []  # Build-up before activation
        self.neuron_glow = []  # Glow effect intensity
        
        # Calculate positions
        layer_spacing = config.width // (len(self.layers) + 1)
        for i, num_neurons in enumerate(self.layers):
            layer_x = (i + 1) * layer_spacing
            layer_neurons = []
            neuron_spacing = config.height // (num_neurons + 1)
            
            for j in range(num_neurons):
                neuron_y = (j + 1) * neuron_spacing
                layer_neurons.append((layer_x, neuron_y))
            
            self.layer_positions.append(layer_neurons)
            self.neuron_states.append([0] * num_neurons)
            self.neuron_charge.append([0] * num_neurons)
            self.neuron_glow.append([0] * num_neurons)
        
        # Initialize connections with visual states
        for i in range(len(self.layers) - 1):
            layer_connections = []
            layer_connection_states = []
            for j in range(self.layers[i]):
                neuron_connections = []
                neuron_connection_states = []
                for k in range(self.layers[i + 1]):
                    weight = random.uniform(0.3, 1.0)
                    neuron_connections.append(weight)
                    neuron_connection_states.append({
                        'intensity': 0,
                        'pulse_position': 0,  # 0 to 1 along the connection
                        'is_pulsing': False,
                        'history': deque(maxlen=5)  # Persistence effect
                    })
                layer_connections.append(neuron_connections)
                layer_connection_states.append(neuron_connection_states)
            self.connections.append(layer_connections)
            self.connection_states.append(layer_connection_states)
        
        # Multiple signal tracking
        self.active_signals = []
        
        # Visual effects
        self.burst_mode = False
        self.burst_timer = 0
        self.wave_phase = 0
        self.activity_map = [[0 for _ in range(config.width // 4)] 
                             for _ in range(config.height // 4)]
        
        # Layer activity meters
        self.layer_activity = [0] * len(self.layers)
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Update wave phase for synchronized effects (slower)
        self.wave_phase += dt * 0.5
        
        # Random burst mode activation (much less frequent)
        if not self.burst_mode and random.random() < 0.001:
            self.burst_mode = True
            self.burst_timer = random.uniform(1, 2)
        
        if self.burst_timer > 0:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                self.burst_mode = False
        
        # Generate new signals (much slower rate)
        spawn_rate = 0.1 if self.burst_mode else 0.02
        if random.random() < spawn_rate:
            # Start new signal at input layer
            input_neuron = random.randint(0, self.layers[0] - 1)
            self.neuron_charge[0][input_neuron] = min(1.0, 
                                                      self.neuron_charge[0][input_neuron] + 0.5)
            
            self.active_signals.append({
                'layer': 0,
                'neuron': input_neuron,
                'strength': random.uniform(0.7, 1.0),
                'age': 0
            })
        
        # Update neuron charging and states
        for i in range(len(self.layers)):
            for j in range(self.layers[i]):
                # Charge build-up (slower)
                if self.neuron_charge[i][j] > 0:
                    self.neuron_charge[i][j] += dt * 0.8
                    
                    # Fire when fully charged
                    if self.neuron_charge[i][j] >= 1.0:
                        self.neuron_states[i][j] = 1.0
                        self.neuron_glow[i][j] = 1.0
                        self.neuron_charge[i][j] = 0
                        
                        # Trigger connections to next layer
                        if i < len(self.layers) - 1:
                            for k in range(self.layers[i + 1]):
                                conn_state = self.connection_states[i][j][k]
                                if random.random() < self.connections[i][j][k]:
                                    conn_state['is_pulsing'] = True
                                    conn_state['pulse_position'] = 0
                
                # State decay (much slower for calming effect)
                self.neuron_states[i][j] = max(0, self.neuron_states[i][j] - dt * 0.5)
                self.neuron_glow[i][j] = max(0, self.neuron_glow[i][j] - dt * 0.8)
        
        # Update connection pulses
        for i in range(len(self.connection_states)):
            for j in range(len(self.connection_states[i])):
                for k in range(len(self.connection_states[i][j])):
                    conn_state = self.connection_states[i][j][k]
                    
                    # Update pulse position (slower travel speed)
                    if conn_state['is_pulsing']:
                        conn_state['pulse_position'] += dt * 1.2
                        
                        # Pulse reached target
                        if conn_state['pulse_position'] >= 1.0:
                            conn_state['is_pulsing'] = False
                            conn_state['pulse_position'] = 0
                            # Charge target neuron
                            self.neuron_charge[i + 1][k] = min(1.0,
                                                              self.neuron_charge[i + 1][k] + 0.3)
                    
                    # Update connection intensity (slower transitions)
                    target_intensity = 0.6 if conn_state['is_pulsing'] else 0
                    conn_state['intensity'] += (target_intensity - conn_state['intensity']) * dt * 2
                    
                    # Store in history for persistence effect
                    if conn_state['intensity'] > 0.1:
                        conn_state['history'].append(conn_state['intensity'])
        
        # Calculate layer activity levels (smooth transitions)
        for i in range(len(self.layers)):
            activity = sum(self.neuron_states[i]) / self.layers[i]
            self.layer_activity[i] += (activity - self.layer_activity[i]) * dt * 1
        
        # Update activity heatmap
        for y in range(len(self.activity_map)):
            for x in range(len(self.activity_map[0])):
                self.activity_map[y][x] *= 0.95  # Decay
        
        # Add activity around active neurons
        for i, layer_neurons in enumerate(self.layer_positions):
            for j, (nx, ny) in enumerate(layer_neurons):
                if self.neuron_states[i][j] > 0:
                    map_x = int(nx / 4)
                    map_y = int(ny / 4)
                    if 0 <= map_x < len(self.activity_map[0]) and 0 <= map_y < len(self.activity_map):
                        self.activity_map[map_y][map_x] = min(1.0, 
                                                             self.activity_map[map_y][map_x] + 0.5)
        
        # Clean up old signals
        self.active_signals = [s for s in self.active_signals if s['age'] < 3]
        for signal in self.active_signals:
            signal['age'] += dt
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw activity heatmap (subtle background)
        for y in range(0, self.config.height, 4):
            for x in range(0, self.config.width, 4):
                map_x = x // 4
                map_y = y // 4
                if (map_y < len(self.activity_map) and map_x < len(self.activity_map[0])):
                    if self.activity_map[map_y][map_x] > 0.2:
                        if random.random() < self.activity_map[map_y][map_x] * 0.3:
                            draw.point((x, y), fill=1)
        
        # Draw connections with enhanced effects
        for i in range(len(self.connections)):
            for j, neuron_connections in enumerate(self.connections[i]):
                x1, y1 = self.layer_positions[i][j]
                
                for k, weight in enumerate(neuron_connections):
                    x2, y2 = self.layer_positions[i + 1][k]
                    conn_state = self.connection_states[i][j][k]
                    
                    # Draw connection based on state
                    if conn_state['is_pulsing']:
                        # Draw traveling pulse
                        pulse_x = x1 + (x2 - x1) * conn_state['pulse_position']
                        pulse_y = y1 + (y2 - y1) * conn_state['pulse_position']
                        
                        # Main pulse square
                        draw.rectangle([pulse_x - 2, pulse_y - 2, 
                                      pulse_x + 2, pulse_y + 2], fill=1)
                        
                        # Trail effect
                        for trail_i in range(3):
                            trail_pos = max(0, conn_state['pulse_position'] - trail_i * 0.1)
                            trail_x = x1 + (x2 - x1) * trail_pos
                            trail_y = y1 + (y2 - y1) * trail_pos
                            if trail_i < 2:
                                draw.point((int(trail_x), int(trail_y)), fill=1)
                    
                    # Draw persistent connection based on intensity
                    elif conn_state['intensity'] > 0.1 or len(conn_state['history']) > 0:
                        # Use history for fading effect
                        if len(conn_state['history']) > 0:
                            recent_intensity = conn_state['history'][-1]
                            if random.random() < recent_intensity:
                                draw.line([(x1, y1), (x2, y2)], fill=1)
                    
                    # Subtle flickering for strong connections (much less frequent)
                    elif weight > 0.8 and random.random() < 0.01:
                        # Very occasional flicker on strong but inactive connections
                        draw.line([(x1, y1), (x2, y2)], fill=1)
        
        # Draw neurons with enhanced effects
        for i, layer_neurons in enumerate(self.layer_positions):
            for j, (x, y) in enumerate(layer_neurons):
                activation = self.neuron_states[i][j]
                charge = self.neuron_charge[i][j]
                glow = self.neuron_glow[i][j]
                
                # Draw glow effect for active neurons
                if glow > 0.1:
                    glow_size = int(4 * glow)
                    # Outer glow square
                    draw.rectangle([x - glow_size, y - glow_size,
                                  x + glow_size, y + glow_size], outline=1)
                
                # Draw charging effect (gentler pulsing)
                if charge > 0 and charge < 1:
                    # Pulsing effect while charging
                    pulse = math.sin(self.wave_phase * 2 + j) * 0.5 + 0.5
                    if pulse * charge > 0.4:
                        draw.rectangle([x - 1, y - 1, x + 1, y + 1], outline=1)
                
                # Draw main neuron
                if activation > 0.1:
                    # Active neuron - filled square
                    size = 3 if activation > 0.7 else 2
                    draw.rectangle([x - size, y - size, x + size, y + size], fill=1)
                else:
                    # Inactive neuron - single point
                    draw.point((x, y), fill=1)
        
        # Draw layer activity indicators at bottom
        bar_width = self.config.width // len(self.layers)
        for i, activity in enumerate(self.layer_activity):
            if activity > 0.1:
                x_start = i * bar_width + 5
                x_end = x_start + bar_width - 10
                y = self.config.height - 3
                bar_length = int((x_end - x_start) * activity)
                
                # Activity bar
                draw.line([(x_start, y), (x_start + bar_length, y)], fill=1)
                
                # Tick marks
                draw.point((x_start, y - 1), fill=1)
                draw.point((x_start + bar_length, y - 1), fill=1)
        
        # Draw burst mode indicator
        if self.burst_mode:
            # Flash corners during burst
            if int(self.wave_phase * 10) % 2 == 0:
                for corner_x in [2, self.config.width - 3]:
                    for corner_y in [2, self.config.height - 3]:
                        draw.rectangle([corner_x - 1, corner_y - 1,
                                      corner_x + 1, corner_y + 1], outline=1)


class EnhancedStarfieldAnimation(BaseAnimation):
    """Enhanced starfield with depth and nebula"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.stars = []
        self.nebula_phase = 0
        self.warp_speed = False
        self.warp_timer = 0
        
        # Initialize star field
        for _ in range(40):
            self.stars.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(0, config.height),
                'z': random.uniform(0.1, 1.0),  # Depth
                'speed': random.uniform(0.5, 3),
                'size': random.choice([1, 1, 2]),  # Most are small
                'twinkle': random.random() < 0.3,
                'twinkle_phase': random.uniform(0, 2 * math.pi)
            })
        
        # Nebula clouds
        self.nebula_clouds = []
        for _ in range(3):
            self.nebula_clouds.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(20, config.height - 20),
                'radius': random.uniform(15, 25),
                'density': random.uniform(0.1, 0.3),
                'drift': random.uniform(-0.5, 0.5)
            })
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        self.nebula_phase += dt * 0.3
        
        # Random warp speed events
        if not self.warp_speed and random.random() < 0.002:
            self.warp_speed = True
            self.warp_timer = random.uniform(1, 3)
        
        if self.warp_timer > 0:
            self.warp_timer -= dt
            if self.warp_timer <= 0:
                self.warp_speed = False
        
        # Update stars
        speed_mult = 5 if self.warp_speed else 1
        
        for star in self.stars:
            star['x'] -= star['speed'] * star['z'] * speed_mult
            
            # Add vertical drift for more dynamic movement
            star['y'] += math.sin(self.phase + star['x'] * 0.01) * 0.2
            
            # Update twinkle
            if star['twinkle']:
                star['twinkle_phase'] += dt * 3
            
            # Reset star if it goes off screen
            if star['x'] < 0:
                star['x'] = self.config.width
                star['y'] = random.uniform(0, self.config.height)
                star['z'] = random.uniform(0.1, 1.0)
                star['speed'] = random.uniform(0.5, 3)
            
            # Wrap vertical position
            if star['y'] < 0:
                star['y'] = self.config.height
            elif star['y'] > self.config.height:
                star['y'] = 0
        
        # Update nebula
        for cloud in self.nebula_clouds:
            cloud['x'] += cloud['drift']
            if cloud['x'] < -cloud['radius']:
                cloud['x'] = self.config.width + cloud['radius']
            elif cloud['x'] > self.config.width + cloud['radius']:
                cloud['x'] = -cloud['radius']
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw nebula clouds first (background)
        for cloud in self.nebula_clouds:
            # Create nebula effect with random points
            num_points = int(cloud['radius'] * cloud['radius'] * cloud['density'])
            for _ in range(num_points):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.gauss(0, cloud['radius'] / 2)
                if abs(dist) < cloud['radius']:
                    x = cloud['x'] + dist * math.cos(angle)
                    y = cloud['y'] + dist * math.sin(angle)
                    
                    if 0 <= x < self.config.width and 0 <= y < self.config.height:
                        opacity = 1 - (abs(dist) / cloud['radius'])
                        if random.random() < opacity * 0.3:
                            draw.point((int(x), int(y)), fill=1)
        
        # Draw stars
        for star in self.stars:
            # Calculate brightness based on depth and twinkle
            visible = True
            
            if star['twinkle']:
                twinkle_value = math.sin(star['twinkle_phase'])
                visible = twinkle_value > -0.3
            
            if visible:
                x, y = int(star['x']), int(star['y'])
                
                if self.warp_speed:
                    # Draw motion lines during warp
                    line_length = int(10 * star['z'])
                    draw.line([(x, y), (x + line_length, y)], fill=1)
                else:
                    # Normal star rendering
                    if star['size'] == 1:
                        draw.point((x, y), fill=1)
                    else:
                        # Larger stars for foreground
                        brightness = star['z']
                        if brightness > 0.7:
                            draw.ellipse([x-1, y-1, x+1, y+1], outline=1)
                        else:
                            draw.rectangle([x, y, x+1, y+1], fill=1)


class ThermalColumnsAnimation(BaseAnimation):
    """Thermal Columns - Vertical spectrum analyzer with hot/cold collision dynamics"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Color boundary where hot and cold collide
        self.boundary = 16
        
        # 8 vertical columns across the width
        self.num_columns = 8
        self.column_width = config.width // self.num_columns - 1
        
        # Each column has hot (descending) and cold (ascending) components
        self.columns = []
        for i in range(self.num_columns):
            self.columns.append({
                # Hot component (orange zone, grows downward)
                'hot_height': 0,
                'hot_target': 0,
                'hot_peak': 0,
                'hot_peak_decay': 0,
                
                # Cold component (blue zone, grows upward)
                'cold_height': 0,
                'cold_target': 0,
                'cold_peak': 0,
                'cold_peak_decay': 0,
                
                # Collision energy at boundary
                'collision_energy': 0,
                'collision_particles': [],
                
                # Phase offset for organic movement
                'phase_offset': random.uniform(0, math.pi * 2),
                'frequency': 0.3 + i * 0.1
            })
        
        # Collision splash particles
        self.splash_particles = []
        
        # Global energy wave that influences all columns
        self.global_phase = 0
        
        # Visual effects at boundary
        self.boundary_glow = 0
        self.boundary_pulse = 0
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        self.global_phase += dt * 0.5
        
        # Update each column
        for i, col in enumerate(self.columns):
            # Generate new target heights (like spectrum analyzer)
            phase = self.global_phase + col['phase_offset']
            
            # Hot target (orange zone, 0 to boundary)
            hot_factor = math.sin(phase * col['frequency']) * 0.5 + 0.5
            col['hot_target'] = hot_factor * (self.boundary - 4)
            
            # Cold target (blue zone, boundary to height)
            cold_factor = math.sin(phase * col['frequency'] * 1.3 + math.pi/3) * 0.5 + 0.5
            col['cold_target'] = cold_factor * (self.config.height - self.boundary - 4)
            
            # Smooth transitions (spectrum analyzer physics)
            hot_diff = col['hot_target'] - col['hot_height']
            col['hot_height'] += hot_diff * 0.3
            
            cold_diff = col['cold_target'] - col['cold_height']
            col['cold_height'] += cold_diff * 0.3
            
            # Update hot peaks
            if col['hot_height'] > col['hot_peak']:
                col['hot_peak'] = col['hot_height']
                col['hot_peak_decay'] = 0
            else:
                col['hot_peak_decay'] += dt * 15
                col['hot_peak'] = max(0, col['hot_peak'] - col['hot_peak_decay'])
            
            # Update cold peaks
            if col['cold_height'] > col['cold_peak']:
                col['cold_peak'] = col['cold_height']
                col['cold_peak_decay'] = 0
            else:
                col['cold_peak_decay'] += dt * 15
                col['cold_peak'] = max(0, col['cold_peak'] - col['cold_peak_decay'])
            
            # Calculate collision energy when both components are strong
            hot_proximity = col['hot_height'] / self.boundary if self.boundary > 0 else 0
            cold_proximity = col['cold_height'] / (self.config.height - self.boundary) if (self.config.height - self.boundary) > 0 else 0
            
            new_collision = hot_proximity * cold_proximity
            col['collision_energy'] = col['collision_energy'] * 0.9 + new_collision * 0.1
            
            # Generate collision particles when energy is high
            if col['collision_energy'] > 0.3 and random.random() < col['collision_energy']:
                x_center = i * (self.column_width + 1) + self.column_width // 2
                
                # Create splash particles
                for _ in range(3):
                    self.splash_particles.append({
                        'x': x_center + random.uniform(-self.column_width, self.column_width),
                        'y': self.boundary + random.uniform(-2, 2),
                        'vx': random.uniform(-1, 1),
                        'vy': random.uniform(-0.5, 0.5),
                        'life': 1.0,
                        'size': random.choice([1, 2])
                    })
        
        # Update splash particles
        for particle in self.splash_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= dt * 2
            
            if particle['life'] <= 0 or particle['x'] < 0 or particle['x'] >= self.config.width:
                self.splash_particles.remove(particle)
        
        # Update boundary effects
        total_collision = sum(col['collision_energy'] for col in self.columns)
        self.boundary_glow = min(1.0, total_collision / len(self.columns))
        self.boundary_pulse = math.sin(self.global_phase * 3) * self.boundary_glow
        
        # Limit particles for performance
        if len(self.splash_particles) > 30:
            self.splash_particles = self.splash_particles[-30:]
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw each column
        for i, col in enumerate(self.columns):
            x = i * (self.column_width + 1)
            
            # === HOT COMPONENT (Orange zone, grows downward from top) ===
            hot_height = int(col['hot_height'])
            if hot_height > 0:
                # Main hot bar growing downward
                draw.rectangle([x, 0,
                              x + self.column_width - 1, hot_height], fill=1)
                
                # Hot peak indicator
                peak_y = int(col['hot_peak'])
                if peak_y > 1 and peak_y < self.boundary - 1:
                    draw.line([(x, peak_y), (x + self.column_width - 1, peak_y)], fill=1)
            
            # === COLD COMPONENT (Blue zone, grows upward from bottom) ===
            cold_height = int(col['cold_height'])
            if cold_height > 0:
                # Main cold bar growing upward
                draw.rectangle([x, self.config.height - cold_height,
                              x + self.column_width - 1, self.config.height - 1], fill=1)
                
                # Cold peak indicator
                peak_y = self.config.height - int(col['cold_peak'])
                if peak_y < self.config.height - 1 and peak_y > self.boundary + 1:
                    draw.line([(x, peak_y), (x + self.column_width - 1, peak_y)], fill=1)
            
            # === COLLISION ZONE ===
            if col['collision_energy'] > 0.1:
                # Draw collision effect at boundary
                center_x = x + self.column_width // 2
                intensity = int(col['collision_energy'] * 3)
                
                for offset in range(-intensity, intensity + 1):
                    if 0 <= center_x + offset < self.config.width:
                        draw.point((center_x + offset, self.boundary), fill=1)
                        if col['collision_energy'] > 0.5:
                            draw.point((center_x + offset, self.boundary + 1), fill=1)
                            draw.point((center_x + offset, self.boundary - 1), fill=1)
        
        # Glow effect at boundary (no line)
        if self.boundary_glow > 0.5:
            for x in range(0, self.config.width, 3):
                if random.random() < self.boundary_pulse:
                    draw.point((x, self.boundary), fill=1)
        
        # Draw splash particles
        for particle in self.splash_particles:
            x, y = int(particle['x']), int(particle['y'])
            if 0 <= x < self.config.width and 0 <= y < self.config.height:
                if particle['size'] == 1:
                    draw.point((x, y), fill=1)
                else:
                    if particle['life'] > 0.5:  # Larger when fresh
                        draw.rectangle([x, y, x+1, y+1], fill=1)
                    else:
                        draw.point((x, y), fill=1)
        
        # Draw energy indicators on sides
        if self.boundary_glow > 0.3:
            # Left side - hot energy flowing down
            for y in range(0, self.boundary, 3):
                if random.random() < self.boundary_glow:
                    draw.point((0, y), fill=1)
            
            # Right side - cold energy flowing up
            for y in range(self.boundary, self.config.height, 3):
                if random.random() < self.boundary_glow:
                    draw.point((self.config.width - 1, y), fill=1)


class HorizonAnimation(BaseAnimation):
    """
    Lava Lamp Animation for Portrait OLED with color zones
    
    Hardware: 128x64 OLED in portrait orientation
    - Top ~16 rows: Orange pixels (hot zone - fire/lava)
    - Bottom ~112 rows: Blue pixels (cool zone - water/ice)
    
    Animation uses vertical thermal dynamics where hot bubbles rise
    and cool drops fall, creating a natural lava lamp effect that
    respects the hardware's color zones.
    """
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Color boundary at row 16 (orange above = hot, blue below = cool)
        self.color_boundary = 16
        
        # Lava bubbles (hot, rising)
        self.lava_bubbles = []
        for _ in range(5):
            self.lava_bubbles.append({
                'x': random.uniform(10, config.width - 10),
                'y': random.uniform(config.height - 20, config.height),
                'radius': random.uniform(3, 8),
                'speed': random.uniform(0.3, 0.8),
                'wobble_phase': random.uniform(0, math.pi * 2),
                'wobble_speed': random.uniform(1, 2),
                'temperature': 1.0,  # Hot
                'lifetime': 0
            })
        
        # Water drops (cool, falling)
        self.water_drops = []
        for _ in range(4):
            self.water_drops.append({
                'x': random.uniform(10, config.width - 10),
                'y': random.uniform(-10, 10),
                'radius': random.uniform(2, 5),
                'speed': random.uniform(0.4, 1.0),
                'stretch': 1.0,
                'temperature': 0.0  # Cool
            })
        
        # Thermal particles (small effects)
        self.particles = []
        
        # Fire flickers in orange zone
        self.fire_points = []
        for _ in range(8):
            self.fire_points.append({
                'x': random.uniform(5, config.width - 5),
                'base_y': random.uniform(2, self.color_boundary - 2),
                'flicker_phase': random.uniform(0, math.pi * 2),
                'intensity': random.uniform(0.5, 1.0)
            })
        
        # Ice crystals in blue zone
        self.ice_crystals = []
        for _ in range(6):
            self.ice_crystals.append({
                'x': random.uniform(5, config.width - 5),
                'y': random.uniform(config.height - 30, config.height - 5),
                'size': random.randint(2, 4),
                'rotation': random.uniform(0, math.pi * 2),
                'spin_speed': random.uniform(-0.5, 0.5)
            })
        
        # Thermal gradient waves
        self.thermal_waves = []
        for i in range(3):
            self.thermal_waves.append({
                'phase': random.uniform(0, math.pi * 2),
                'speed': 0.5 + i * 0.2,
                'amplitude': 2 + i
            })
        
        # Steam/mist at boundary
        self.steam_particles = []
        
        # Thermal convection current visualization
        self.convection_phase = 0
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        self.convection_phase += dt * 0.5
        
        # Update lava bubbles (rising)
        for bubble in self.lava_bubbles[:]:
            # Rise with wobble
            bubble['y'] -= bubble['speed']
            bubble['wobble_phase'] += dt * bubble['wobble_speed']
            bubble['x'] += math.sin(bubble['wobble_phase']) * 0.3
            bubble['lifetime'] += dt
            
            # Cool down as it rises
            if bubble['y'] < self.color_boundary + 10:
                bubble['temperature'] = max(0, bubble['temperature'] - dt * 0.5)
            
            # Reset when reaches top or cools completely
            if bubble['y'] < -bubble['radius'] or bubble['temperature'] <= 0:
                bubble['y'] = self.config.height + bubble['radius']
                bubble['x'] = random.uniform(10, self.config.width - 10)
                bubble['radius'] = random.uniform(3, 8)
                bubble['speed'] = random.uniform(0.3, 0.8)
                bubble['temperature'] = 1.0
                bubble['lifetime'] = 0
        
        # Update water drops (falling)
        for drop in self.water_drops[:]:
            # Fall with acceleration
            drop['y'] += drop['speed']
            drop['speed'] = min(drop['speed'] + dt * 0.1, 2.0)
            
            # Stretch as it falls
            drop['stretch'] = 1.0 + drop['speed'] * 0.3
            
            # Reset when reaches bottom
            if drop['y'] > self.config.height + drop['radius']:
                drop['y'] = -drop['radius']
                drop['x'] = random.uniform(10, self.config.width - 10)
                drop['radius'] = random.uniform(2, 5)
                drop['speed'] = random.uniform(0.4, 1.0)
                drop['stretch'] = 1.0
        
        # Update fire flickers
        for fire in self.fire_points:
            fire['flicker_phase'] += dt * 3
            fire['intensity'] = 0.5 + 0.5 * math.sin(fire['flicker_phase'])
        
        # Update ice crystals
        for crystal in self.ice_crystals:
            crystal['rotation'] += crystal['spin_speed'] * dt
            # Slight drift
            crystal['x'] += math.sin(self.convection_phase + crystal['rotation']) * 0.1
        
        # Update thermal waves
        for wave in self.thermal_waves:
            wave['phase'] += dt * wave['speed']
        
        # Generate steam particles at boundary
        self.steam_particles = []
        if random.random() < 0.3:
            for _ in range(3):
                self.steam_particles.append({
                    'x': random.uniform(5, self.config.width - 5),
                    'y': self.color_boundary + random.randint(-2, 2),
                    'life': random.uniform(0.5, 1.0)
                })
        
        # Update existing steam
        for steam in self.steam_particles[:]:
            steam['y'] -= 0.5  # Rise slowly
            steam['life'] -= dt
            if steam['life'] <= 0:
                self.steam_particles.remove(steam)
        
        # Generate thermal particles
        self.particles = []
        for bubble in self.lava_bubbles:
            if bubble['temperature'] > 0.5 and random.random() < 0.1:
                self.particles.append({
                    'x': bubble['x'] + random.uniform(-bubble['radius'], bubble['radius']),
                    'y': bubble['y'],
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(-1, -0.5),
                    'life': 1.0
                })
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # === HOT ZONE (Orange pixels, top 16 rows) ===
        
        # Draw fire/flame effects
        for fire in self.fire_points:
            x = int(fire['x'])
            y = int(fire['base_y'] + math.sin(fire['flicker_phase']) * 2)
            
            if fire['intensity'] > 0.3:
                # Flame shape
                draw.point((x, y), fill=1)
                if fire['intensity'] > 0.6:
                    draw.point((x-1, y+1), fill=1)
                    draw.point((x+1, y+1), fill=1)
                if fire['intensity'] > 0.8:
                    draw.point((x, y-1), fill=1)
        
        # Draw convection currents in hot zone
        for i in range(3):
            x = self.config.width // 4 * (i + 1)
            for y in range(2, self.color_boundary - 2, 3):
                phase = self.convection_phase + i * math.pi / 3
                offset = math.sin(phase + y * 0.2) * 2
                if abs(offset) > 1:
                    draw.point((int(x + offset), y), fill=1)
        
        # === THERMAL BOUNDARY (Row 16) ===
        # Draw dynamic boundary with thermal mixing
        for x in range(self.config.width):
            # Wavy boundary showing thermal interaction
            wave_offset = math.sin(x * 0.1 + self.thermal_waves[0]['phase']) * 1
            boundary_y = self.color_boundary + int(wave_offset)
            if 0 <= boundary_y < self.config.height:
                draw.point((x, boundary_y), fill=1)
        
        # Draw steam particles at boundary
        for steam in self.steam_particles:
            x, y = int(steam['x']), int(steam['y'])
            if steam['life'] > 0.5:
                draw.point((x, y), fill=1)
                draw.point((x+1, y), fill=1)
            else:
                draw.point((x, y), fill=1)
        
        # === COOL ZONE (Blue pixels, below row 16) ===
        
        # Draw thermal gradient waves
        for wave_idx, wave in enumerate(self.thermal_waves):
            y_base = self.color_boundary + 10 + wave_idx * 20
            if y_base < self.config.height:
                for x in range(0, self.config.width, 2):
                    y = y_base + int(math.sin(x * 0.1 + wave['phase']) * wave['amplitude'])
                    if self.color_boundary < y < self.config.height:
                        draw.point((x, y), fill=1)
        
        # Draw lava bubbles (rising)
        for bubble in self.lava_bubbles:
            x, y = int(bubble['x']), int(bubble['y'])
            r = int(bubble['radius'])
            
            if bubble['temperature'] > 0.7:
                # Hot bubble - filled
                draw.ellipse([x-r, y-r, x+r, y+r], fill=1)
                # Add glow effect
                draw.ellipse([x-r-1, y-r-1, x+r+1, y+r+1], outline=1)
            elif bubble['temperature'] > 0.3:
                # Cooling bubble - outlined
                draw.ellipse([x-r, y-r, x+r, y+r], outline=1)
                # Partial fill
                if random.random() < bubble['temperature']:
                    draw.ellipse([x-r+1, y-r+1, x+r-1, y+r-1], fill=1)
            else:
                # Cool bubble - just outline
                draw.ellipse([x-r, y-r, x+r, y+r], outline=1)
        
        # Draw water drops (falling)
        for drop in self.water_drops:
            x, y = int(drop['x']), int(drop['y'])
            r = int(drop['radius'])
            stretch = drop['stretch']
            
            # Stretched ellipse for falling drop
            draw.ellipse([x-r, y-int(r*stretch), x+r, y+int(r*stretch)], outline=1)
            
            # Add trail effect
            if drop['speed'] > 1.0:
                for i in range(1, 3):
                    trail_y = y - i * 2
                    if trail_y > self.color_boundary:
                        draw.point((x, trail_y), fill=1)
        
        # Draw ice crystals at bottom
        for crystal in self.ice_crystals:
            x, y = int(crystal['x']), int(crystal['y'])
            size = crystal['size']
            rot = crystal['rotation']
            
            # Draw crystalline pattern
            for angle in range(0, 360, 60):  # Hexagonal
                rad = math.radians(angle + math.degrees(rot))
                end_x = x + int(math.cos(rad) * size)
                end_y = y + int(math.sin(rad) * size)
                draw.line([(x, y), (end_x, end_y)], fill=1)
        
        # Draw thermal particles
        for particle in self.particles:
            if 0 <= particle['x'] < self.config.width and 0 <= particle['y'] < self.config.height:
                draw.point((int(particle['x']), int(particle['y'])), fill=1)
        
        # Add subtle convection indicators on sides
        # Left side - hot rising
        for y in range(self.config.height - 10, self.color_boundary, -5):
            if random.random() < 0.3:
                draw.point((2, y), fill=1)
                draw.line([(2, y), (2, y-2)], fill=1)
        
        # Right side - cool falling  
        for y in range(self.color_boundary, self.config.height - 10, 5):
            if random.random() < 0.3:
                draw.point((self.config.width - 3, y), fill=1)
                draw.line([(self.config.width - 3, y), (self.config.width - 3, y+2)], fill=1)


class ProfessionalMatrixAnimation(BaseAnimation):
    """Enhanced Matrix rain with better characters"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Column configuration
        self.num_columns = config.width // 6
        self.columns = []
        
        # Character patterns for matrix effect
        self.char_patterns = [
            # Various geometric patterns to simulate characters
            [(0,0), (2,0), (1,1), (0,2), (2,2)],  # H-like
            [(1,0), (0,1), (1,1), (2,1), (1,2)],  # Cross
            [(0,0), (1,0), (2,0), (0,1), (0,2)],  # L
            [(0,0), (1,0), (2,0), (2,1), (2,2)],  # Reverse L
            [(1,0), (1,1), (1,2), (0,1), (2,1)],  # T
            [(0,0), (2,0), (0,2), (2,2)],         # Square corners
            [(1,0), (0,1), (2,1), (1,2)],         # Diamond
            [(0,0), (1,0), (0,1), (1,1)],         # Small square
        ]
        
        # Initialize columns
        for i in range(self.num_columns):
            self.columns.append({
                'x': i * 6 + 1,
                'chars': [],
                'speed': random.uniform(1, 4),
                'spawn_timer': random.uniform(0, 2),
                'intensity_decay': random.uniform(0.7, 0.95)
            })
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        for col in self.columns:
            # Update spawn timer
            col['spawn_timer'] -= dt
            
            # Spawn new character
            if col['spawn_timer'] <= 0:
                col['chars'].append({
                    'y': -3,
                    'pattern': random.choice(self.char_patterns),
                    'intensity': 1.0,
                    'changing': random.random() < 0.3  # Some chars change as they fall
                })
                col['spawn_timer'] = random.uniform(0.1, 0.5)
            
            # Update existing characters
            for char in col['chars'][:]:
                char['y'] += col['speed']
                char['intensity'] *= col['intensity_decay']
                
                # Random character changes
                if char['changing'] and random.random() < 0.1:
                    char['pattern'] = random.choice(self.char_patterns)
                
                # Remove off-screen characters
                if char['y'] > self.config.height or char['intensity'] < 0.1:
                    col['chars'].remove(char)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        for col in self.columns:
            for i, char in enumerate(col['chars']):
                # Head of trail is brightest
                is_head = (i == len(col['chars']) - 1)
                
                # Draw character pattern
                for px, py in char['pattern']:
                    x = col['x'] + px
                    y = int(char['y']) + py
                    
                    if 0 <= x < self.config.width and 0 <= y < self.config.height:
                        if is_head or char['intensity'] > 0.5:
                            draw.point((x, y), fill=1)
                        elif random.random() < char['intensity']:
                            draw.point((x, y), fill=1)


class CylonAnimation(BaseAnimation):
    """Knight Rider / Battlestar Galactica scanner"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.position = 0
        self.direction = 1
        self.trail_length = 5
        self.speed = 3
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        self.position += self.direction * self.speed
        
        if self.position >= self.config.width - 1:
            self.position = self.config.width - 1
            self.direction = -1
        elif self.position <= 0:
            self.position = 0
            self.direction = 1
            
        return True
    
    def render(self, draw: ImageDraw) -> None:
        y_center = self.config.height // 2
        
        # Draw trail
        for i in range(self.trail_length):
            trail_pos = self.position - (i * self.direction * 3)
            if 0 <= trail_pos < self.config.width:
                size = max(1, 3 - i)
                
                if i < 3:  # Only draw first few trail elements
                    draw.rectangle([
                        trail_pos - size, y_center - size,
                        trail_pos + size, y_center + size
                    ], fill=1)
        
        # Draw scanning lines
        for y_offset in [-10, 0, 10]:
            y = y_center + y_offset
            if y_offset == 0:  # Only draw center line
                draw.line([(0, y), (self.config.width, y)], fill=1)


class BreathAnimation(BaseAnimation):
    """Calming breathing animation with particles"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.particles = []
        
        # Initialize particles
        for _ in range(15):
            self.particles.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(0, config.height),
                'speed': random.uniform(0.1, 0.3),
                'size': random.choice([1, 2])
            })
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Update particles
        for particle in self.particles:
            particle['x'] -= particle['speed']
            if particle['x'] < 0:
                particle['x'] = self.config.width
                particle['y'] = random.uniform(0, self.config.height)
                
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Calculate breathing cycle
        breath_cycle = (math.sin(self.phase * 0.5) + 1) / 2
        
        # Draw main breathing rectangle
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        
        width = 20 + breath_cycle * 20
        height = 10 + breath_cycle * 10
        
        draw.rectangle([
            center_x - width, center_y - height,
            center_x + width, center_y + height
        ], outline=1)
        
        # Draw inner rectangle
        inner_width = 20 + (1 - breath_cycle) * 15
        inner_height = 10 + (1 - breath_cycle) * 7
        
        draw.rectangle([
            center_x - inner_width, center_y - inner_height,
            center_x + inner_width, center_y + inner_height
        ], outline=1)
        
        # Draw particles
        for particle in self.particles:
            draw.point((int(particle['x']), int(particle['y'])), fill=1)


class GeometricAnimation(BaseAnimation):
    """Ocean-like waves with thermal-style physics"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Color boundary
        self.boundary = 16
        
        # Orange zone (scrolls right)
        self.orange_scroll = 0
        
        # Global phase (like thermal columns)
        self.global_phase = 0
        
        # Blue zone waves with spectrum analyzer physics
        self.wave_phases = []
        for i in range(8):  # 8 waves
            self.wave_phases.append({
                'offset': 0,
                'frequency': 0.3 + i * 0.1,  # Individual frequencies like thermal columns
                'current_amplitude': 5,  # Current amplitude (smoothly animated)
                'target_amplitude': 5,  # Target amplitude (changes over time)
                'y_base': self.boundary + 5 + i * 5.5,  # Vertical positions
                'phase_offset': random.uniform(0, math.pi * 2),  # Random starting phase like thermal
                'energy': 0  # Wave energy level
            })
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Orange scrolls right
        self.orange_scroll += dt * 1.5
        
        # Update global phase (like thermal columns)
        self.global_phase += dt * 0.5
        
        # Update waves with thermal-style physics
        for i, wave in enumerate(self.wave_phases):
            # Scroll waves right
            wave['offset'] += dt * (1.2 + i * 0.05)
            
            # Generate new target amplitude based on global phase (like thermal columns)
            phase = self.global_phase + wave['phase_offset']
            amplitude_factor = math.sin(phase * wave['frequency']) * 0.5 + 0.5
            wave['target_amplitude'] = 3 + amplitude_factor * 7  # Range from 3 to 10
            
            # Smooth transition to target (spectrum analyzer physics)
            amp_diff = wave['target_amplitude'] - wave['current_amplitude']
            wave['current_amplitude'] += amp_diff * 0.3  # Smooth momentum
            
            # Update wave energy (affects how waves interact)
            wave['energy'] = wave['current_amplitude'] / 10
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # === ORANGE ZONE - Scrolling right pattern ===
        for x in range(0, self.config.width, 3):
            # Create a flowing pattern that scrolls right
            phase = (x * 0.1) - self.orange_scroll
            for y in range(2, self.boundary - 2):
                intensity = math.sin(phase + y * 0.3) * 0.5 + 0.5
                if intensity > 0.4:
                    draw.point((x, y), fill=1)
                    if intensity > 0.7:
                        draw.point((x+1, y), fill=1)
        
        # === BLUE ZONE - Ocean waves with thermal-style smooth amplitude changes ===
        for wave in self.wave_phases:
            points = []
            
            # Use smoothly animated amplitude (like thermal columns)
            amplitude = wave['current_amplitude']
            
            # Simple sine wave with smooth physics
            for x in range(0, self.config.width, 2):
                # Clean sine wave
                phase = x * 0.05 + wave['offset']
                
                # Calculate wave height with smooth amplitude
                y = wave['y_base'] + int(math.sin(phase) * amplitude)
                
                if self.boundary < y < self.config.height:
                    points.append((x, y))
            
            # Draw connected lines for smoother waves
            for i in range(len(points) - 1):
                draw.line([points[i], points[i+1]], fill=1, width=1)


class ParticleAnimation(BaseAnimation):
    """Particle system with physics"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.particles = []
        self.gravity = 0.1
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Spawn new particles
        if random.random() < 0.3:
            self.particles.append({
                'x': self.config.width // 2 + random.gauss(0, 10),
                'y': self.config.height - 10,
                'vx': random.gauss(0, 2),
                'vy': random.uniform(-5, -2),
                'life': 1.0
            })
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += self.gravity
            particle['life'] -= 0.02
            
            if particle['life'] <= 0 or particle['y'] > self.config.height:
                self.particles.remove(particle)
        
        # Limit particle count
        if len(self.particles) > 50:
            self.particles = self.particles[-50:]
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        for particle in self.particles:
            if particle['life'] > 0.3:
                size = 1 if particle['life'] < 0.5 else 2
                
                if size == 1:
                    draw.point((int(particle['x']), int(particle['y'])), fill=1)
                else:
                    draw.rectangle([
                        int(particle['x']), int(particle['y']),
                        int(particle['x']) + 1, int(particle['y']) + 1
                    ], fill=1)


class WaveAnimation(BaseAnimation):
    """Multiple overlapping wave patterns"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.waves = [
            {'freq': 2, 'amp': 10, 'phase': 0, 'speed': 1},
            {'freq': 3, 'amp': 8, 'phase': math.pi/3, 'speed': 1.5},
            {'freq': 1.5, 'amp': 6, 'phase': math.pi/2, 'speed': 0.8}
        ]
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        for wave in self.waves:
            wave['phase'] += dt * wave['speed']
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        center_y = self.config.height // 2
        
        for wave in self.waves:
            points = []
            for x in range(self.config.width):
                t = (x / self.config.width) * 2 * math.pi * wave['freq']
                y = center_y + wave['amp'] * math.sin(t + wave['phase'])
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill=1, width=1)


class SpiralAnimation(BaseAnimation):
    """Simple rotating dots for each color zone"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.boundary = 16
        
        # Simple rotating dots
        self.rotation = 0
        
        # Orange zone - small circle of dots
        self.orange_dots = 5
        self.orange_radius = 6
        
        # Blue zone - larger pattern
        self.blue_dots = 12  
        self.blue_radius = 20
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Simple rotation
        self.rotation += dt * 2
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Orange zone - small rotating circle
        center_x = self.config.width // 2
        center_y = 8
        
        for i in range(self.orange_dots):
            angle = self.rotation + (i * 2 * math.pi / self.orange_dots)
            x = center_x + self.orange_radius * math.cos(angle)
            y = center_y + self.orange_radius * math.sin(angle) * 0.5
            
            if 0 <= x < self.config.width and 0 <= y < self.boundary:
                draw.rectangle([x-1, y-1, x+1, y+1], fill=1)
        
        # Blue zone - larger rotating pattern
        center_y = self.boundary + (self.config.height - self.boundary) // 2
        
        for i in range(self.blue_dots):
            angle = -self.rotation * 0.7 + (i * 2 * math.pi / self.blue_dots)
            x = center_x + self.blue_radius * math.cos(angle)
            y = center_y + self.blue_radius * math.sin(angle)
            
            if 0 <= x < self.config.width and self.boundary < y < self.config.height:
                # Draw trailing dots
                for j in range(3):
                    trail_angle = angle - j * 0.2
                    trail_x = center_x + (self.blue_radius - j * 3) * math.cos(trail_angle)
                    trail_y = center_y + (self.blue_radius - j * 3) * math.sin(trail_angle)
                    
                    if 0 <= trail_x < self.config.width and self.boundary < trail_y < self.config.height:
                        draw.point((int(trail_x), int(trail_y)), fill=1)


class GlitchAnimation(BaseAnimation):
    """Data corruption glitch optimized for color zones"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.boundary = 16
        
        # Orange zone - simple scan lines
        self.orange_scan_line = 0
        self.orange_static_level = 0
        
        # Blue zone - data corruption blocks
        self.blue_blocks = []
        self.blue_data_streams = []
        
        # Initialize data streams
        for x in range(0, config.width, 8):
            self.blue_data_streams.append({
                'x': x,
                'data': [random.randint(0, 1) for _ in range(20)],
                'scroll_speed': random.uniform(0.5, 2),
                'scroll_pos': 0
            })
        
        # Glitch states
        self.glitch_intensity = 0
        self.corruption_spreading = False
        self.recovery_timer = 0
        
        # Cascade effect
        self.cascade_y = 0
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Random glitch events
        if random.random() < 0.05:
            self.glitch_intensity = random.uniform(0.3, 1.0)
            self.corruption_spreading = True
            self.cascade_y = 0
            
        # Decay glitch intensity
        self.glitch_intensity *= 0.97
        
        # Update orange zone
        self.orange_scan_line = (self.orange_scan_line + dt * 30) % self.boundary
        self.orange_static_level = self.glitch_intensity
        
        # Update blue zone data streams
        for stream in self.blue_data_streams:
            stream['scroll_pos'] += stream['scroll_speed'] * dt
            if stream['scroll_pos'] > 1:
                stream['scroll_pos'] = 0
                # Corrupt data occasionally
                if random.random() < self.glitch_intensity:
                    for i in range(len(stream['data'])):
                        if random.random() < 0.3:
                            stream['data'][i] = 1 - stream['data'][i]
        
        # Generate corruption blocks
        if self.corruption_spreading and random.random() < self.glitch_intensity:
            self.blue_blocks.append({
                'x': random.randint(0, self.config.width - 16),
                'y': random.randint(self.boundary, self.config.height - 16),
                'w': random.randint(8, 16),
                'h': random.randint(8, 16),
                'life': 1.0,
                'type': random.choice(['solid', 'lines', 'dots'])
            })
        
        # Update corruption blocks
        for block in self.blue_blocks[:]:
            block['life'] -= dt * 2
            if block['life'] <= 0:
                self.blue_blocks.remove(block)
        
        # Cascade effect
        if self.corruption_spreading:
            self.cascade_y += dt * 60
            if self.cascade_y > self.config.height:
                self.corruption_spreading = False
        
        # System recovery
        if self.glitch_intensity < 0.1 and random.random() < 0.01:
            self.recovery_timer = 0.5
            # Clear corruptions
            self.blue_blocks = []
            for stream in self.blue_data_streams:
                stream['data'] = [random.randint(0, 1) for _ in range(20)]
        
        if self.recovery_timer > 0:
            self.recovery_timer -= dt
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # === ORANGE ZONE - Simple interference ===
        # Horizontal scan line
        scan_y = int(self.orange_scan_line)
        if scan_y < self.boundary:
            draw.line([(0, scan_y), (self.config.width - 1, scan_y)], fill=1)
        
        # Minimal static when glitching
        if self.orange_static_level > 0.2:
            for _ in range(int(self.orange_static_level * 20)):
                x = random.randint(0, self.config.width - 1)
                y = random.randint(0, self.boundary - 1)
                draw.point((x, y), fill=1)
        
        # === Corruption spreading (no boundary line) ===
        if self.corruption_spreading:
            # Show corruption spreading down
            for x in range(0, self.config.width, 4):
                if random.random() < self.glitch_intensity:
                    y = self.boundary + int(self.cascade_y) % (self.config.height - self.boundary)
                    draw.point((x, y), fill=1)
        
        # === BLUE ZONE - Simplified data corruption ===
        # Draw only a few data streams
        for i, stream in enumerate(self.blue_data_streams[::2]):  # Every other stream
            x = stream['x']
            for j, bit in enumerate(stream['data'][::3]):  # Every 3rd bit
                y = self.boundary + 10 + j * 8 + int(stream['scroll_pos'] * 8)
                if y < self.config.height - 5 and bit:
                    draw.line([(x, y), (x + 4, y)], fill=1)
        
        # Draw fewer, simpler corruption blocks
        for block in self.blue_blocks[:3]:  # Max 3 blocks
            if block['type'] == 'lines':
                for y in range(block['y'], min(block['y'] + block['h'], self.config.height), 4):
                    draw.line([(block['x'], y), (block['x'] + block['w'], y)], fill=1)
            else:  # Just dots, no solid blocks
                for x in range(block['x'], min(block['x'] + block['w'], self.config.width), 3):
                    for y in range(block['y'], min(block['y'] + block['h'], self.config.height), 3):
                        if random.random() < 0.5:
                            draw.point((x, y), fill=1)
        
        # Recovery flash
        if self.recovery_timer > 0:
            if int(self.recovery_timer * 10) % 2 == 0:
                # Flash effect
                for y in range(0, self.config.height, 8):
                    draw.line([(0, y), (self.config.width - 1, y)], fill=1)


class PlasmaFlowAnimation(BaseAnimation):
    """Plasma Flow - Spectrum analyzer meets liquid physics with flowing energy"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Spectrum-style bars but with plasma physics
        self.num_bars = 12
        self.bar_width = config.width // self.num_bars - 1
        
        # Each bar has multiple properties for plasma simulation
        self.bars = []
        for i in range(self.num_bars):
            self.bars.append({
                'height': 0,
                'target_height': 0,
                'velocity': 0,
                'energy': 0,
                'plasma_temp': random.uniform(0.3, 1.0),
                'flow_phase': random.uniform(0, math.pi * 2),
                'peak_height': 0,
                'peak_decay': 0,
                # Plasma tendrils connecting bars
                'tendrils': []
            })
        
        # Plasma field grid for background effects
        self.plasma_field = [[0 for _ in range(config.width // 4)] 
                             for _ in range(config.height // 4)]
        
        # Flow particles that move between bars
        self.flow_particles = []
        for _ in range(20):
            self.flow_particles.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(0, config.height),
                'vx': random.uniform(-2, 2),
                'vy': 0,
                'life': 1.0,
                'energy': random.uniform(0.5, 1.0)
            })
        
        # Energy waves that propagate through bars
        self.energy_waves = []
        self.wave_spawn_timer = 0
        
        # Global plasma temperature affects all dynamics
        self.global_temp = 0.5
        self.temp_target = 0.5
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Update global temperature (creates overall mood changes)
        self.temp_target = 0.3 + math.sin(self.phase * 0.2) * 0.3 + random.uniform(-0.1, 0.1)
        self.global_temp += (self.temp_target - self.global_temp) * 0.1
        
        # Generate spectrum-like targets with plasma influence
        for i, bar in enumerate(self.bars):
            # Base frequency response like spectrum
            freq_factor = 1.0 - (i / self.num_bars) * 0.3
            base = math.sin(self.phase * (i + 1) * 0.3) * 0.5 + 0.5
            
            # Add plasma temperature influence
            plasma_boost = bar['plasma_temp'] * self.global_temp * 0.3
            bar['target_height'] = (base * freq_factor + plasma_boost) * (self.config.height - 10)
            
            # Physics-based movement with spring dynamics
            spring_force = (bar['target_height'] - bar['height']) * 0.2
            damping = bar['velocity'] * 0.1
            bar['velocity'] += spring_force - damping
            bar['height'] += bar['velocity'] * dt * 5
            
            # Update plasma temperature (affects color intensity)
            bar['plasma_temp'] += random.uniform(-0.05, 0.05)
            bar['plasma_temp'] = max(0.2, min(1.0, bar['plasma_temp']))
            
            # Flow phase for internal movement
            bar['flow_phase'] += dt * (2 + bar['plasma_temp'])
            
            # Peak tracking like spectrum
            if bar['height'] > bar['peak_height']:
                bar['peak_height'] = bar['height']
                bar['peak_decay'] = 0
            else:
                bar['peak_decay'] += dt * 15
                bar['peak_height'] = max(0, bar['peak_height'] - bar['peak_decay'])
            
            # Update energy level
            bar['energy'] = bar['height'] / self.config.height
        
        # Spawn energy waves periodically
        self.wave_spawn_timer += dt
        if self.wave_spawn_timer > 0.5:
            self.wave_spawn_timer = 0
            if random.random() < 0.7:
                self.energy_waves.append({
                    'position': 0,
                    'speed': random.uniform(30, 60),
                    'amplitude': random.uniform(5, 15),
                    'decay': 0.95
                })
        
        # Update energy waves
        for wave in self.energy_waves[:]:
            wave['position'] += wave['speed'] * dt
            wave['amplitude'] *= wave['decay']
            
            # Apply wave to bars
            bar_index = int(wave['position'] * self.num_bars / self.config.width)
            if 0 <= bar_index < self.num_bars:
                self.bars[bar_index]['velocity'] += wave['amplitude'] * 0.5
            
            # Remove dead waves
            if wave['position'] > self.config.width or wave['amplitude'] < 0.5:
                self.energy_waves.remove(wave)
        
        # Update flow particles
        for particle in self.flow_particles:
            # Attract to nearest high-energy bar
            nearest_bar = min(self.num_bars - 1, max(0, int(particle['x'] * self.num_bars / self.config.width)))
            bar_center_x = nearest_bar * (self.bar_width + 1) + self.bar_width / 2
            
            # Apply attraction force
            dx = bar_center_x - particle['x']
            attraction = dx * 0.02 * self.bars[nearest_bar]['energy']
            particle['vx'] += attraction
            
            # Vertical force based on bar energy
            if particle['y'] > self.config.height - self.bars[nearest_bar]['height']:
                particle['vy'] -= 2  # Push up
            else:
                particle['vy'] += 0.5  # Gravity
            
            # Update position
            particle['x'] += particle['vx'] * dt * 10
            particle['y'] += particle['vy'] * dt * 10
            
            # Apply damping
            particle['vx'] *= 0.95
            particle['vy'] *= 0.9
            
            # Wrap horizontally, reset vertically
            if particle['x'] < 0:
                particle['x'] = self.config.width
            elif particle['x'] > self.config.width:
                particle['x'] = 0
            
            if particle['y'] > self.config.height:
                particle['y'] = 0
                particle['vy'] = random.uniform(1, 3)
            elif particle['y'] < 0:
                particle['y'] = self.config.height
                particle['vy'] = random.uniform(-3, -1)
            
            # Energy decay
            particle['life'] -= dt * 0.1
            if particle['life'] < 0:
                particle['life'] = 1.0
                particle['energy'] = random.uniform(0.5, 1.0)
        
        # Update plasma field (background effect)
        for y in range(len(self.plasma_field)):
            for x in range(len(self.plasma_field[0])):
                # Calculate field value based on nearby bars
                bar_x = x * 4 * self.num_bars / self.config.width
                if bar_x < self.num_bars:
                    bar_index = int(bar_x)
                    influence = self.bars[bar_index]['energy'] * 0.3
                    noise = math.sin(x * 0.5 + self.phase) * math.cos(y * 0.3 + self.phase * 0.7)
                    self.plasma_field[y][x] = influence + noise * 0.2
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw plasma field background (subtle)
        for y in range(0, len(self.plasma_field), 2):
            for x in range(0, len(self.plasma_field[0]), 2):
                if self.plasma_field[y][x] > 0.3:
                    draw.point((x * 4, y * 4), fill=1)
        
        # Draw energy connections between bars
        for i in range(self.num_bars - 1):
            if self.bars[i]['energy'] > 0.5 and self.bars[i + 1]['energy'] > 0.5:
                x1 = i * (self.bar_width + 1) + self.bar_width
                x2 = (i + 1) * (self.bar_width + 1)
                y1 = self.config.height - int(self.bars[i]['height'])
                y2 = self.config.height - int(self.bars[i + 1]['height'])
                
                # Draw plasma tendril with sine wave
                for t in range(0, 10):
                    tx = x1 + (x2 - x1) * t / 10
                    offset = math.sin(self.bars[i]['flow_phase'] + t * 0.5) * 2
                    ty = y1 + (y2 - y1) * t / 10 + offset
                    if 0 <= ty < self.config.height:
                        draw.point((int(tx), int(ty)), fill=1)
        
        # Draw main bars with plasma effects
        for i, bar in enumerate(self.bars):
            x = i * (self.bar_width + 1)
            height = int(bar['height'])
            
            if height > 0:
                # Draw main bar with plasma flow pattern
                for y_offset in range(height):
                    y = self.config.height - 1 - y_offset
                    
                    # Create flowing plasma pattern inside bar
                    flow_pattern = math.sin(y * 0.2 + bar['flow_phase']) * 0.5 + 0.5
                    if flow_pattern > 0.3 or y_offset < 3 or y_offset > height - 3:
                        draw.rectangle([x, y, x + self.bar_width - 1, y], fill=1)
                
                # Draw peak indicator with glow
                peak_y = self.config.height - int(bar['peak_height'])
                if peak_y < self.config.height - 2:
                    # Main peak line
                    draw.line([(x, peak_y), (x + self.bar_width - 1, peak_y)], fill=1)
                    # Glow effect above and below
                    if bar['peak_decay'] < 5:
                        if peak_y > 0:
                            draw.line([(x, peak_y - 1), (x + self.bar_width - 1, peak_y - 1)], fill=1)
        
        # Draw flow particles
        for particle in self.flow_particles:
            if particle['energy'] > 0.3:
                x, y = int(particle['x']), int(particle['y'])
                if 0 <= x < self.config.width and 0 <= y < self.config.height:
                    draw.point((x, y), fill=1)
                    # Add glow for high energy particles
                    if particle['energy'] > 0.7:
                        if x > 0:
                            draw.point((x - 1, y), fill=1)
                        if x < self.config.width - 1:
                            draw.point((x + 1, y), fill=1)
        
        # Draw baseline
        draw.line([(0, self.config.height - 1), (self.config.width - 1, self.config.height - 1)], fill=1)


class QuantumFieldAnimation(BaseAnimation):
    """Quantum Field - Wave interference patterns with particle physics"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        
        # Wave sources that create interference patterns
        self.wave_sources = []
        for _ in range(3):
            self.wave_sources.append({
                'x': random.uniform(20, config.width - 20),
                'y': random.uniform(20, config.height - 20),
                'frequency': random.uniform(0.5, 2.0),
                'amplitude': random.uniform(10, 20),
                'phase': 0,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'color_phase': random.uniform(0, math.pi * 2)
            })
        
        # Quantum particles affected by the field
        self.quantum_particles = []
        for _ in range(30):
            self.quantum_particles.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(0, config.height),
                'vx': 0,
                'vy': 0,
                'phase': random.uniform(0, math.pi * 2),
                'entangled_with': None,
                'probability': 1.0,
                'spin': random.choice([-1, 1])
            })
        
        # Field grid for efficient calculation
        self.field_resolution = 8
        self.field_width = config.width // self.field_resolution
        self.field_height = config.height // self.field_resolution
        self.field = [[0 for _ in range(self.field_width)] 
                      for _ in range(self.field_height)]
        
        # Entanglement pairs
        self.entanglement_lines = []
        
        # Quantum tunneling events
        self.tunnel_events = []
        
        # Wave collapse visualization
        self.collapse_points = []
        
    def calculate_field_at_point(self, x: float, y: float, t: float) -> float:
        """Calculate wave interference at a specific point"""
        total = 0
        for source in self.wave_sources:
            dx = x - source['x']
            dy = y - source['y']
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # Wave equation with decay
                wave_value = source['amplitude'] * math.sin(
                    source['frequency'] * (distance * 0.1 - t) + source['phase']
                ) / (1 + distance * 0.01)
                total += wave_value
        
        return total
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        
        # Update wave sources
        for source in self.wave_sources:
            # Move sources slowly
            source['x'] += source['vx'] * dt
            source['y'] += source['vy'] * dt
            
            # Bounce off walls
            if source['x'] < 10 or source['x'] > self.config.width - 10:
                source['vx'] *= -1
                source['x'] = max(10, min(self.config.width - 10, source['x']))
            if source['y'] < 10 or source['y'] > self.config.height - 10:
                source['vy'] *= -1
                source['y'] = max(10, min(self.config.height - 10, source['y']))
            
            # Update phase
            source['phase'] += dt * 2
            source['color_phase'] += dt * 0.5
        
        # Calculate field grid
        for y in range(self.field_height):
            for x in range(self.field_width):
                px = x * self.field_resolution
                py = y * self.field_resolution
                self.field[y][x] = self.calculate_field_at_point(px, py, self.phase)
        
        # Update quantum particles
        self.entanglement_lines.clear()
        
        for i, particle in enumerate(self.quantum_particles):
            # Get field value at particle position
            grid_x = int(particle['x'] / self.field_resolution)
            grid_y = int(particle['y'] / self.field_resolution)
            
            if 0 <= grid_x < self.field_width and 0 <= grid_y < self.field_height:
                field_value = self.field[grid_y][grid_x]
                
                # Field affects particle velocity
                gradient_x = 0
                gradient_y = 0
                
                if grid_x > 0:
                    gradient_x = self.field[grid_y][grid_x] - self.field[grid_y][grid_x - 1]
                if grid_y > 0:
                    gradient_y = self.field[grid_y][grid_x] - self.field[grid_y - 1][grid_x]
                
                # Apply quantum forces
                particle['vx'] += gradient_x * particle['spin'] * 0.5
                particle['vy'] += gradient_y * particle['spin'] * 0.5
                
                # Damping
                particle['vx'] *= 0.95
                particle['vy'] *= 0.95
            
            # Update position
            particle['x'] += particle['vx'] * dt * 10
            particle['y'] += particle['vy'] * dt * 10
            
            # Quantum tunneling at boundaries
            if particle['x'] < 0 or particle['x'] > self.config.width:
                if random.random() < 0.3:  # Tunnel probability
                    # Quantum tunnel to opposite side
                    self.tunnel_events.append({
                        'start_x': particle['x'],
                        'start_y': particle['y'],
                        'end_x': self.config.width - particle['x'],
                        'end_y': particle['y'],
                        'time': 0
                    })
                    particle['x'] = self.config.width - particle['x']
                else:
                    # Normal bounce
                    particle['vx'] *= -1
                    particle['x'] = max(0, min(self.config.width, particle['x']))
            
            if particle['y'] < 0 or particle['y'] > self.config.height:
                particle['vy'] *= -1
                particle['y'] = max(0, min(self.config.height, particle['y']))
            
            # Update phase
            particle['phase'] += dt * 3
            
            # Probability wave function
            particle['probability'] = abs(math.sin(particle['phase'])) * 0.5 + 0.5
            
            # Create entanglement with nearby particles
            if particle['entangled_with'] is None and random.random() < 0.01:
                for j, other in enumerate(self.quantum_particles):
                    if i != j and other['entangled_with'] is None:
                        dx = particle['x'] - other['x']
                        dy = particle['y'] - other['y']
                        distance = math.sqrt(dx * dx + dy * dy)
                        
                        if distance < 30:
                            particle['entangled_with'] = j
                            other['entangled_with'] = i
                            break
            
            # Draw entanglement lines
            if particle['entangled_with'] is not None:
                if particle['entangled_with'] < len(self.quantum_particles):
                    other = self.quantum_particles[particle['entangled_with']]
                    self.entanglement_lines.append((
                        particle['x'], particle['y'],
                        other['x'], other['y'],
                        particle['probability']
                    ))
                    
                    # Occasionally break entanglement
                    if random.random() < 0.005:
                        other['entangled_with'] = None
                        particle['entangled_with'] = None
                        
                        # Wave function collapse effect
                        self.collapse_points.append({
                            'x': (particle['x'] + other['x']) / 2,
                            'y': (particle['y'] + other['y']) / 2,
                            'radius': 0,
                            'max_radius': 20
                        })
        
        # Update tunnel events
        for event in self.tunnel_events[:]:
            event['time'] += dt * 5
            if event['time'] > 1:
                self.tunnel_events.remove(event)
        
        # Update collapse points
        for point in self.collapse_points[:]:
            point['radius'] += dt * 40
            if point['radius'] > point['max_radius']:
                self.collapse_points.remove(point)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw interference pattern field
        for y in range(0, self.field_height, 2):
            for x in range(0, self.field_width, 2):
                value = self.field[y][x]
                
                # Create interference pattern visualization
                if abs(value) > 5:
                    px = x * self.field_resolution
                    py = y * self.field_resolution
                    
                    # Positive and negative interference
                    if value > 5:
                        draw.rectangle([px, py, px + self.field_resolution - 1, py], fill=1)
                    elif value < -5 and abs(value) > 10:
                        draw.point((px, py), fill=1)
                        draw.point((px + self.field_resolution - 1, py), fill=1)
        
        # Draw entanglement lines
        for x1, y1, x2, y2, probability in self.entanglement_lines:
            if probability > 0.5:
                # Draw dotted line for entanglement
                steps = 10
                for i in range(0, steps, 2):
                    t = i / steps
                    x = x1 + (x2 - x1) * t
                    y = y1 + (y2 - y1) * t
                    draw.point((int(x), int(y)), fill=1)
        
        # Draw quantum tunneling effects
        for event in self.tunnel_events:
            # Draw tunnel path
            t = event['time']
            if t < 1:
                for i in range(5):
                    x = event['start_x'] + (event['end_x'] - event['start_x']) * t
                    y = event['start_y'] + random.uniform(-2, 2)
                    if 0 <= x < self.config.width and 0 <= y < self.config.height:
                        draw.point((int(x), int(y)), fill=1)
        
        # Draw wave collapse effects
        for point in self.collapse_points:
            radius = int(point['radius'])
            if radius > 0:
                # Draw expanding circle
                for angle in range(0, 360, 30):
                    x = point['x'] + radius * math.cos(math.radians(angle))
                    y = point['y'] + radius * math.sin(math.radians(angle))
                    if 0 <= x < self.config.width and 0 <= y < self.config.height:
                        draw.point((int(x), int(y)), fill=1)
        
        # Draw quantum particles
        for particle in self.quantum_particles:
            if particle['probability'] > 0.3:
                x, y = int(particle['x']), int(particle['y'])
                
                if 0 <= x < self.config.width and 0 <= y < self.config.height:
                    # Draw particle with spin indicator
                    draw.point((x, y), fill=1)
                    
                    # Spin visualization
                    if particle['spin'] > 0:
                        # Spin up - draw small vertical line above
                        if y > 1:
                            draw.point((x, y - 1), fill=1)
                    else:
                        # Spin down - draw small vertical line below
                        if y < self.config.height - 2:
                            draw.point((x, y + 1), fill=1)
                    
                    # High probability particles get bigger representation
                    if particle['probability'] > 0.8:
                        if x > 0:
                            draw.point((x - 1, y), fill=1)
                        if x < self.config.width - 1:
                            draw.point((x + 1, y), fill=1)
        
        # Draw wave sources as pulsing circles
        for source in self.wave_sources:
            x, y = int(source['x']), int(source['y'])
            
            # Pulsing radius based on phase
            radius = 3 + int(math.sin(source['color_phase']) * 2)
            
            # Draw circle
            for angle in range(0, 360, 45):
                px = x + radius * math.cos(math.radians(angle))
                py = y + radius * math.sin(math.radians(angle))
                if 0 <= px < self.config.width and 0 <= py < self.config.height:
                    draw.point((int(px), int(py)), fill=1)


class OLEDController:
    """Main controller for OLED animations"""
    
    def __init__(self, config: AnimationConfig):
        self.config = config
        self.device = None
        self.current_animation = None
        self.animations = {
            AnimationType.OSCILLOSCOPE: OscilloscopeAnimation,
            AnimationType.SIGNAL_WAVE: SignalWaveAnimation,
            AnimationType.SPECTRUM: SpectrumAnalyzerAnimation,
            AnimationType.NEURAL: NeuralNetworkAnimation,
            AnimationType.STARFIELD: EnhancedStarfieldAnimation,
            AnimationType.MATRIX: ProfessionalMatrixAnimation,
            AnimationType.CYLON: CylonAnimation,
            AnimationType.BREATH: BreathAnimation,
            AnimationType.GEOMETRIC: GeometricAnimation,
            AnimationType.PARTICLES: ParticleAnimation,
            AnimationType.WAVES: WaveAnimation,
            AnimationType.SPIRAL: SpiralAnimation,
            AnimationType.GLITCH: GlitchAnimation,
            AnimationType.HORIZON: HorizonAnimation,
            AnimationType.THERMAL: ThermalColumnsAnimation,
            AnimationType.PLASMAFLOW: PlasmaFlowAnimation,
            AnimationType.QUANTUMFIELD: QuantumFieldAnimation
        }
        self.running = False
        # Preview-related attributes
        self.preview_thread = None
        self.preview_running = False
        self.preview_lock = threading.Lock()
        
    def initialize(self):
        """Initialize the OLED display with automatic fallback to multiplexer"""
        try:
            # Use the helper function that handles both direct and multiplexed connections
            self.device = initialize_display_with_fallback(self.config)
            
            if self.device:
                return True
            else:
                return False
        except Exception as e:
            print(f"Failed to initialize display: {e}")
            return False
    
    def set_animation(self, animation_type: AnimationType):
        """Set the current animation"""
        if animation_type in self.animations:
            animation_class = self.animations[animation_type]
            self.current_animation = animation_class(self.config)
            print(f"Switched to {animation_type.value} animation")
        else:
            print(f"Warning: {animation_type.value} animation not implemented, skipping...")
            return False
        return True
    
    def run_single(self, animation_type: AnimationType):
        """Run a single animation"""
        if not self.set_animation(animation_type):
            print(f"Cannot run {animation_type.value} - not implemented")
            return
        self.running = True
        
        frame_time = 1.0 / self.config.fps
        last_frame = time.time()
        
        print(f"Running {animation_type.value} animation (Press Ctrl+C to stop)")
        
        while self.running:
            try:
                current_time = time.time()
                dt = current_time - last_frame
                
                if dt >= frame_time:
                    # Update animation
                    if not self.current_animation.update(dt):
                        break
                    
                    # Render frame
                    image = Image.new('1', (self.config.width, self.config.height), 0)
                    draw = ImageDraw.Draw(image)
                    self.current_animation.render(draw)
                    
                    # Display frame
                    self.device.display(image)
                    last_frame = current_time
                else:
                    time.sleep(0.001)
                    
            except KeyboardInterrupt:
                break
    
    def run_cycle(self, animations: List[AnimationType], cycle_time: float = 10):
        """Cycle through multiple animations"""
        # Filter out unimplemented animations
        valid_animations = [a for a in animations if a in self.animations]
        
        if not valid_animations:
            print("No valid animations to cycle through!")
            return
        
        self.running = True
        animation_index = 0
        
        print(f"Cycling through {len(valid_animations)} animations every {cycle_time}s")
        print("Available animations:", [a.value for a in valid_animations])
        print("Press Ctrl+C to stop")
        
        while self.running:
            try:
                # Set current animation
                current_type = valid_animations[animation_index]
                if not self.set_animation(current_type):
                    # Skip to next if this one fails
                    animation_index = (animation_index + 1) % len(valid_animations)
                    continue
                
                # Run animation for cycle_time seconds
                start_time = time.time()
                frame_time = 1.0 / self.config.fps
                last_frame = time.time()
                
                while time.time() - start_time < cycle_time and self.running:
                    current_time = time.time()
                    dt = current_time - last_frame
                    
                    if dt >= frame_time:
                        # Update animation
                        self.current_animation.update(dt)
                        
                        # Render frame
                        image = Image.new('1', (self.config.width, self.config.height), 0)
                        draw = ImageDraw.Draw(image)
                        self.current_animation.render(draw)
                        
                        # Display frame
                        self.device.display(image)
                        last_frame = current_time
                    else:
                        time.sleep(0.001)
                
                # Move to next animation
                animation_index = (animation_index + 1) % len(valid_animations)
                
            except KeyboardInterrupt:
                break
    
    def list_animations(self):
        """List all available animations"""
        print("\nAvailable Animations:")
        print("-" * 30)
        implemented = []
        for anim_type in AnimationType:
            if anim_type in self.animations:
                implemented.append(anim_type)
                print(f"✓ {anim_type.value:<15} - Ready")
            else:
                print(f"  {anim_type.value:<15} - Not implemented")
        print("-" * 30)
        return implemented
    
    def start_preview(self, animation_type: AnimationType):
        """Start previewing an animation in the background"""
        with self.preview_lock:
            # Stop any existing preview
            if self.preview_thread and self.preview_thread.is_alive():
                self.preview_running = False
                self.preview_thread.join(timeout=1.0)
            
            # Start new preview
            self.preview_running = True
            self.preview_thread = threading.Thread(
                target=self.preview_loop,
                args=(animation_type,),
                daemon=True
            )
            self.preview_thread.start()
    
    def stop_preview(self):
        """Stop the current preview"""
        with self.preview_lock:
            if self.preview_running:
                self.preview_running = False
                if self.preview_thread and self.preview_thread.is_alive():
                    self.preview_thread.join(timeout=1.0)
            
            # Clear the display
            if self.device:
                try:
                    self.device.clear()
                except:
                    pass  # Ignore errors during cleanup
    
    def preview_loop(self, animation_type: AnimationType):
        """Run animation preview in background thread"""
        try:
            # Set up animation
            if animation_type not in self.animations:
                return
            
            animation_class = self.animations[animation_type]
            preview_animation = animation_class(self.config)
            
            # Use lower FPS for preview (smoother transitions)
            frame_time = 1.0 / 15  # 15 FPS for preview
            last_frame = time.time()
            
            while self.preview_running:
                current_time = time.time()
                dt = current_time - last_frame
                
                if dt >= frame_time:
                    # Update animation
                    if not preview_animation.update(dt):
                        # Animation finished, restart it
                        preview_animation = animation_class(self.config)
                    
                    # Render frame
                    image = Image.new('1', (self.config.width, self.config.height), 0)
                    draw = ImageDraw.Draw(image)
                    preview_animation.render(draw)
                    
                    # Display frame
                    if self.device and self.preview_running:
                        try:
                            self.device.display(image)
                        except:
                            break  # Exit on display error
                    
                    last_frame = current_time
                else:
                    time.sleep(0.001)
        except:
            pass  # Silently handle any errors in preview thread
    
    def interactive_select(self):
        """Interactive animation selection with arrow key navigation"""
        import termios
        import tty
        
        implemented = self.list_animations()
        
        if not implemented:
            print("No animations available!")
            return None
        
        # Save terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            # Enable raw mode for arrow key detection
            tty.setraw(sys.stdin.fileno())
            
            current_index = 0
            
            # Start preview of first animation
            self.start_preview(implemented[current_index])
            
            # Clear and show menu
            print("\r\033[2J\033[H", end='')  # Clear screen
            print("OLED Animation Selector")
            print("═" * 30)
            print("Use ↑/↓ arrows to navigate, Enter to select, ESC to cancel")
            print("Live preview showing on OLED display\n")
            
            while True:
                # Display menu with current selection highlighted
                for i, anim in enumerate(implemented):
                    if i == current_index:
                        print(f"\r\033[K→ {anim.value:<20} [PREVIEWING]", end='')
                    else:
                        print(f"\r\033[K  {anim.value:<20}", end='')
                    if i < len(implemented) - 1:
                        print()  # New line for all but last item
                
                # Read key press
                key = sys.stdin.read(1)
                
                if key == '\x1b':  # ESC sequence
                    next_key = sys.stdin.read(2)
                    if next_key == '[A':  # Up arrow
                        current_index = (current_index - 1) % len(implemented)
                        # Start preview of newly selected animation
                        self.start_preview(implemented[current_index])
                        # Move cursor up to redraw menu
                        print(f"\r\033[{len(implemented)}A", end='')
                    elif next_key == '[B':  # Down arrow
                        current_index = (current_index + 1) % len(implemented)
                        # Start preview of newly selected animation
                        self.start_preview(implemented[current_index])
                        # Move cursor up to redraw menu
                        print(f"\r\033[{len(implemented)}A", end='')
                    elif next_key == '':  # Just ESC pressed
                        print("\n\nCancelled.")
                        return None
                elif key == '\r' or key == '\n':  # Enter key
                    selected = implemented[current_index]
                    print(f"\n\nSelected: {selected.value}")
                    return selected
                elif key == '\x03':  # Ctrl+C
                    print("\n\nCancelled.")
                    return None
                elif key == 'q' or key == 'Q':  # Q to quit
                    print("\n\nCancelled.")
                    return None
                
        finally:
            # Stop preview before restoring terminal
            self.stop_preview()
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            print()  # Final newline for clean output
    
    def stop(self):
        """Stop animations and clear display"""
        self.running = False
        if self.device:
            self.device.clear()
            print("\nDisplay cleared")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutdown signal received")
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OLED Permanent Pro - BlackBox Quality Animations')
    parser.add_argument('--animation', '-a', type=str,
                       choices=[a.value for a in AnimationType],
                       help='Animation to run')
    parser.add_argument('--cycle', '-c', action='store_true',
                       help='Cycle through all animations')
    parser.add_argument('--cycle-time', '-t', type=float, default=45,
                       help='Time per animation in cycle mode (seconds)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all available animations')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive animation selection')
    parser.add_argument('--loop', action='store_true',
                       help='Loop single animation forever (use with -a)')
    parser.add_argument('--fps', '-f', type=int, default=20,
                       help='Frames per second')
    parser.add_argument('--address', type=lambda x: int(x, 0), default=0x3C,
                       help='I2C address (e.g., 0x3C)')
    parser.add_argument('--port', '-p', type=int, default=1,
                       help='I2C port number')
    parser.add_argument('--rotate', '-r', type=int, choices=[0, 1, 2, 3], default=0,
                       help='Display rotation (0, 1, 2, or 3)')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create configuration
    config = AnimationConfig(
        i2c_address=args.address,
        i2c_port=args.port,
        fps=args.fps,
        rotation=args.rotate * 90
    )
    
    # Create controller
    controller = OLEDController(config)
    
    # Handle list option before initializing display
    if args.list:
        controller.list_animations()
        sys.exit(0)
    
    # Initialize display
    if not controller.initialize():
        sys.exit(1)
    
    try:
        if args.interactive:
            # Interactive selection mode
            selected = controller.interactive_select()
            if selected:
                # Always loop when selected from interactive menu
                print(f"Looping {selected.value} animation (Press Ctrl+C to stop)")
                while True:
                    controller.run_single(selected)
        elif args.cycle:
            # Cycle through all animations
            animations = list(AnimationType)
            controller.run_cycle(animations, args.cycle_time)
        elif args.animation:
            # Run specific animation
            animation_type = AnimationType(args.animation)
            if args.loop:
                # Loop single animation forever
                print(f"Looping {args.animation} forever (Press Ctrl+C to stop)")
                while True:
                    controller.run_single(animation_type)
            else:
                controller.run_single(animation_type)
        else:
            # Default: cycle through professional animations
            pro_animations = [
                AnimationType.OSCILLOSCOPE,
                AnimationType.SIGNAL_WAVE,
                AnimationType.SPECTRUM,
                AnimationType.NEURAL,
                AnimationType.STARFIELD,
                AnimationType.MATRIX,
                AnimationType.PLASMAFLOW,
                AnimationType.QUANTUMFIELD
            ]
            controller.run_cycle(pro_animations, args.cycle_time)  # Now defaults to 45 seconds
    finally:
        controller.stop()


if __name__ == "__main__":
    main()