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
                new_grid[r][c] = 1 if neighbors in (2, 3) else 0
            else:
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
