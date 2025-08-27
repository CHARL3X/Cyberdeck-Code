#!/usr/bin/env python3
"""
OLED Permanent Animation Controller
Standalone script for running animations on permanently mounted SSD1306 OLED display
"""

import time
import math
import random
import argparse
import signal
import sys
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    from PIL import Image, ImageDraw
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
    STARFIELD = "starfield"
    CYLON = "cylon"
    BREATH = "breath"
    GEOMETRIC = "geometric"
    OSCILLOSCOPE = "oscilloscope"
    GLITCH = "glitch"
    MATRIX = "matrix"
    PARTICLES = "particles"
    WAVES = "waves"
    SPIRAL = "spiral"


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
        
    def update(self, dt: float) -> bool:
        """Update animation state"""
        self.frame_count += 1
        self.phase += dt
        
        if self.config.duration and (time.time() - self.start_time) >= self.config.duration:
            return False
        return True
        
    def render(self, draw: ImageDraw) -> None:
        """Render animation frame"""
        pass


class StarfieldAnimation(BaseAnimation):
    """Space travel starfield animation"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.stars = []
        self.nebula_phase = 0
        
        # Initialize stars
        for _ in range(30):
            self.stars.append({
                'x': random.uniform(0, config.width),
                'y': random.uniform(0, config.height),
                'depth': random.uniform(0.2, 1.0),
                'speed': random.uniform(1, 3),
                'size': random.choice([1, 2]),
                'twinkle': random.random() < 0.3
            })
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        self.nebula_phase += dt * 0.5
        
        # Update stars
        for star in self.stars:
            star['x'] -= star['speed'] * star['depth']
            
            # Reset stars that go off screen
            if star['x'] < 0:
                star['x'] = self.config.width
                star['y'] = random.uniform(0, self.config.height)
                star['depth'] = random.uniform(0.2, 1.0)
                star['speed'] = random.uniform(1, 3)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        # Draw nebula clouds
        for i in range(5):
            x = (i * 30 + self.nebula_phase * 10) % self.config.width
            y = self.config.height / 2 + math.sin(self.nebula_phase + i) * 20
            radius = 15 + math.sin(self.nebula_phase * 0.5 + i) * 5
            
            # Draw nebula as subtle dots
            for _ in range(10):
                nx = x + random.gauss(0, radius)
                ny = y + random.gauss(0, radius/2)
                if 0 <= nx < self.config.width and 0 <= ny < self.config.height:
                    if random.random() < 0.3:
                        draw.point((nx, ny), fill=1)
        
        # Draw stars
        for star in self.stars:
            brightness = 1 if star['depth'] > 0.5 else 1
            
            if star['twinkle'] and math.sin(self.phase * 10 + star['x']) < 0:
                continue  # Skip drawing for twinkle effect
            
            if star['size'] == 1:
                draw.point((int(star['x']), int(star['y'])), fill=1)
            else:
                draw.rectangle([
                    (int(star['x']), int(star['y'])),
                    (int(star['x']) + 1, int(star['y']) + 1)
                ], fill=1)


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
                    draw.ellipse([
                        (trail_pos - size, y_center - size),
                        (trail_pos + size, y_center + size)
                    ], fill=1)
        
        # Draw scanning lines
        for y_offset in [-10, 0, 10]:
            y = y_center + y_offset
            brightness = 128 if y_offset != 0 else 255
            draw.line([(0, y), (self.config.width, y)], fill=brightness//4)


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
            (center_x - width, center_y - height),
            (center_x + width, center_y + height)
        ], outline=255)
        
        # Draw inner rectangle
        inner_width = 20 + (1 - breath_cycle) * 15
        inner_height = 10 + (1 - breath_cycle) * 7
        
        draw.rectangle([
            (center_x - inner_width, center_y - inner_height),
            (center_x + inner_width, center_y + inner_height)
        ], outline=128)
        
        # Draw particles
        for particle in self.particles:
            brightness = 255 if particle['size'] > 1 else 128
            draw.point((int(particle['x']), int(particle['y'])), fill=brightness)


class GeometricAnimation(BaseAnimation):
    """Mathematical geometric patterns"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.pattern_type = 0
        self.pattern_phase = 0
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        self.pattern_phase += dt
        
        # Switch patterns every 5 seconds
        if int(self.phase) % 5 == 0 and int(self.phase) != int(self.phase - dt):
            self.pattern_type = (self.pattern_type + 1) % 3
            
        return True
    
    def render(self, draw: ImageDraw) -> None:
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        
        if self.pattern_type == 0:  # Lissajous
            points = []
            for i in range(100):
                t = i * 0.1 + self.pattern_phase
                x = center_x + 30 * math.sin(3 * t)
                y = center_y + 25 * math.sin(2 * t + math.pi/4)
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill=255, width=1)
                
        elif self.pattern_type == 1:  # Spiral
            points = []
            for i in range(50):
                r = i * 0.8
                angle = i * 0.3 + self.pattern_phase
                x = center_x + r * math.cos(angle)
                y = center_y + r * math.sin(angle)
                points.append((x, y))
            
            if len(points) > 1:
                draw.line(points, fill=255, width=1)
                
        else:  # Rotating shapes
            for i in range(3):
                angle = self.pattern_phase + i * 2 * math.pi / 3
                x = center_x + 25 * math.cos(angle)
                y = center_y + 25 * math.sin(angle)
                
                size = 5 + 3 * math.sin(self.pattern_phase * 2 + i)
                draw.ellipse([
                    (x - size, y - size),
                    (x + size, y + size)
                ], outline=255)


class OscilloscopeAnimation(BaseAnimation):
    """Scientific oscilloscope visualization"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.wave_type = 0
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Switch wave types
        if int(self.phase) % 3 == 0 and int(self.phase) != int(self.phase - dt):
            self.wave_type = (self.wave_type + 1) % 3
            
        return True
    
    def render(self, draw: ImageDraw) -> None:
        points = []
        center_y = self.config.height // 2
        
        for x in range(self.config.width):
            t = (x / self.config.width) * 4 * math.pi + self.phase * 2
            
            if self.wave_type == 0:  # Sine wave
                y = center_y + 20 * math.sin(t)
            elif self.wave_type == 1:  # Square wave
                y = center_y + 20 * (1 if math.sin(t) > 0 else -1)
            else:  # Sawtooth
                y = center_y + 20 * (2 * (t / (2 * math.pi) - math.floor(t / (2 * math.pi) + 0.5)))
            
            points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill=255, width=1)
        
        # Draw grid
        for i in range(0, self.config.width, 16):
            draw.line([(i, 0), (i, self.config.height)], fill=64)
        for i in range(0, self.config.height, 16):
            draw.line([(0, i), (self.config.width, i)], fill=64)


class MatrixAnimation(BaseAnimation):
    """Matrix-style falling characters"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.columns = []
        
        # Initialize columns
        num_columns = config.width // 8
        for i in range(num_columns):
            self.columns.append({
                'x': i * 8,
                'y': random.randint(-20, 0),
                'speed': random.uniform(2, 5),
                'length': random.randint(5, 15)
            })
    
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
            
        # Update columns
        for col in self.columns:
            col['y'] += col['speed']
            
            # Reset column when it goes off screen
            if col['y'] > self.config.height + col['length']:
                col['y'] = random.randint(-20, 0)
                col['speed'] = random.uniform(2, 5)
                col['length'] = random.randint(5, 15)
        
        return True
    
    def render(self, draw: ImageDraw) -> None:
        for col in self.columns:
            for i in range(col['length']):
                y = col['y'] - i * 3
                if 0 <= y < self.config.height:
                    brightness = 255 - (i * 20)
                    # Draw random "character"
                    pattern = random.choice([
                        [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],  # Simple pattern
                        [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],  # Cross
                        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]   # L shape
                    ])
                    
                    for px, py in pattern:
                        if col['x'] + px < self.config.width:
                            draw.point((col['x'] + px, y + py), fill=brightness)


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
            brightness = int(255 * particle['life'])
            size = 1 if particle['life'] < 0.5 else 2
            
            if size == 1:
                draw.point((int(particle['x']), int(particle['y'])), fill=brightness)
            else:
                draw.rectangle([
                    (int(particle['x']), int(particle['y'])),
                    (int(particle['x']) + 1, int(particle['y']) + 1)
                ], fill=brightness)


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
                brightness = 255 - self.waves.index(wave) * 50
                draw.line(points, fill=brightness, width=1)


class SpiralAnimation(BaseAnimation):
    """Animated spiral patterns"""
    
    def __init__(self, config: AnimationConfig):
        super().__init__(config)
        self.spiral_count = 3
        
    def update(self, dt: float) -> bool:
        if not super().update(dt):
            return False
        return True
    
    def render(self, draw: ImageDraw) -> None:
        center_x = self.config.width // 2
        center_y = self.config.height // 2
        
        for spiral in range(self.spiral_count):
            points = []
            phase_offset = spiral * 2 * math.pi / self.spiral_count
            
            for i in range(50):
                t = i * 0.15
                r = t * 5
                angle = t + self.phase + phase_offset
                
                x = center_x + r * math.cos(angle)
                y = center_y + r * math.sin(angle)
                
                if 0 <= x < self.config.width and 0 <= y < self.config.height:
                    points.append((x, y))
            
            if len(points) > 1:
                brightness = 255 - spiral * 50
                draw.line(points, fill=brightness, width=1)


class OLEDController:
    """Main controller for OLED animations"""
    
    def __init__(self, config: AnimationConfig):
        self.config = config
        self.device = None
        self.current_animation = None
        self.animations = {
            AnimationType.STARFIELD: StarfieldAnimation,
            AnimationType.CYLON: CylonAnimation,
            AnimationType.BREATH: BreathAnimation,
            AnimationType.GEOMETRIC: GeometricAnimation,
            AnimationType.OSCILLOSCOPE: OscilloscopeAnimation,
            AnimationType.MATRIX: MatrixAnimation,
            AnimationType.PARTICLES: ParticleAnimation,
            AnimationType.WAVES: WaveAnimation,
            AnimationType.SPIRAL: SpiralAnimation
        }
        self.running = False
        
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
    
    def run_single(self, animation_type: AnimationType):
        """Run a single animation"""
        self.set_animation(animation_type)
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
        self.running = True
        animation_index = 0
        
        print(f"Cycling through {len(animations)} animations every {cycle_time}s")
        print("Press Ctrl+C to stop")
        
        while self.running:
            try:
                # Set current animation
                current_type = animations[animation_index]
                self.set_animation(current_type)
                
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
                animation_index = (animation_index + 1) % len(animations)
                
            except KeyboardInterrupt:
                break
    
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
    parser = argparse.ArgumentParser(description='OLED Permanent Animation Controller')
    parser.add_argument('--animation', '-a', type=str, 
                       choices=[a.value for a in AnimationType],
                       help='Animation to run')
    parser.add_argument('--cycle', '-c', action='store_true',
                       help='Cycle through all animations')
    parser.add_argument('--cycle-time', '-t', type=float, default=45,
                       help='Time per animation in cycle mode (seconds)')
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
    
    # Initialize display
    if not controller.initialize():
        sys.exit(1)
    
    try:
        if args.cycle:
            # Cycle through all animations
            animations = list(AnimationType)
            controller.run_cycle(animations, args.cycle_time)
        elif args.animation:
            # Run specific animation
            animation_type = AnimationType(args.animation)
            controller.run_single(animation_type)
        else:
            # Default: cycle through best animations
            best_animations = [
                AnimationType.STARFIELD,
                AnimationType.CYLON,
                AnimationType.BREATH,
                AnimationType.GEOMETRIC,
                AnimationType.OSCILLOSCOPE,
                AnimationType.PARTICLES,
                AnimationType.WAVES
            ]
            controller.run_cycle(best_animations, args.cycle_time)
    finally:
        controller.stop()


if __name__ == "__main__":
    main()