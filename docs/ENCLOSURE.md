# Enclosure Build Guide

## Shadow Box Frame Assembly

**Frame:** Frametory 8×8 Shadow Box, 2" depth, front-opening magnetic door, tan/natural wood  
**Display:** 64×64 RGB LED Matrix, 3mm pitch (192mm × 192mm / 7.56" × 7.56")  
**Controller:** Raspberry Pi 3 A+ (65mm × 56mm) + Adafruit RGB Matrix Bonnet (66mm × 31mm)

### Component Stack (front to back)

| Layer | Component | Thickness |
|-------|-----------|-----------|
| 1 | Diffusion acrylic (replaces glass) | 2.6mm |
| 2 | LED panel (face against acrylic) | ~12mm |
| 3 | Air gap / wiring | ~8mm |
| 4 | Pi 3 A+ with Bonnet on GPIO | ~25mm |
| **Total** | | **~48mm** |

Frame interior depth: 2" (50.8mm). Clearance: ~3mm. Snug fit.

### Fit Notes

The frame interior opening is 7.5" × 7.5" (190.5mm). The panel is 192mm (7.56"). This is 1.5mm oversize — a friction fit. If it won't seat, lightly sand or file the panel's plastic edge frame (not the PCB) on two sides. Remove material from the panel, not the frame.

---

## Parts List

| Part | Source | Price |
|------|--------|-------|
| Frametory 8×8 Shadow Box, Tan, 2" deep | [Amazon](https://www.amazon.com/Frametory-8x8-Black-Shadow-Case/dp/B07V3TBC7R) | ~$18 |
| Adafruit Black LED Diffusion Acrylic 12×12" | [Adafruit #4749](https://www.adafruit.com/product/4749) | $5 |
| Uglu Dashes adhesive rectangles | [Amazon](https://www.amazon.com/s?k=uglu+dashes) | ~$6 |
| M2.5 × 6mm nylon standoffs (4 pack) | Amazon | ~$5 |
| 5V 4A power supply with 2.1mm barrel jack | [Adafruit](https://www.adafruit.com/product/1466) | ~$15 |
| 2.1mm barrel jack to screw terminal adapter | [Adafruit](https://www.adafruit.com/product/368) | ~$3 |
| Micro-USB right-angle cable (6", optional) | Amazon | ~$6 |

**Total enclosure cost (excluding Pi, Bonnet, panel):** ~$58

---

## Frame Modifications

### 1. Remove the Glass

Open the magnetic front door. The glass panel is held by clips or friction — remove it carefully and set aside (keep as backup). The diffusion acrylic replaces it.

### 2. Remove the Linen Backboard

Pull out the felt/linen backing board. You won't need it — the LED panel sits directly in the frame.

### 3. Cut the Diffusion Acrylic

The 12×12" acrylic sheet needs to be cut to fit the 7.5" frame opening.

**Target size:** 190mm × 190mm (7.48" × 7.48") — slightly under the 7.5" opening so it drops in without binding.

**Cutting method:**
- Score and snap: Use a metal straightedge and utility knife. Score the protective paper side deeply (5-6 passes), then snap over a table edge. Acrylic this thin (2.6mm) snaps cleanly.
- Or: bandsaw/tablesaw with fine-tooth blade.

Peel protective paper from both sides after cutting. The **matte side faces outward** (toward the viewer).

### 4. Cable Exit Notch

Cut or file a small notch in the bottom edge of the frame's rear panel (or bottom rail) for the power cable to exit cleanly.

**Size:** ~12mm wide × 5mm deep — just enough for a barrel jack cable or two wires.

**Method:** Small file, Dremel, or even a sharp chisel. The MDF is soft.

**Location:** Bottom center of the frame back, so the cable drops straight down when wall-mounted, or exits underneath when on a desk.

### 5. Optional: Ventilation Holes

The Pi 3 A+ runs cool at this workload, but if you want belt-and-suspenders airflow, drill 4× small holes (3-4mm) in the top rear of the frame. Not strictly necessary — the front-opening door provides some passive ventilation.

---

## Assembly

### Step 1: Mount Pi + Bonnet to Panel

The LED panel has M3 mounting holes on the back (typically 4 corners and/or magnet screw holes). Use these to attach nylon standoffs, then mount the Pi on the standoffs.

1. Seat the **Bonnet on the Pi's 40-pin GPIO header** (it just pushes on)
2. Attach **4× M2.5 nylon standoffs** (6mm) to the back of the LED panel using the panel's mounting holes. You may need M3-to-M2.5 adapters or just use M3 standoffs with the Pi's mounting holes.
3. The Pi sits behind the panel, components facing outward (away from the panel), with the Bonnet on top.

**Orientation:** Position the Pi so the micro-USB power port faces toward the bottom of the frame (where your cable notch is).

### Step 2: Connect IDC Cable

Connect the **16-pin IDC ribbon cable** from the Bonnet's HUB75 output to the LED panel's HUB75 INPUT header. The cable is short — fold it neatly between the Pi and the panel back.

### Step 3: Wire Power

The Bonnet has screw terminals for 5V power input. This single connection powers both the LED panel and the Pi.

1. Connect the **2.1mm barrel jack adapter** to the Bonnet's screw terminals (observe polarity: + to +, – to –)
2. Route the barrel jack cable through the frame's cable notch
3. The 5V 4A adapter plugs into a wall outlet

**Important:** The Bonnet powers both the panel AND the Pi through the GPIO header. You do NOT need a separate micro-USB cable to the Pi unless you want redundant power.

### Step 4: Seat Panel in Frame

1. Drop the **diffusion acrylic** into the frame's front channel (matte side out)
2. Apply **4× Uglu Dashes** to the acrylic's inner face (one per corner)
3. Press the **LED panel face-first** onto the acrylic, so the LEDs are right against the diffuser
4. The Pi+Bonnet assembly now faces into the depth of the shadow box

### Step 5: Close It Up

Route the power cable through the notch, close the magnetic front door, and power on.

---

## Software: Auto-Boot

The Pi should boot directly into the Game of Life display with no monitor, keyboard, or user intervention.

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

On power-up, the Pi boots headless, the service starts, and the display begins the ticker sequence automatically.

---

## Display Placement

### Wall Mount
The shadow box has sawtooth hangers on the back. Hang it like a picture. The power cable drops down the wall to an outlet. Use cable clips or paintable cord cover for a clean look.

### Desk / Shelf
The frame sits flat or use a small easel stand behind it. The front-opening door means you can access internals without moving the frame.

### Viewing Distance
At 3mm pitch, the diffusion acrylic smooths the pixel grid nicely from about 2 feet and beyond. Up close (~12") you'll still see individual LED glow spots, which honestly looks cool — like a backlit medieval manuscript.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Only half the display lights up | Solder the **E address jumper** on the Bonnet (bridge to pin 8). Required for 64×64 panels. |
| Display is garbled or wrong colors | Check IDC cable orientation — the red stripe on the ribbon should align with pin 1 |
| Display is very dim | Insufficient power supply. Need 5V **4A minimum** for a 64×64 panel |
| Pi won't boot | Check microSD card is properly flashed. Try re-imaging with Raspberry Pi Imager |
| Flickering | Add `isolcpus=3` to `/boot/cmdline.txt` to dedicate a CPU core to the matrix driver |
| Panel is 1.5mm too wide for frame | File or sand the panel's plastic edge frame on two sides. Remove from the panel, not the frame |
