"""
Classic Conway's Game of Life patterns for a 64x64 grid.

Usage:
    from patterns import load_pattern

    grid = load_pattern("glider_gun", rows=64, cols=64)
"""

ROWS = 64
COLS = 64


def empty_grid(rows=ROWS, cols=COLS):
    """Create an empty grid."""
    return [[0] * cols for _ in range(rows)]


def place_pattern(grid, pattern, row_offset, col_offset):
    """Place a list of (row, col) offsets onto the grid with wrapping."""
    rows = len(grid)
    cols = len(grid[0])
    for dr, dc in pattern:
        grid[(row_offset + dr) % rows][(col_offset + dc) % cols] = 1


# --- Still Lifes ---

BLOCK = [(0, 0), (0, 1), (1, 0), (1, 1)]

BEEHIVE = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 2)]

LOAF = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 3), (3, 2)]

BOAT = [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)]

TUB = [(0, 1), (1, 0), (1, 2), (2, 1)]


# --- Oscillators ---

BLINKER = [(0, 0), (0, 1), (0, 2)]

TOAD = [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]

BEACON = [(0, 0), (0, 1), (1, 0), (2, 3), (3, 2), (3, 3)]

PULSAR = [
    (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
    (2, 0), (2, 5), (2, 7), (2, 12),
    (3, 0), (3, 5), (3, 7), (3, 12),
    (4, 0), (4, 5), (4, 7), (4, 12),
    (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
    (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
    (8, 0), (8, 5), (8, 7), (8, 12),
    (9, 0), (9, 5), (9, 7), (9, 12),
    (10, 0), (10, 5), (10, 7), (10, 12),
    (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10),
]

PENTADECATHLON = [
    (0, 1), (1, 1), (2, 0), (2, 2), (3, 1), (4, 1),
    (5, 1), (6, 1), (7, 0), (7, 2), (8, 1), (9, 1),
]


# --- Spaceships ---

GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]

LWSS = [  # Lightweight Spaceship
    (0, 1), (0, 4),
    (1, 0),
    (2, 0), (2, 4),
    (3, 0), (3, 1), (3, 2), (3, 3),
]

MWSS = [  # Middleweight Spaceship
    (0, 2),
    (1, 0), (1, 4),
    (2, 5),
    (3, 0), (3, 5),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
]

HWSS = [  # Heavyweight Spaceship
    (0, 2), (0, 3),
    (1, 0), (1, 5),
    (2, 6),
    (3, 0), (3, 6),
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6),
]


# --- Guns ---

GOSPER_GLIDER_GUN = [
    (0, 24),
    (1, 22), (1, 24),
    (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
    (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
    (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
    (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
    (6, 10), (6, 16), (6, 24),
    (7, 11), (7, 15),
    (8, 12), (8, 13),
]


# --- Methuselahs ---

R_PENTOMINO = [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)]

DIEHARD = [(0, 6), (1, 0), (1, 1), (2, 1), (2, 5), (2, 6), (2, 7)]

ACORN = [(0, 1), (1, 3), (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)]


# --- Pattern catalog ---

PATTERNS = {
    # Still lifes
    "block": BLOCK,
    "beehive": BEEHIVE,
    "loaf": LOAF,
    "boat": BOAT,
    "tub": TUB,
    # Oscillators
    "blinker": BLINKER,
    "toad": TOAD,
    "beacon": BEACON,
    "pulsar": PULSAR,
    "pentadecathlon": PENTADECATHLON,
    # Spaceships
    "glider": GLIDER,
    "lwss": LWSS,
    "mwss": MWSS,
    "hwss": HWSS,
    # Guns
    "gosper_glider_gun": GOSPER_GLIDER_GUN,
    # Methuselahs
    "r_pentomino": R_PENTOMINO,
    "diehard": DIEHARD,
    "acorn": ACORN,
}


def load_pattern(name, rows=ROWS, cols=COLS, row_offset=None, col_offset=None):
    """
    Load a named pattern onto a grid, centered by default.

    Args:
        name: Pattern name (see PATTERNS dict)
        rows: Grid height
        cols: Grid width
        row_offset: Row to place pattern (None = center)
        col_offset: Col to place pattern (None = center)

    Returns:
        2D grid with the pattern placed on it.
    """
    if name not in PATTERNS:
        available = ", ".join(sorted(PATTERNS.keys()))
        raise ValueError(f"Unknown pattern '{name}'. Available: {available}")

    pattern = PATTERNS[name]
    grid = empty_grid(rows, cols)

    # Calculate pattern bounding box for centering
    if row_offset is None or col_offset is None:
        max_r = max(r for r, c in pattern)
        max_c = max(c for r, c in pattern)
        if row_offset is None:
            row_offset = (rows - max_r) // 2
        if col_offset is None:
            col_offset = (cols - max_c) // 2

    place_pattern(grid, pattern, row_offset, col_offset)
    return grid


def list_patterns():
    """Print all available patterns."""
    categories = {
        "Still Lifes": ["block", "beehive", "loaf", "boat", "tub"],
        "Oscillators": ["blinker", "toad", "beacon", "pulsar", "pentadecathlon"],
        "Spaceships": ["glider", "lwss", "mwss", "hwss"],
        "Guns": ["gosper_glider_gun"],
        "Methuselahs": ["r_pentomino", "diehard", "acorn"],
    }
    for category, names in categories.items():
        print(f"\n{category}:")
        for name in names:
            print(f"  - {name}")
