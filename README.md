# Conway's Game of Life on a 64x64 RGB LED Matrix

A medieval blackletter ticker scrolls a cryptic message, lands on the word **"find"**, holds — then the letters dissolve under Game of Life rules. The simulation runs forever, its pace drifting with a circadian rhythm.

## Quick Start

**Preview on your Mac** (no hardware needed):

```bash
cd python
python3 preview.py
```

**Run on Raspberry Pi** (Python):

```bash
sudo python3 python/game_of_life.py
```

**Run on Raspberry Pi** (C++, best performance):

```bash
cd cpp
make
sudo ./game-of-life
```

---

## What Happens

Timing derives from two rhythms: the **breath** (5-second twinkle cycle) and the **heartbeat** (750ms generation tick, ~80 BPM). Scroll speed decelerates line-to-line by φ (golden ratio).

1. **Stargazing** — 5 seconds of pure night sky. 12 stars twinkle on black. One full breath before anything happens.
2. **Ticker** scrolls three lines in gothic blackletter, each line slower than the last (φ deceleration: 47ms → 76ms → 101ms per pixel):
   - *Fate isnt what were up against* — brisk
   - *Theres no design* — easing (¼-breath pause before)
   - *No flaw to find* — drifting (½-breath pause before)
3. **Dawn** — "find" holds for 7.5s (1½ breaths) as the background transitions from black → primary blue. Stars fade out.
4. **Dissolve** — Game of Life rules kick in. The letters shatter into green cells on a blue sea over 16 generations.
5. **Cruise** — simulation runs indefinitely with a **circadian rhythm**: a random walk across 9 tempo steps (58–100 BPM) that drifts every 8 generations, bell-curving around 80 BPM. Auto-reseeds after 50 stale generations.

**Colors:** Primary green (#00ff00) alive cells on primary blue (#0000ff) background. The green is the one constant as the world transforms around it.

---

## Hardware Requirements

| Component | Description | Approx. Cost |
|-----------|-------------|--------------|
| **Raspberry Pi 3 A+** (or 3B+/4B) | Main controller | $25-55 |
| **64x64 HUB75 RGB LED Matrix** | P3 or P4 pitch | $25-50 |
| **Adafruit RGB Matrix HAT/Bonnet** | GPIO to HUB75 interface | $25 |
| **5V 4A+ Power Supply** | Powers Pi + panel via Bonnet | $10-15 |
| **16GB+ microSD Card** | Raspberry Pi OS Lite (64-bit) | $8-12 |
| **Frametory 8×8 Shadow Box** | 2" depth, front-opening, tan | ~$18 |
| **Diffusion Acrylic 12×12"** | Frosted matte P95 (Amazon) or Adafruit black LED | ~$5–8 |

See [docs/ENCLOSURE.md](docs/ENCLOSURE.md) for the full enclosure build guide.

The Pi 3 A+ is recommended for its small form factor (65×56mm) — same SoC as 3B+, 512MB RAM is plenty for a single 64×64 panel.

---

## Hardware Assembly

1. Flash **Raspberry Pi OS Lite (64-bit)** via Raspberry Pi Imager. Enable SSH and WiFi in Imager settings before writing.
2. Seat the **RGB Matrix HAT/Bonnet** on all 40 GPIO pins
3. Connect **HUB75 ribbon cable**: HAT output → panel INPUT
4. Wire **5V power supply** to HAT screw terminals (powers both Pi and panel)
5. Disable onboard audio in `/boot/config.txt`: `dtparam=audio=off`

---

## Software Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git build-essential python3-dev python3-pip

# Build the LED matrix library
cd ~
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make

# Build Python bindings
cd bindings/python
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

---

## Configuration

Timing derives from two rhythms. The **breath** (5s twinkle cycle) governs pauses and transitions. The **heartbeat** (~750ms) governs generation ticks, modulated by a circadian random walk. Scroll speed decelerates by φ (golden ratio).

| Parameter | Value | Derivation |
|-----------|-------|------------|
| `TWINKLE` | 5s cycle | The fundamental breath |
| `STARGAZE` | 5000ms | 1 breath — opening pause |
| `PAUSE_BETWEEN` | 1250, 2500ms | ¼, ½ breath between lines |
| `SEED_HOLD` | 7500ms | 1½ breaths — "find" hold + dawn |
| `SCROLL_BASE_DELAY` | 47ms/px | Fastest line (line 1) |
| `SCROLL_EXPONENTS` | 0, 1, 1.5 | φ⁰=47, φ¹=76, φ^1.5=101 ms/px |
| `CIRCADIAN_STEPS` | 600–1034ms | 9 tempo steps, 58–100 BPM |
| `CIRCADIAN_STRIDE` | 8 gens | Random walk interval (~6s at center) |
| `DISSOLVE_GENS` | 16 | ~12s of letter dissolution |
| `STALE_RESET_GENS` | 50 | ~38s before auto-reseed |

---

## Auto-Start on Boot

```bash
sudo nano /etc/systemd/system/gameoflife.service
```

```ini
[Unit]
Description=Game of Life LED Display
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=/home/pi/game_of_life/cpp
ExecStart=/home/pi/game_of_life/cpp/game-of-life
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable gameoflife.service
sudo systemctl start gameoflife.service
```

---

## Project Structure

```
game_of_life/
├── README.md
├── docs/
│   └── ENCLOSURE.md         # Shadow box frame build guide
├── python/
│   ├── game_of_life.py      # Pi version (rgbmatrix)
│   ├── preview.py            # Mac preview (tkinter)
│   └── bubble_font.py        # Medieval blackletter glyphs
├── cpp/
│   ├── game_of_life.cc       # Pi version (C++)
│   ├── bubble_font.h         # Font header
│   └── Makefile
└── patterns/
    └── patterns.py            # Classic GoL pattern library
```

## Font

The medieval blackletter font is hand-designed at 14×20 pixels per glyph. Features include pointed triangular serifs, diamond dot on 'i', thick-thin stroke contrast, and a hand-hewn quality. Character set: `a d e f g h i l n o p r s t u w` (space).

## License

MIT. The `hzeller/rpi-rgb-led-matrix` library is GPL-2.0.
