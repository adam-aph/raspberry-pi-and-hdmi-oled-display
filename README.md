# Raspberry Pi 5 HDMI OLED Status Panel

## Project Overview

This mini project implements a **self-contained HDMI OLED status panel** powered by a **Raspberry Pi 5 (4 GB)** and fully embedded inside a monitor stand.  
The OLED display operates as a **secondary HDMI output** and continuously presents:

- Current date and time in **Warsaw**
- World clocks for **India, Nevada, and New York**
- Current **weather conditions for Warsaw**
- A **news feed ticker**
- A continuously rendered **animated 4D tesseract projection**

The system is designed to be:
- Headless and auto-starting
- Robust against HDMI hot-plug events
- Fully managed via systemd user services
- Physically compact and self-contained

---

## Hardware Components

- Raspberry Pi 5 (4 GB RAM)
- Ultra-wide HDMI OLED display (1424×280)
- HDMI + USB internal cabling
- Custom internal mounting inside monitor stand
- Passive cooling and concealed power routing

---

## Repository Structure
```
media/
├── oled-1424x280-1.jpg # Retail photo of OLED display
├── oled-1424x280-2.mp4 # Initial functional tests
├── oled-20250929-0001.jpg # Raspberry Pi assembly
├── oled-20250929-0002.jpg # Internal display mounting
├── oled-20250929-0003.jpg # Stand assembly process
├── oled-20250929-0004.jpg # Final internal layout
└── oled-20250929-0005.mp4 # Final working system demo

raspi/
├── oled-screen.py # Main HDMI OLED rendering application
├── rpi5-cmdline.txt # Kernel boot parameters
├── rpi5-config.txt # Raspberry Pi firmware configuration
└── rpi5-os-setup.txt # OS-level and compositor configuration
```
---

## Hardware Assembly (Photos & Video)
### OLED display
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-1424x280-1.jpg" width=100% height=100%>
### Initial tests
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-1424x280-2.jpg" width=50% height=50%>
### Initial tests video
media/oled-1424x280-2.mp4
### Raspberry Pi assembly
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-20250929-0001.jpg" width=50% height=50%>
### Internal mounting
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-20250929-0002.jpg" width=50% height=50%>
### Stand integration
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-20250929-0003.jpg" width=50% height=50%>
### Final internals
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-20250929-0004.jpg" width=50% height=50%>
### Final result
<img src="https://github.com/adam-aph/raspberry-pi-and-hdmi-oled-display/blob/main/media/oled-20250929-0005.jpg" width=50% height=50%>
### Final result video
media/oled-20250929-0005.mp4

---

## Display Application (`oled-screen.py`)

The Python script is a **long-running, frame-based rendering loop** targeting the OLED HDMI output.

### Core Responsibilities

- Initialize a **fullscreen window** on the secondary HDMI output
- Render layered content using GPU-accelerated drawing:
  - Static layout grid
  - Clock widgets (local + world time zones)
  - Weather data for Warsaw
  - Scrolling news feed
  - Animated rotating **tesseract (4D cube projection)**
- Maintain fixed refresh cadence
- Gracefully restart on compositor or HDMI reconfiguration

The application is designed to run **without window manager decorations** and assumes exclusive control of the OLED output.

---

## Raspberry Pi OS & Display Configuration

All non-Python logic is documented in `rpi5-os-setup.txt`.

### Key Concepts

#### 1. Wayland / Wayfire Output Control
- HDMI-A-1: primary display (rotated as needed)
- HDMI-A-2: OLED panel positioned far off-screen to prevent cursor bleed
- Dynamic hot-plug handling via `wlr-randr`

#### 2. Headless Fallback Output
- NOOP virtual output defined to keep compositor stable when OLED is disconnected

#### 3. Panel Isolation
- Desktop panel (`wf-panel-pi`) is forcibly pinned away from the OLED
- Prevents accidental rendering of taskbars or system UI on the OLED

#### 4. Automated HDMI Guard
A custom watchdog script:
- Monitors HDMI-A-2 availability
- Reconfigures outputs on connect/disconnect
- Restarts UI services only when OLED is stable

#### 5. Mouse & Focus Control
- `ydotool` daemon runs as root
- Used to force pointer focus away from OLED after hot-plug events

---

## systemd User Services

The OLED runs fully unattended using systemd user units:

- `ydotool@.service` – virtual input control
- `hdmi-panel-guard.service` – HDMI state watchdog
- `lcd-screen.service` – launches `oled-screen.py`

All services auto-start after login and recover automatically after crashes or HDMI changes.

---

## Result

The final system behaves as a **dedicated embedded information display**, independent of the main desktop, resistant to HDMI state changes, and visually optimized for ultra-wide OLED panels. This approach avoids SPI/I²C OLED limitations while retaining full GPU acceleration and Wayland stability on Raspberry Pi 5.

---

## License

Apache-2.0 license
