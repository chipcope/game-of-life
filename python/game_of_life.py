#!/usr/bin/env python3
"""
Conway's Game of Life on a 64x64 RGB LED Matrix.

Night sky with twinkling stars → dawn transition → blue sea.

Timing derives from two rhythms:
  • The breath: 5s twinkle cycle. Pauses are ¼, ½, 1, 1½ fractions.
  • The heartbeat: 750ms generation tick ≈ resting pulse.
  • Scroll decelerates line-to-line by φ (golden ratio).

Requires: rpi-rgb-led-matrix Python bindings installed.
Usage:    sudo python3 game_of_life.py
"""

import math
import time
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from bubble_font import (
    text_to_bitmap, bitmap_to_grid, overlay_bitmap_to_grid,
    CHAR_HEIGHT, CELL_WIDTH
)

# --- Configuration ---
ROWS = 64
COLS = 64
BRIGHTNESS = 50
GPIO_MAPPING = "adafruit-hat"
SLOWDOWN_GPIO = 2
ALIVE_COLOR = (0, 255, 0)
DEAD_COLOR = (0, 0, 255)       # primary blue sea
NIGHT_COLOR = (0, 0, 0)
STAR_COLOR = (200, 220, 255)
INITIAL_DENSITY = 0.20
STALE_RESET_GENS = 50

# --- The Breath ---
#   Everything nests inside the twinkle cycle.
#   Twinkle = 5s. Pauses are cycle fractions.
#   Scroll decelerates by φ (golden ratio).
#   Generation tick ≈ resting heartbeat.

HEARTBEAT = 0.750                     # 80 BPM
PHI = 1.618033988749895
TWINKLE_PERIOD = 5.0                  # one full cycle in seconds

# --- Stars ---
NUM_STARS = 12
TWINKLE_HZ = 1.0 / TWINKLE_PERIOD

# --- Ticker ---
TICKER_LINES = [
    "Fate isnt what were up against",
    "There is no design",
    "No flaws to find",
]
SCROLL_BASE_DELAY = 0.047
SCROLL_EXPONENTS = [0, 1, 1.5]        # φ exponents per line: 1×, φ, φ^1.5
PAUSE_BETWEEN_LINES = HEARTBEAT       # one heartbeat between lines
STARGAZE = TWINKLE_PERIOD             # one full breath before first scroll
SEED_HOLD = TWINKLE_PERIOD * 1.5     # 7.5s — breath and a half on last word
TEXT_COLOR = ALIVE_COLOR

# --- Dawn ---
DAWN_STEPS = 50
DAWN_STEP_DELAY = SEED_HOLD / DAWN_STEPS

# --- Simulation ---
DISSOLVE_TOTAL_GENS = 12              # accelerating cascade

# Last-word vertical positions
FIND_Y_TOP = 1
FIND_Y_MID = 22                       # == (ROWS - CHAR_HEIGHT) // 2
FIND_Y_BOT = 43
FIND_Y_UPPER_BRIDGE = 11             # centered on top/mid boundary (row 21)
FIND_Y_LOWER_BRIDGE = 32             # centered on mid/bot boundary (row 42)

# Dissolve schedule: accelerating cascade (gaps: 4, 3, 2, 1 gens)
DISSOLVE_SCHEDULE = [
    ( 4, FIND_Y_TOP),                 # phase 2 (gap: 4)
    ( 7, FIND_Y_BOT),                 # phase 3 (gap: 3)
    ( 9, FIND_Y_UPPER_BRIDGE),        # phase 4 (gap: 2)
    (10, FIND_Y_LOWER_BRIDGE),        # phase 5 (gap: 1)
]

# --- Circadian Rhythm ---
#   Random walk on 9 steps, centered on 750ms (80 BPM).
#   Every 8 generations: step up, down, or stay (equal odds).
#   Reflects at boundaries. Produces a bell curve around center.
CIRCADIAN_STEPS = [0.600, 0.632, 0.674, 0.714, 0.750, 0.800, 0.857, 0.938, 1.034]
CIRCADIAN_CENTER = 4
CIRCADIAN_STRIDE = 8


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def create_matrix():
    options = RGBMatrixOptions()
    options.rows = ROWS
    options.cols = COLS
    options.brightness = BRIGHTNESS
    options.gpio_slowdown = SLOWDOWN_GPIO
    options.hardware_mapping = GPIO_MAPPING
    options.pwm_lsb_nanoseconds = 130
    options.show_refresh_rate = False
    return RGBMatrix(options=options)


class StarField:
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

    def get_brightness(self, phase):
        t = time.time() - self.start_time
        val = math.sin(2 * math.pi * TWINKLE_HZ * t + phase)
        return max(0.0, val)


def render_night_frame(canvas, bitmap, x_offset, y_offset, stars,
                        bg_rgb=NIGHT_COLOR, star_mult=1.0):
    """Render one frame: background + stars + text."""
    # Build text pixel set
    text_pixels = set()
    for row in range(len(bitmap)):
        py = y_offset + row
        if py < 0 or py >= ROWS:
            continue
        for col in range(len(bitmap[row])):
            px = x_offset + col
            if px < 0 or px >= COLS:
                continue
            if bitmap[row][col]:
                text_pixels.add((py, px))

    # Fill background
    for r in range(ROWS):
        for c in range(COLS):
            canvas.SetPixel(c, r, *bg_rgb)

    # Stars
    if star_mult > 0.01:
        for (r, c, phase) in stars.stars:
            if (r, c) in text_pixels:
                continue
            brightness = stars.get_brightness(phase) * star_mult
            if brightness > 0.05:
                sc = lerp_color(bg_rgb, STAR_COLOR, brightness)
                canvas.SetPixel(c, r, *sc)

    # Text
    for (py, px) in text_pixels:
        canvas.SetPixel(px, py, *TEXT_COLOR)


def scroll_line(matrix, canvas, text, y_offset, stars, line_index=0):
    bitmap = text_to_bitmap(text)
    text_width = len(bitmap[0]) if bitmap else 0
    # Each line decelerates by φ raised to its exponent
    delay = SCROLL_BASE_DELAY * PHI ** SCROLL_EXPONENTS[line_index]
    x = COLS
    while x > -text_width:
        render_night_frame(canvas, bitmap, x, y_offset, stars)
        canvas = matrix.SwapOnVSync(canvas)
        x -= 1
        time.sleep(delay)
    return canvas


def scroll_final_and_dawn(matrix, canvas, text, y_offset, stars, line_index=0):
    bitmap = text_to_bitmap(text)
    find_text = "find"
    find_start = (len(text) - len(find_text)) * CELL_WIDTH
    x_stop = -find_start
    delay = SCROLL_BASE_DELAY * PHI ** SCROLL_EXPONENTS[line_index]

    # Scroll until last word is centered
    x = COLS
    while x > x_stop:
        render_night_frame(canvas, bitmap, x, y_offset, stars)
        canvas = matrix.SwapOnVSync(canvas)
        x -= 1
        time.sleep(delay)

    # Dawn transition
    find_bitmap = text_to_bitmap(find_text)
    print(f"  Dawn transition ({DAWN_STEPS} steps)...")
    for step in range(DAWN_STEPS):
        t = step / DAWN_STEPS
        bg = lerp_color(NIGHT_COLOR, DEAD_COLOR, t)
        star_fade = 1.0 - t
        render_night_frame(canvas, find_bitmap, 0, y_offset, stars,
                            bg_rgb=bg, star_mult=star_fade)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(DAWN_STEP_DELAY)

    grid = bitmap_to_grid(find_bitmap, COLS, ROWS,
                           x_offset=0, y_offset=y_offset)
    return canvas, grid


def render_grid(matrix, canvas, grid):
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c]:
                canvas.SetPixel(c, r, *ALIVE_COLOR)
            else:
                canvas.SetPixel(c, r, *DEAD_COLOR)
    return matrix.SwapOnVSync(canvas)


def startup_sequence(matrix, canvas):
    y_offset = (ROWS - CHAR_HEIGHT) // 2
    stars = StarField(y_offset, CHAR_HEIGHT)

    # Stargazing pause
    print("  Stargazing...")
    pause_end = time.time() + STARGAZE
    while time.time() < pause_end:
        render_night_frame(canvas, [[]], 0, y_offset, stars)
        canvas = matrix.SwapOnVSync(canvas)
        time.sleep(0.08)

    for i, line in enumerate(TICKER_LINES[:-1]):
        print(f'  Scrolling: "{line}"')
        canvas = scroll_line(matrix, canvas, line, y_offset, stars,
                              line_index=i)
        # Pause with twinkling stars
        pause_end = time.time() + PAUSE_BETWEEN_LINES
        while time.time() < pause_end:
            render_night_frame(canvas, [[]], 0, y_offset, stars)
            canvas = matrix.SwapOnVSync(canvas)
            time.sleep(0.08)

    print(f'  Scrolling: "{TICKER_LINES[-1]}" (stopping on last word)')
    canvas, grid = scroll_final_and_dawn(
        matrix, canvas, TICKER_LINES[-1], y_offset, stars,
        line_index=len(TICKER_LINES) - 1
    )
    return canvas, grid


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


def main():
    matrix = create_matrix()
    canvas = matrix.CreateFrameCanvas()

    print("=== Startup Ticker ===")
    canvas, grid = startup_sequence(matrix, canvas)

    print("\n=== Dissolving (triple last word) ===")
    find_bitmap = text_to_bitmap("find")
    gen_count = 0
    stale_count = 0
    last_pop = 0
    dissolving = True
    dissolve_phase = 1  # 1=center only, 2–8=overlays
    circadian_pos = CIRCADIAN_CENTER

    try:
        while True:
            canvas = render_grid(matrix, canvas, grid)
            grid = next_generation(grid)
            gen_count += 1

            current_pop = population(grid)
            if current_pop == last_pop:
                stale_count += 1
            else:
                stale_count = 0
            last_pop = current_pop

            if gen_count <= 30 or gen_count % 25 == 0:
                print(f"  Gen {gen_count}: pop={current_pop}")

            # Phased dissolve: overlay new last word at phase boundaries
            if dissolving:
                idx = dissolve_phase - 1  # schedule is 0-indexed
                if (idx < len(DISSOLVE_SCHEDULE)
                        and gen_count >= DISSOLVE_SCHEDULE[idx][0]):
                    y = DISSOLVE_SCHEDULE[idx][1]
                    print(f"  Phase {dissolve_phase + 1}: "
                          f"overlaying last word at y={y}")
                    overlay_bitmap_to_grid(find_bitmap, grid,
                                           x_offset=0, y_offset=y)
                    dissolve_phase += 1
                    stale_count = 0
                elif (idx >= len(DISSOLVE_SCHEDULE)
                        and gen_count >= DISSOLVE_TOTAL_GENS):
                    print("  Dissolve complete, entering cruise "
                          "(natural seed)")
                    dissolving = False
                    stale_count = 0

            if not dissolving:
                if stale_count >= STALE_RESET_GENS or current_pop == 0:
                    print(f"  Resetting at gen {gen_count} "
                          f"(pop={current_pop})")
                    grid = random_grid()
                    stale_count = 0

                # Circadian rhythm: random walk every CIRCADIAN_STRIDE gens
                # (frozen during dissolve for deterministic cascade timing)
                if gen_count % CIRCADIAN_STRIDE == 0:
                    move = random.choice([-1, 0, 1])
                    new_pos = circadian_pos + move
                    if new_pos < 0:
                        new_pos = 1
                    elif new_pos >= len(CIRCADIAN_STEPS):
                        new_pos = len(CIRCADIAN_STEPS) - 2
                    circadian_pos = new_pos
                    if move != 0:
                        bpm = round(60 / CIRCADIAN_STEPS[new_pos])
                        print(f"  Circadian: step {new_pos} "
                              f"({CIRCADIAN_STEPS[new_pos]:.3f}s, "
                              f"~{bpm} BPM)")

            time.sleep(CIRCADIAN_STEPS[circadian_pos])

    except KeyboardInterrupt:
        print(f"\nStopped after {gen_count} generations.")
        matrix.Clear()


if __name__ == "__main__":
    main()
