# Cyberdeck Code

Clean, organized repository for Raspberry Pi 5 Cyberdeck custom features including OLED animations and screen tilt servo control.

## Features

### OLED Display System
- **Spectrum Analyzer**: Audio-reactive visualization (default animation)
- **15+ Animations**: Including starfield, matrix, neural network, oscilloscope, and more
- **Hardware Optimized**: For SSD1306 128x64 OLED with I2C multiplexer support
- **No Input Required**: Perfect for autorun on boot

### Screen Tilt Control
- **Rotary Encoder Control**: Smooth adjustment of screen angle
- **Multiple Modes**: Direct, fine, and range-limited control
- **Position Memory**: Saves and restores last position
- **Button Features**:
  - Single click: Return to home position
  - Double click: Switch control modes
  - Long press: Save current position

## Quick Start

### Run Everything
```bash
cd /home/morph/01_Code/Cyberdeck-Code
./startup-scripts/run-all.sh
```

### Run Individual Components

#### OLED Spectrum Analyzer (Default)
```bash
./startup-scripts/oled-spectrum.py
```

#### Screen Tilt Control
```bash
./startup-scripts/screen-tilt.py
```

## Installation

### Prerequisites
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Enable I2C
sudo raspi-config
# Navigate to Interface Options -> I2C -> Enable

# Verify I2C devices
i2cdetect -y 1
```

## Autorun Configuration

### Method 1: Using Desktop Autostart (Recommended)

1. Open the Autostart application on your Pi desktop
2. Add a new entry:
   - Name: `Cyberdeck Systems`
   - Command: `/home/morph/01_Code/Cyberdeck-Code/startup-scripts/run-all.sh`
   - Or for individual components:
     - OLED: `/home/morph/01_Code/Cyberdeck-Code/startup-scripts/oled-spectrum.py`
     - Tilt: `/home/morph/01_Code/Cyberdeck-Code/startup-scripts/screen-tilt.py`

### Method 2: Using rc.local

Add to `/etc/rc.local` before `exit 0`:
```bash
# Start Cyberdeck components
su - morph -c "/home/morph/01_Code/Cyberdeck-Code/startup-scripts/run-all.sh &"
```

### Method 3: Using systemd (Advanced)

Create service files in `/etc/systemd/system/`:

#### oled-spectrum.service
```ini
[Unit]
Description=OLED Spectrum Analyzer
After=multi-user.target

[Service]
Type=simple
User=morph
ExecStart=/home/morph/01_Code/Cyberdeck-Code/startup-scripts/oled-spectrum.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### screen-tilt.service
```ini
[Unit]
Description=Screen Tilt Control
After=multi-user.target

[Service]
Type=simple
User=morph
ExecStart=/home/morph/01_Code/Cyberdeck-Code/startup-scripts/screen-tilt.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable oled-spectrum.service
sudo systemctl enable screen-tilt.service
sudo systemctl start oled-spectrum.service
sudo systemctl start screen-tilt.service
```

## Project Structure

```
Cyberdeck-Code/
├── startup-scripts/          # No-input scripts for autorun
│   ├── oled-spectrum.py     # Default OLED animation
│   ├── screen-tilt.py       # Screen servo control
│   └── run-all.sh           # Master startup script
├── oled_display/            # OLED display system
│   ├── oled_controller.py   # Basic controller
│   ├── oled_controller_pro.py # Enhanced controller
│   └── i2c_helper.py        # I2C/multiplexer support
├── servo_control/           # Servo control systems
│   └── screen_tilt/         # Screen tilt mechanism
│       ├── screen_tilt_control.py
│       ├── config.json      # Servo configuration
│       └── position_state.json # Saved position
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration

### OLED Display

The OLED system auto-detects displays at:
- Direct connection: 0x3C
- Via multiplexer: 0x70 (mux) -> channel 0 -> 0x3C

No configuration needed for standard setup.

### Screen Tilt Servo

Configuration in `servo_control/screen_tilt/config.json`:
```json
{
  "servo_channel": 0,
  "center_angle": 250,
  "min_angle": 0,
  "max_angle": 270,
  "modes": {
    "direct": {"sensitivity": 5.0},
    "fine": {"sensitivity": 1.0},
    "range": {"sensitivity": 5.0, "min_angle": 90, "max_angle": 180}
  }
}
```

## Hardware Requirements

### OLED Display
- SSD1306 128x64 OLED display
- I2C connection (SDA/SCL)
- Optional: TCA9548A I2C multiplexer

### Screen Tilt Control
- MG996R 270-degree servo motor
- PCA9685 16-channel PWM driver
- Rotary encoder with button
- GPIO connections:
  - Encoder CLK: GPIO 17
  - Encoder DT: GPIO 27
  - Encoder SW: GPIO 22

## Troubleshooting

### OLED Not Displaying

Check I2C connection:
```bash
i2cdetect -y 1
# Should show device at 0x3C or 0x70 (multiplexer)
```

Test directly:
```bash
cd /home/morph/01_Code/Cyberdeck-Code
python3 -c "from oled_display.oled_controller import *; print('Import OK')"
```

### Screen Tilt Not Working

Check PCA9685 connection:
```bash
i2cdetect -y 1
# Should show device at 0x40
```

Test encoder:
```bash
gpio readall
# Check GPIO 17, 27, 22
```

### Stop All Components

```bash
pkill -f "python3.*Cyberdeck-Code"
```

## Development

### Adding New OLED Animations

1. Add animation to `oled_display/oled_controller_pro.py`
2. Update AnimationType enum
3. Test: `python3 oled_display/oled_controller_pro.py -a your_animation`

### Adjusting Screen Tilt Settings

Edit `servo_control/screen_tilt/config.json` and restart the service.

## License

This project is for personal cyberdeck use. Feel free to modify for your own setup.

## Credits

Built for Raspberry Pi 5 Cyberdeck project using:
- luma.oled for display control
- gpiozero for GPIO control  
- adafruit-circuitpython-servokit for servo control