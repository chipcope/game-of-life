#!/usr/bin/env python3
"""
Conway's Game of Life on a 64x64 RGB LED Matrix.
Preview version using tkinter.

Night sky with twinkling stars → dawn transition → blue sea.
Green text is the one constant as the world transforms around it.

Timing derives from two rhythms:
  • The breath: 5s twinkle cycle. Pauses are ¼, ½, 1, 1½ fractions.
  • The heartbeat: 750ms generation tick ≈ resting pulse.
  • Scroll decelerates line-to-line by φ (golden ratio).

Run:  python3 preview.py
"""

import math
import time
import random
import tkinter as tk
from bubble_font import (
    text_to_bitmap, bitmap_to_grid, overlay_bitmap_to_grid,
    CHAR_HEIGHT, CELL_WIDTH
)

# --- Matrix / Display Config ---
ROWS = 64
COLS = 64
PIXEL_SIZE = 10
WINDOW_W = COLS * PIXEL_SIZE
WINDOW_H = ROWS * PIXEL_SIZE

# --- Colors ---
#   Green: the one constant. Bright enough to pop against both
#   black night and blue day. The fixed point in a changing world.
ALIVE_RGB = (0, 255, 0)
ALIVE_HEX = '#00ff00'

#   Night: pure black
NIGHT_RGB = (0, 0, 0)

#   Day: primary blue sea
DAY_RGB = (0, 0, 255)
DAY_HEX = '#0000ff'

#   Stars: cool white with a hint of blue
STAR_RGB = (200, 220, 255)

# --- The Breath ---
#   Everything nests inside the twinkle cycle.
#   Twinkle = 5s. Pauses are cycle fractions.
#   Scroll decelerates by φ (golden ratio).
#   Generation tick ≈ resting heartbeat.

HEARTBEAT_MS = 750                    # 80 BPM
PHI = 1.618033988749895

# --- Stars ---
NUM_STARS = 12
TWINKLE_HZ = 1.0 / 5.0               # 5s cycle — the fundamental breath
TWINKLE_MS = 5000                     # one full cycle in ms

# --- Ticker ---
TICKER_LINES = [
    "Fate isnt what were up against",
    "There is no design",
    "No flaws to find",
]
SCROLL_BASE_DELAY_MS = 47             # px delay for longest line
SCROLL_EXPONENTS = [0, 1, 1.5]        # φ exponents per line: 1×, φ, φ^1.5
PAUSE_BETWEEN_MS = HEARTBEAT_MS       # one heartbeat between lines
STARGAZE_MS = TWINKLE_MS              # one full breath before first scroll
SEED_HOLD_MS = TWINKLE_MS + TWINKLE_MS // 2  # 7.5s — breath and a half on last word

# --- Dawn transition ---
DAWN_STEPS = 50
DAWN_STEP_MS = SEED_HOLD_MS // DAWN_STEPS  # 150ms per step

# --- Simulation ---
DISSOLVE_PHASE_GENS = 4
DISSOLVE_TOTAL_GENS = 20              # 5 phases × 4 gens
INITIAL_DENSITY = 0.20
STALE_RESET_GENS = 50

# Last-word vertical positions
FIND_Y_TOP = 1
FIND_Y_MID = 22                       # == (ROWS - CHAR_HEIGHT) // 2
FIND_Y_BOT = 43
FIND_Y_UPPER_BRIDGE = 11             # centered on top/mid boundary (row 21)
FIND_Y_LOWER_BRIDGE = 32             # centered on mid/bot boundary (row 42)

# Dissolve schedule: 4 overlays after the initial dawn seed (phase 1)
DISSOLVE_SCHEDULE = [
    (DISSOLVE_PHASE_GENS * 1, FIND_Y_TOP),           # phase 2
    (DISSOLVE_PHASE_GENS * 2, FIND_Y_BOT),           # phase 3
    (DISSOLVE_PHASE_GENS * 3, FIND_Y_UPPER_BRIDGE),  # phase 4
    (DISSOLVE_PHASE_GENS * 4, FIND_Y_LOWER_BRIDGE),  # phase 5
]

# --- Circadian Rhythm ---
#   Random walk on 9 steps, centered on 750ms (80 BPM).
#   Every 8 generations: step up, down, or stay (equal odds).
#   Reflects at boundaries. Produces a bell curve around center.
#
#   Step  BPM   Delay   Feel
#     0   100    600    energetic
#     1    95    632    lively
#     2    89    674    brisk
#     3    84    714    walking
#     4    80    750    center
#     5    75    800    easy
#     6    70    857    contemplative
#     7    64    938    meditative
#     8    58   1034    deep rest

CIRCADIAN_STEPS = [600, 632, 674, 714, 750, 800, 857, 938, 1034]
CIRCADIAN_CENTER = 4
CIRCADIAN_STRIDE = 8                  # gens between steps (one twinkle cycle)


def lerp_color(c1, c2, t):
    """Linear interpolate between two RGB tuples, t in [0, 1]."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


class StarField:
    """A handful of twinkling 1px stars that avoid the text band."""

    def __init__(self, y_offset, char_height):
        self.stars = []
        self.start_time = time.time()
        text_top = y_offset
        text_bot = y_offset + char_height
        sky_pixels = [(r, c) for r in range(ROWS) for c in range(COLS)
                      if r < text_top or r >= text_bot]
        chosen = random.sample(sky_pixels, min(NUM_STARS, len(sky_pixels)))
        for r, c in chosen:
            phase = random.uniform(0, 2 * math.pi)
            self.stars.append((r, c, phase))

    def get_brightness(self, phase, t=None):
        """Return 0.0–1.0 brightness for a star at current time."""
        if t is None:
            t = time.time() - self.start_time
        val = math.sin(2 * math.pi * TWINKLE_HZ * t + phase)
        return max(0.0, val)  # dark half the cycle = natural twinkle


class LEDMatrix:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game of Life — 64x64 LED Preview")
        self.root.configure(bg='#000000')
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root, width=WINDOW_W, height=WINDOW_H,
            bg='#000000', highlightthickness=0
        )
        self.canvas.pack()

        self.pixels = [[None] * COLS for _ in range(ROWS)]
        gap = 1
        for r in range(ROWS):
            for c in range(COLS):
                x0 = c * PIXEL_SIZE + gap
                y0 = r * PIXEL_SIZE + gap
                x1 = x0 + PIXEL_SIZE - gap * 2
                y1 = y0 + PIXEL_SIZE - gap * 2
                self.pixels[r][c] = self.canvas.create_rectangle(
                    x0, y0, x1, y1, fill='#000000', outline=''
                )

        self.root.bind('<Escape>', lambda e: self.root.destroy())

    def set_pixel(self, r, c, hex_color):
        self.canvas.itemconfig(self.pixels[r][c], fill=hex_color)

    def fill(self, hex_color):
        for r in range(ROWS):
            for c in range(COLS):
                self.canvas.itemconfig(self.pixels[r][c], fill=hex_color)

    def render_grid(self, grid):
        for r in range(ROWS):
            for c in range(COLS):
                self.canvas.itemconfig(
                    self.pixels[r][c],
                    fill=ALIVE_HEX if grid[r][c] else DAY_HEX
                )

    def update(self):
        self.root.update_idletasks()
        self.root.update()


class GameOfLife:
    def __init__(self):
        self.display = LEDMatrix()
        self.y_offset = (ROWS - CHAR_HEIGHT) // 2
        self.stars = StarField(self.y_offset, CHAR_HEIGHT)
        self.grid = None
        self.gen_count = 0
        self.stale_count = 0
        self.last_pop = 0
        self.dissolving = False
        self.circadian_pos = CIRCADIAN_CENTER

    def render_night_frame(self, bitmap, x_offset, bg_rgb=NIGHT_RGB,
                            star_mult=1.0):
        """Render one frame: background + stars + text."""
        bg_hex = rgb_to_hex(bg_rgb)
        t = time.time() - self.stars.start_time

        # Build a set of text pixel positions for this frame
        text_pixels = set()
        for row in range(len(bitmap)):
            py = self.y_offset + row
            if py < 0 or py >= ROWS:
                continue
            for col in range(len(bitmap[row])):
                px = x_offset + col
                if px < 0 or px >= COLS:
                    continue
                if bitmap[row][col]:
                    text_pixels.add((py, px))

        # Fill background
        self.display.fill(bg_hex)

        # Draw stars (if still visible)
        if star_mult > 0.01:
            for (r, c, phase) in self.stars.stars:
                if (r, c) in text_pixels:
                    continue
                brightness = self.stars.get_brightness(phase, t) * star_mult
                if brightness > 0.05:
                    star_color = lerp_color(bg_rgb, STAR_RGB, brightness)
                    self.display.set_pixel(r, c, rgb_to_hex(star_color))

        # Draw text
        for (py, px) in text_pixels:
            self.display.set_pixel(py, px, ALIVE_HEX)

    def scroll_line(self, text, callback, line_index=0):
        bitmap = text_to_bitmap(text)
        text_width = len(bitmap[0]) if bitmap else 0
        # Each line decelerates by φ raised to its exponent
        delay = round(SCROLL_BASE_DELAY_MS * PHI ** SCROLL_EXPONENTS[line_index])

        def step(x):
            if x <= -text_width:
                callback()
                return
            try:
                self.render_night_frame(bitmap, x)
                self.display.update()
                self.display.root.after(delay, lambda: step(x - 1))
            except tk.TclError:
                pass

        step(COLS)

    def scroll_final_line(self, text, callback, line_index=0):
        bitmap = text_to_bitmap(text)
        find_text = "find"
        find_start = (len(text) - len(find_text)) * CELL_WIDTH
        x_stop = -find_start
        delay = round(SCROLL_BASE_DELAY_MS * PHI ** SCROLL_EXPONENTS[line_index])

        def step(x):
            if x <= x_stop:
                self.dawn_transition(callback)
                return
            try:
                self.render_night_frame(bitmap, x)
                self.display.update()
                self.display.root.after(delay, lambda: step(x - 1))
            except tk.TclError:
                pass

        step(COLS)

    def dawn_transition(self, callback):
        """Sunrise: black→blue background, stars fade out, last word stays."""
        find_bitmap = text_to_bitmap("find")
        step_count = [0]

        def dawn_step():
            if step_count[0] >= DAWN_STEPS:
                # Build seed grid from last word
                self.grid = bitmap_to_grid(find_bitmap, COLS, ROWS,
                                            x_offset=0,
                                            y_offset=self.y_offset)
                callback()
                return
            try:
                t = step_count[0] / DAWN_STEPS  # 0.0 → 1.0
                bg = lerp_color(NIGHT_RGB, DAY_RGB, t)
                star_fade = 1.0 - t
                self.render_night_frame(find_bitmap, 0, bg_rgb=bg,
                                         star_mult=star_fade)
                self.display.update()
                step_count[0] += 1
                self.display.root.after(DAWN_STEP_MS, dawn_step)
            except tk.TclError:
                pass

        dawn_step()

    def pause_then(self, ms, callback):
        """Pause with night sky (stars still twinkling)."""
        empty_bitmap = [[]]

        def tick(remaining):
            if remaining <= 0:
                callback()
                return
            try:
                self.render_night_frame(empty_bitmap, 0)
                self.display.update()
                wait = min(remaining, 80)  # update stars ~12fps
                self.display.root.after(wait,
                                         lambda: tick(remaining - wait))
            except tk.TclError:
                pass

        tick(ms)

    def run_ticker(self):
        lines = list(TICKER_LINES)
        print("  Stargazing...")

        def scroll_next(idx):
            if idx < len(lines) - 1:
                print(f'  Scrolling: "{lines[idx]}"')
                self.scroll_line(
                    lines[idx],
                    lambda: self.pause_then(PAUSE_BETWEEN_MS,
                                             lambda: scroll_next(idx + 1)),
                    line_index=idx
                )
            else:
                print(f'  Scrolling: "{lines[idx]}" (stopping on last word)')
                self.scroll_final_line(lines[idx], self.start_dissolve,
                                        line_index=idx)

        scroll_next(0)

    def start_dissolve(self):
        print("\n=== Dissolving (triple last word) ===")
        self.gen_count = 0
        self.stale_count = 0
        self.last_pop = 0
        self.dissolving = True
        self.dissolve_phase = 1  # 1=center only, 2–8=overlays
        self.find_bitmap = text_to_bitmap("find")
        self.simulation_step()

    def simulation_step(self):
        try:
            self.display.render_grid(self.grid)
            self.display.update()

            self.grid = next_generation(self.grid)
            self.gen_count += 1

            current_pop = population(self.grid)
            if current_pop == self.last_pop:
                self.stale_count += 1
            else:
                self.stale_count = 0
            self.last_pop = current_pop

            if self.gen_count <= 30 or self.gen_count % 25 == 0:
                print(f"  Gen {self.gen_count}: pop={current_pop}")

            # Phased dissolve: overlay new last word at phase boundaries
            if self.dissolving:
                idx = self.dissolve_phase - 1  # schedule is 0-indexed
                if (idx < len(DISSOLVE_SCHEDULE)
                        and self.gen_count >= DISSOLVE_SCHEDULE[idx][0]):
                    y = DISSOLVE_SCHEDULE[idx][1]
                    print(f"  Phase {self.dissolve_phase + 1}: "
                          f"overlaying last word at y={y}")
                    overlay_bitmap_to_grid(self.find_bitmap, self.grid,
                                           x_offset=0, y_offset=y)
                    self.dissolve_phase += 1
                    self.stale_count = 0
                elif (idx >= len(DISSOLVE_SCHEDULE)
                        and self.gen_count >= DISSOLVE_TOTAL_GENS):
                    print("  Dissolve complete, entering cruise "
                          "(natural seed)")
                    self.dissolving = False
                    self.stale_count = 0

            if not self.dissolving:
                if self.stale_count >= STALE_RESET_GENS or current_pop == 0:
                    print(f"  Resetting at gen {self.gen_count} "
                          f"(pop={current_pop})")
                    self.grid = random_grid()
                    self.stale_count = 0

            # Circadian rhythm: random walk every CIRCADIAN_STRIDE gens
            if self.gen_count % CIRCADIAN_STRIDE == 0:
                move = random.choice([-1, 0, 1])
                new_pos = self.circadian_pos + move
                # Reflect at boundaries
                if new_pos < 0:
                    new_pos = 1
                elif new_pos >= len(CIRCADIAN_STEPS):
                    new_pos = len(CIRCADIAN_STEPS) - 2
                self.circadian_pos = new_pos
                if move != 0:
                    bpm = round(60000 / CIRCADIAN_STEPS[new_pos])
                    print(f"  Circadian: step {new_pos} "
                          f"({CIRCADIAN_STEPS[new_pos]}ms, ~{bpm} BPM)")

            gen_delay = CIRCADIAN_STEPS[self.circadian_pos]
            self.display.root.after(gen_delay, self.simulation_step)
        except tk.TclError:
            pass

    def run(self):
        print("=== Startup Ticker ===")
        print("(Press ESC or close window to quit)\n")
        self.display.root.after(100,
            lambda: self.pause_then(STARGAZE_MS, self.run_ticker))
        self.display.root.mainloop()


# --- Game of Life core ---

def random_grid():
    return [
        [1 if random.random() < INITIAL_DENSITY else 0 for _ in range(COLS)]
        for _ in range(ROWS)
    ]

def count_neighbors(grid, row, col):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            count += grid[(row + dr) % ROWS][(col + dc) % COLS]
    return count

def next_generation(grid):
    new_grid = [[0] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            n = count_neighbors(grid, r, c)
            if grid[r][c]:
                new_grid[r][c] = 1 if n in (2, 3) else 0
            else:
                new_grid[r][c] = 1 if n == 3 else 0
    return new_grid

def population(grid):
    return sum(sum(row) for row in grid)


if __name__ == "__main__":
    game = GameOfLife()
    game.run()
