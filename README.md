# Conway's Game of Life on a 64x64 RGB LED Matrix

A complete guide to building and programming Conway's Game of Life on a 64x64 HUB75 RGB LED panel using a Raspberry Pi and the `hzeller/rpi-rgb-led-matrix` library.

## Table of Contents

- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [Hardware Assembly](#hardware-assembly)
- [Software Setup](#software-setup)
- [Running the Built-in Demo](#running-the-built-in-demo)
- [Custom Game of Life Implementation](#custom-game-of-life-implementation)
- [Configuration and Tuning](#configuration-and-tuning)
- [Alternative Approaches](#alternative-approaches)
- [Troubleshooting](#troubleshooting)

---

## Overview

Conway's Game of Life is a cellular automaton where cells on a grid live, die, or are born based on simple rules:

1. **Underpopulation** — A live cell with fewer than 2 neighbors dies
2. **Survival** — A live cell with 2 or 3 neighbors lives on
3. **Overpopulation** — A live cell with more than 3 neighbors dies
4. **Reproduction** — A dead cell with exactly 3 neighbors becomes alive

A 64x64 LED panel gives us 4,096 cells — enough to produce complex, mesmerizing patterns.

---

## Hardware Requirements

### Essential Components

| Component | Description | Approx. Cost |
|-----------|-------------|--------------|
| **Raspberry Pi 4 Model B** (2GB+ RAM) | Main controller. Pi 3B+ also works. | $35-55 |
| **64x64 HUB75 RGB LED Matrix Panel** | P3 or P4 pitch recommended for indoor use | $25-50 |
| **Adafruit RGB Matrix HAT or Bonnet** | Interfaces Pi GPIO to HUB75 connector | $25 |
| **5V Power Supply** (4A minimum, 8A recommended) | Powers the LED panel directly | $10-15 |
| **16GB+ microSD Card** | For Raspberry Pi OS | $8-12 |
| **HUB75 ribbon cable** | Usually included with panel | — |
| **Jumper wires / standoffs** | For mounting and connections | $5 |

### Optional but Recommended

- **5V 10A power supply** — headroom for full-white brightness
- **Heat sinks / fan** for the Raspberry Pi
- **3D-printed or laser-cut enclosure/frame**
- **USB keyboard + HDMI monitor** — for initial Pi setup (or use SSH)

### Panel Specifications to Verify Before Purchasing

- **Resolution**: 64x64 pixels
- **Interface**: HUB75E (the "E" means it has an address line for 1/32 scan)
- **Scan rate**: 1/32 scan (standard for 64x64)
- **Pitch**: P2, P2.5, P3, or P4 (distance between LEDs in mm)

---

## Hardware Assembly

### Step 1 — Prepare the Raspberry Pi

1. Download **Raspberry Pi OS Lite (64-bit)** from https://www.raspberrypi.com/software/
2. Flash it to your microSD card using **Raspberry Pi Imager**
3. Before first boot, enable SSH:
   - Mount the boot partition
   - Create an empty file named `ssh` in the boot directory
4. Optionally configure WiFi by creating `wpa_supplicant.conf` in the boot partition:
   ```
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1

   network={
       ssid="YOUR_WIFI_SSID"
       psk="YOUR_WIFI_PASSWORD"
   }
   ```
5. Insert the microSD card and boot the Pi

### Step 2 — Attach the RGB Matrix HAT/Bonnet

1. **Power off the Pi** before connecting anything
2. Align the HAT/Bonnet with the Pi's 40-pin GPIO header
3. Press it firmly and evenly onto the pins — all 40 pins must seat fully
4. If using the Adafruit RGB Matrix Bonnet:
   - Solder the included 2x8 header if not pre-soldered
   - The bonnet sits directly on the GPIO header

### Step 3 — Connect the LED Panel

1. Connect the **HUB75 ribbon cable** from the HAT/Bonnet's output to the panel's **input** connector
   - The panel has two HUB75 connectors: **INPUT** and **OUTPUT**
   - Connect to **INPUT** (usually marked with an arrow or label)
   - The ribbon cable has a keyed connector — it only fits one way
2. If your panel doesn't have labeled connectors, the input is typically the one on the **left** when the panel text/arrows face you

### Step 4 — Wire the Power Supply

1. Connect the 5V power supply to the LED panel's power connector
   - Most panels have a 2-pin or 4-pin power connector
   - **Red = +5V**, **Black = GND**
2. **Also connect 5V power to the HAT/Bonnet's power terminal**
   - The Adafruit HAT has screw terminals for external 5V power
   - This powers both the Pi and the panel through the HAT
3. **Do NOT try to power the panel from the Pi's USB alone** — it cannot supply enough current

### Step 5 — Verify Connections Before Powering On

```
Checklist:
[ ] HAT/Bonnet seated on all 40 GPIO pins
[ ] HUB75 ribbon cable: HAT output → Panel INPUT
[ ] 5V power supply → Panel power connector
[ ] 5V power supply → HAT/Bonnet power terminal
[ ] microSD card inserted in Pi
```

---

## Software Setup

### Step 1 — Update the System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2 — Install Build Dependencies

```bash
sudo apt-get install -y git build-essential python3-dev python3-pip
```

### Step 3 — Clone the rpi-rgb-led-matrix Library

```bash
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
```

### Step 4 — Build the Core Library

```bash
make
```

This compiles the C++ library. It should complete in under a minute on a Pi 4.

### Step 5 — Build the Demo Programs

```bash
cd examples-api-use
make
cd ..
```

### Step 6 — (Optional) Build the Python Bindings

If you want to write custom Game of Life code in Python:

```bash
cd bindings/python
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
cd ../..
```

### Step 7 — Disable On-Board Audio (Recommended)

The Pi's onboard audio uses a GPIO pin that conflicts with the LED matrix. Disable it:

```bash
sudo nano /boot/config.txt
```

Find the line:
```
dtparam=audio=on
```

Change it to:
```
dtparam=audio=off
```

Save and reboot:
```bash
sudo reboot
```

### Step 8 — (Optional) Isolate a CPU Core for Real-Time Performance

For flicker-free output, isolate CPU core 3 from the Linux scheduler:

```bash
sudo nano /boot/cmdline.txt
```

Add to the end of the existing line (same line, not a new line):
```
isolcpus=3
```

Reboot for this to take effect.

---

## Running the Built-in Demo

The library includes Game of Life as **Demo #7**. Run it with:

```bash
cd ~/rpi-rgb-led-matrix/examples-api-use
sudo ./demo -D 7 --led-rows=64 --led-cols=64
```

### Common Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--led-rows` | Number of rows on your panel | `--led-rows=64` |
| `--led-cols` | Number of columns on your panel | `--led-cols=64` |
| `--led-gpio-mapping` | GPIO wiring type | `--led-gpio-mapping=adafruit-hat` |
| `--led-slowdown-gpio` | Slow down GPIO for stability (0-4) | `--led-slowdown-gpio=2` |
| `--led-brightness` | Brightness percentage (1-100) | `--led-brightness=50` |
| `--led-pwm-bits` | Color depth (1-11) | `--led-pwm-bits=7` |
| `-D` | Demo number to run | `-D 7` |

### Recommended First Run Command

```bash
sudo ./demo -D 7 \
  --led-rows=64 \
  --led-cols=64 \
  --led-gpio-mapping=adafruit-hat \
  --led-slowdown-gpio=2 \
  --led-brightness=50
```

Press **Ctrl+C** to stop the demo.

### If You See Flickering or Garbage

Try increasing the slowdown value:
```bash
sudo ./demo -D 7 --led-rows=64 --led-cols=64 --led-slowdown-gpio=4
```

If the display looks shifted or garbled, your panel might use a different multiplexing scheme. See [Troubleshooting](#troubleshooting).

---

## Custom Game of Life Implementation

### Option A — Python (Easiest to Modify)

Create a file called `game_of_life.py`:

```python
#!/usr/bin/env python3
"""
Conway's Game of Life on a 64x64 RGB LED Matrix.

Requires: rpi-rgb-led-matrix Python bindings installed.
Usage:    sudo python3 game_of_life.py
"""

import time
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# --- Configuration ---
ROWS = 64
COLS = 64
BRIGHTNESS = 50
GPIO_MAPPING = "adafruit-hat"
SLOWDOWN_GPIO = 2
GENERATION_DELAY = 0.1        # seconds between generations
ALIVE_COLOR = (0, 255, 0)     # green
DEAD_COLOR = (0, 0, 0)        # black (off)
INITIAL_DENSITY = 0.3         # 30% of cells start alive
STALE_RESET_GENS = 200        # auto-reset if population is stable for N generations


def create_matrix():
    """Initialize the RGB matrix with hardware configuration."""
    options = RGBMatrixOptions()
    options.rows = ROWS
    options.cols = COLS
    options.brightness = BRIGHTNESS
    options.gpio_slowdown = SLOWDOWN_GPIO
    options.hardware_mapping = GPIO_MAPPING
    # Reduce flicker
    options.pwm_lsb_nanoseconds = 130
    options.show_refresh_rate = False
    return RGBMatrix(options=options)


def random_grid():
    """Generate a random starting grid."""
    return [
        [1 if random.random() < INITIAL_DENSITY else 0 for _ in range(COLS)]
        for _ in range(ROWS)
    ]


def count_neighbors(grid, row, col):
    """Count live neighbors with wrapping (toroidal grid)."""
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r = (row + dr) % ROWS
            c = (col + dc) % COLS
            count += grid[r][c]
    return count


def next_generation(grid):
    """Compute the next generation using standard Game of Life rules."""
    new_grid = [[0] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            neighbors = count_neighbors(grid, r, c)
            if grid[r][c] == 1:
                # Alive cell survives with 2 or 3 neighbors
                new_grid[r][c] = 1 if neighbors in (2, 3) else 0
            else:
                # Dead cell becomes alive with exactly 3 neighbors
                new_grid[r][c] = 1 if neighbors == 3 else 0
    return new_grid


def population(grid):
    """Count total live cells."""
    return sum(sum(row) for row in grid)


def render(matrix, canvas, grid):
    """Draw the grid onto the LED matrix."""
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c]:
                canvas.SetPixel(c, r, *ALIVE_COLOR)
            else:
                canvas.SetPixel(c, r, *DEAD_COLOR)
    canvas = matrix.SwapOnVSync(canvas)
    return canvas


def main():
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()
    grid = random_grid()

    gen_count = 0
    stale_count = 0
    last_pop = 0

    print("Game of Life running. Press Ctrl+C to exit.")

    try:
        while True:
            canvas = render(matrix, canvas, grid)
            grid = next_generation(grid)
            gen_count += 1

            # Detect stale patterns and auto-reset
            current_pop = population(grid)
            if current_pop == last_pop:
                stale_count += 1
            else:
                stale_count = 0
            last_pop = current_pop

            if stale_count >= STALE_RESET_GENS or current_pop == 0:
                print(f"  Resetting at generation {gen_count} (pop={current_pop})")
                grid = random_grid()
                stale_count = 0

            time.sleep(GENERATION_DELAY)

    except KeyboardInterrupt:
        print(f"\nStopped after {gen_count} generations.")
        matrix.Clear()


if __name__ == "__main__":
    main()
```

**Run it:**
```bash
sudo python3 game_of_life.py
```

### Option B — C++ (Best Performance)

Create a file called `game_of_life.cc` in the `examples-api-use/` directory:

```cpp
/*
 * Conway's Game of Life on a 64x64 RGB LED Matrix.
 *
 * Build: make (from the examples-api-use directory after adding to Makefile)
 * Run:   sudo ./game-of-life --led-rows=64 --led-cols=64
 */

#include "led-matrix.h"
#include "threaded-canvas-manipulator.h"

#include <cstdlib>
#include <cstring>
#include <ctime>
#include <unistd.h>
#include <signal.h>

using namespace rgb_matrix;

volatile bool interrupted = false;
static void sigint_handler(int) { interrupted = true; }

class GameOfLife : public ThreadedCanvasManipulator {
public:
    GameOfLife(Canvas *canvas, int delay_ms = 100, float density = 0.3f)
        : ThreadedCanvasManipulator(canvas),
          delay_ms_(delay_ms),
          density_(density) {
        rows_ = canvas->height();
        cols_ = canvas->width();
        grid_ = new uint8_t[rows_ * cols_]();
        next_ = new uint8_t[rows_ * cols_]();
        Randomize();
    }

    ~GameOfLife() override {
        delete[] grid_;
        delete[] next_;
    }

    void Run() override {
        int stale_count = 0;
        int last_pop = 0;

        while (running() && !interrupted) {
            // Render
            for (int r = 0; r < rows_; r++) {
                for (int c = 0; c < cols_; c++) {
                    if (At(grid_, r, c)) {
                        canvas()->SetPixel(c, r, 0, 255, 0);  // green
                    } else {
                        canvas()->SetPixel(c, r, 0, 0, 0);    // off
                    }
                }
            }

            // Compute next generation
            for (int r = 0; r < rows_; r++) {
                for (int c = 0; c < cols_; c++) {
                    int n = CountNeighbors(r, c);
                    if (At(grid_, r, c)) {
                        Set(next_, r, c, (n == 2 || n == 3) ? 1 : 0);
                    } else {
                        Set(next_, r, c, (n == 3) ? 1 : 0);
                    }
                }
            }

            // Swap grids
            uint8_t *tmp = grid_;
            grid_ = next_;
            next_ = tmp;

            // Auto-reset on stale state
            int pop = Population();
            if (pop == last_pop) stale_count++;
            else stale_count = 0;
            last_pop = pop;

            if (stale_count > 200 || pop == 0) {
                Randomize();
                stale_count = 0;
            }

            usleep(delay_ms_ * 1000);
        }
    }

private:
    uint8_t &At(uint8_t *g, int r, int c) {
        return g[r * cols_ + c];
    }

    void Set(uint8_t *g, int r, int c, uint8_t v) {
        g[r * cols_ + c] = v;
    }

    int CountNeighbors(int r, int c) {
        int count = 0;
        for (int dr = -1; dr <= 1; dr++) {
            for (int dc = -1; dc <= 1; dc++) {
                if (dr == 0 && dc == 0) continue;
                int nr = (r + dr + rows_) % rows_;
                int nc = (c + dc + cols_) % cols_;
                count += At(grid_, nr, nc);
            }
        }
        return count;
    }

    int Population() {
        int count = 0;
        for (int i = 0; i < rows_ * cols_; i++)
            count += grid_[i];
        return count;
    }

    void Randomize() {
        for (int i = 0; i < rows_ * cols_; i++) {
            grid_[i] = (static_cast<float>(rand()) / RAND_MAX < density_) ? 1 : 0;
        }
    }

    int rows_, cols_;
    int delay_ms_;
    float density_;
    uint8_t *grid_;
    uint8_t *next_;
};

int main(int argc, char *argv[]) {
    srand(time(nullptr));
    signal(SIGINT, sigint_handler);

    RGBMatrix::Options defaults;
    defaults.rows = 64;
    defaults.cols = 64;
    defaults.hardware_mapping = "adafruit-hat";

    RuntimeOptions runtime;
    runtime.gpio_slowdown = 2;

    RGBMatrix *matrix = RGBMatrix::CreateFromFlags(&argc, &argv, &defaults, &runtime);
    if (matrix == nullptr) {
        fprintf(stderr, "Could not create matrix. Check your flags.\n");
        return 1;
    }

    printf("Game of Life running on %dx%d. Press Ctrl+C to stop.\n",
           matrix->width(), matrix->height());

    GameOfLife *life = new GameOfLife(matrix, 100);
    life->Start();

    while (!interrupted) {
        sleep(1);
    }

    life->Stop();
    delete life;
    delete matrix;

    printf("\nDone.\n");
    return 0;
}
```

**Build it** (add to the Makefile in `examples-api-use/` or compile manually):

```bash
cd ~/rpi-rgb-led-matrix
g++ -o game-of-life examples-api-use/game_of_life.cc \
    -I include -L lib -lrgbmatrix -lpthread -lrt -lm \
    -O3 -Wall
```

**Run it:**
```bash
sudo ./game-of-life --led-rows=64 --led-cols=64 --led-gpio-mapping=adafruit-hat
```

---

## Configuration and Tuning

### Color Customization

In the Python version, modify these variables at the top of the file:

```python
# Solid colors
ALIVE_COLOR = (0, 255, 0)     # bright green

# Age-based coloring (add this to the render function):
# Young cells = bright green, older cells fade to blue
# Requires tracking cell age in the grid (use int > 1 for age)
```

### Speed Control

```python
GENERATION_DELAY = 0.05   # faster (20 FPS)
GENERATION_DELAY = 0.2    # slower (5 FPS)
GENERATION_DELAY = 0.0    # as fast as possible
```

### Initial Patterns

Instead of random initialization, you can seed with classic patterns. Add these functions to the Python version:

```python
def clear_grid():
    """Create an empty grid."""
    return [[0] * COLS for _ in range(ROWS)]


def add_glider(grid, row, col):
    """Place a glider at (row, col)."""
    pattern = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    for dr, dc in pattern:
        grid[(row + dr) % ROWS][(col + dc) % COLS] = 1


def add_blinker(grid, row, col):
    """Place a blinker (period-2 oscillator) at (row, col)."""
    for dc in range(3):
        grid[row % ROWS][(col + dc) % COLS] = 1


def add_glider_gun(grid, row, col):
    """Place a Gosper Glider Gun at (row, col)."""
    gun = [
        (0,24),
        (1,22),(1,24),
        (2,12),(2,13),(2,20),(2,21),(2,34),(2,35),
        (3,11),(3,15),(3,20),(3,21),(3,34),(3,35),
        (4,0),(4,1),(4,10),(4,16),(4,20),(4,21),
        (5,0),(5,1),(5,10),(5,14),(5,16),(5,17),(5,22),(5,24),
        (6,10),(6,16),(6,24),
        (7,11),(7,15),
        (8,12),(8,13),
    ]
    for dr, dc in gun:
        grid[(row + dr) % ROWS][(col + dc) % COLS] = 1


# Usage: replace random_grid() in main() with:
# grid = clear_grid()
# add_glider_gun(grid, 10, 10)
```

### Brightness and Flicker Tuning

| Symptom | Solution |
|---------|----------|
| Too bright / washed out | Reduce `--led-brightness` to 30-50 |
| Flickering | Increase `--led-slowdown-gpio` (try 2, 3, or 4) |
| Ghosting / faint lines | Set `--led-pwm-lsb-nanoseconds=130` |
| Wrong colors | Check `--led-rgb-sequence` (try `RBG` or `BGR`) |

---

## Alternative Approaches

### Approach 2 — Dedicated GoL Repo (jfhenriques/rgb-matrix-gol)

If you want a standalone Game of Life binary rather than using the demo:

```bash
cd ~
git clone https://github.com/jfhenriques/rgb-matrix-gol.git
cd rgb-matrix-gol
git submodule update --init
make
sudo ./gol --led-rows=64 --led-cols=64 --led-gpio-mapping=adafruit-hat
```

### Approach 3 — CircuitPython on Raspberry Pi Pico

If you prefer a microcontroller over a full Raspberry Pi:

**Hardware needed:**
- Raspberry Pi Pico
- 64x64 HUB75 RGB LED panel
- Level shifter (3.3V to 5V for HUB75 signals)

**Steps:**
1. Install CircuitPython on the Pico (download UF2 from circuitpython.org)
2. Install required libraries:
   - `adafruit_matrixportal`
   - `rgbmatrix`
3. Reference implementation: https://www.henriaanstoot.nl/2024/04/05/64x64-matrixrgb-plus-conways-game-of-life/

### Approach 4 — Adafruit MatrixPortal

For a more integrated solution:
- Uses the **Adafruit MatrixPortal M4** board (built-in HUB75 driver)
- CircuitPython-based
- Tutorial: https://learn.adafruit.com/rgb-led-matrices-matrix-panels-with-circuitpython/example-conways-game-of-life

---

## Troubleshooting

### Display Issues

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Nothing displays | Power not connected to panel | Check 5V power to both panel AND HAT |
| Garbled / shifted image | Wrong row multiplexing | Try `--led-multiplexing=1` through `--led-multiplexing=18` |
| Only top half works | Panel is 1/16 scan, not 1/32 | Verify you have a 1/32 scan 64x64 panel |
| Colors are wrong | RGB sequence differs | Try `--led-rgb-sequence=RBG` or `BGR` |
| Flickering | GPIO too fast for wiring | Increase `--led-slowdown-gpio` |
| Ghost images | PWM timing issue | Add `--led-pwm-lsb-nanoseconds=130` |

### Permission Issues

The LED matrix requires root access to directly control GPIO:

```bash
# Always run with sudo
sudo ./demo -D 7 --led-rows=64 --led-cols=64

# For Python
sudo python3 game_of_life.py
```

If you don't want to use `sudo`, you can set up GPIO permissions:
```bash
sudo usermod -a -G gpio $USER
# Then log out and back in
```

### Pi Won't Boot After Config Changes

If the Pi doesn't boot after editing `/boot/config.txt` or `/boot/cmdline.txt`:
1. Remove the microSD card
2. Mount it on another computer
3. Revert your changes in the config files
4. Re-insert and boot

### Performance Tips

1. **Use C++ over Python** for the smoothest animation — Python adds ~10ms per frame of overhead
2. **Isolate a CPU core** (see setup Step 8) for dedicated matrix refresh
3. **Disable unnecessary services**:
   ```bash
   sudo systemctl disable bluetooth
   sudo systemctl disable avahi-daemon
   ```
4. **Use `--led-pwm-bits=7`** instead of the default 11 — fewer bits = faster refresh

### Auto-Start on Boot

To run Game of Life automatically when the Pi powers on:

```bash
sudo nano /etc/systemd/system/gameoflife.service
```

Add:
```ini
[Unit]
Description=Conway's Game of Life LED Display
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/pi/rpi-rgb-led-matrix/examples-api-use/demo -D 7 --led-rows=64 --led-cols=64 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=2 --led-brightness=50
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl enable gameoflife.service
sudo systemctl start gameoflife.service
```

---

## Project Structure

```
game_of_life/
├── README.md              # This file — full build & programming guide
├── python/
│   └── game_of_life.py    # Custom Python implementation
├── cpp/
│   └── game_of_life.cc    # Custom C++ implementation
└── patterns/
    └── patterns.py        # Classic GoL pattern definitions
```

## License

This guide and the custom code in this repository are released under the MIT License. The `hzeller/rpi-rgb-led-matrix` library has its own license (GPL-2.0).
