# pyDroneWire

A reverse-engineered Python controller for the FLOW-UFO (KY Y-series) drone with real-time video, DJI-style HUD overlay, and vision-based optical flow stabilization.

The entire control protocol was reverse-engineered from pcap captures of the official KY UFO Android app. No SDK, no documentation — just packet analysis.

## What It Does

- **Full flight control** from a keyboard with spring-back sticks, 3-speed modes, takeoff/land, emergency stop, gyro calibration, headless mode, and flips
- **Dual camera streaming** via RTSP with hot-switching between front and bottom cameras
- **DJI-style HUD overlay** — pitch ladder, compass, throttle/yaw scales, stick position indicators, flight timer, signal status
- **Vision-based optical flow stabilization** — uses Lucas-Kanade sparse flow on the downward camera to detect and correct lateral drift, forward/backward drift, and yaw rotation in real-time
- **Recording and screenshots** with the full HUD overlay baked in
- **Auto-reconnect** on signal loss with time-based detection and retry logic

## The Drone

FLOW-UFO (SSID: `FLOW-UFO-XXXXXX`) — a cheap Chinese toy drone using the KY UFO / E58 protocol family. Dual cameras (front 720p, bottom 480p), WiFi control, no GPS, no altitude hold barometer (uses IR sensor). Available for ~$30 on Amazon/AliExpress.

## Protocol Details

| Property | Value |
|---|---|
| Control transport | UDP port 7099 |
| Video transport | RTSP over UDP, `rtsp://DRONE_IP:7070/webcam` |
| Packet format | 21 bytes: `[0x03, 0x66, 0x14, roll, pitch, throttle, yaw, cmd, speed, 0x00*10, xor_checksum, 0x99]` |
| Control rate | 20 Hz (fixed) |
| Heartbeat | 1 Hz (`0x03 0x66 0x10 0x00 0x00 0x00 0x00 0x00 0x99`) |
| Stick center | `0x80` (128) for all axes |
| Camera switch | `0x06 0x01` (front) or `0x06 0x02` (bottom) to port 7099 |

**Commands (cmd byte):**
| Value | Action |
|---|---|
| `0x01` | Takeoff / Land toggle |
| `0x02` | Emergency stop (motors off immediately) |
| `0x03` | Gyro calibration |
| `0x04` | Headless mode toggle |
| `0x05` | Flip |

Speed modes are **client-side only** — the app limits stick deflection (30% / 60% / 100%). No speed command is sent to the drone.

## Optical Flow Stabilization

When the front camera is pointed downward, the stabilizer tracks surface features using Lucas-Kanade sparse optical flow and applies corrections via a PD controller:

- **Translation detection**: Median flow vector across tracked features = lateral/longitudinal drift
- **Rotation detection**: Tangential component of flow relative to frame center = yaw rotation
- **PD controller**: Proportional gain counters current drift, derivative gain damps oscillation (critical with ~200ms WiFi round-trip latency)
- **Manual holdoff**: Stabilization pauses for 0.6s after any pilot input, then resumes from a clean slate (no accumulated drift from fast maneuvers)
- **Safety**: Corrections are zeroed immediately on signal loss; max authority capped at ~20% stick deflection

Tunable parameters are at the top of `drone_controller.py` under `STAB_*` constants.

## Controls

| Key | Action |
|---|---|
| `W` / `S` | Pitch forward / backward |
| `A` / `D` | Roll left / right |
| `Up` / `Down` (`I` / `K`) | Throttle up / down |
| `Left` / `Right` (`J` / `O`) | Yaw left / right |
| `Space` | Hover (center all sticks) |
| `C` | Arm / Disarm |
| `T` | Takeoff (auto-arms) |
| `L` | Land (smooth) |
| `E` | Emergency stop |
| `F` | Flip (while flying) |
| `G` | Calibrate gyro (on ground) |
| `H` | Headless mode toggle |
| `B` | Toggle vision stabilization |
| `1` / `2` / `3` | Speed mode: 30% / 60% / 100% |
| `V` | Switch camera (front/bottom) |
| `R` | Reconnect video stream |
| `X` | Start / Stop recording |
| `P` | Screenshot |
| `Q` / `ESC` | Quit |

## Requirements

- Python 3.8+
- OpenCV (`opencv-python`)
- NumPy

```bash
pip install opencv-python numpy
```

## Usage

1. Power on the drone and connect to its WiFi network (`FLOW-UFO-XXXXXX`)
2. Run the controller:

```bash
python3 drone_controller.py
```

3. Press `C` to arm, then use throttle (`Up` arrow or `I`) to take off
4. Press `B` to enable stabilization (works best with front camera pointed down via `V`)

Debug logs are written to `debug.log` in the project directory. Pass `--debug` for verbose console output.

Recordings and screenshots are saved to `~/DroneCaptures/`.

## Files

| File | Description |
|---|---|
| `drone_controller.py` | Main controller — protocol, control loop, HUD, stabilization, everything |
| `probe_servo.py` | Utility script for brute-force testing unknown protocol bytes (camera servo probing) |

## Disclaimer

This project is for educational and hobbyist purposes. The protocol was reverse-engineered from publicly observable WiFi traffic. Use responsibly and follow local drone regulations.
