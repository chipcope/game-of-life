/*
 * Conway's Game of Life on a 64x64 RGB LED Matrix.
 *
 * Night sky with twinkling stars → dawn transition → blue sea.
 *
 * Timing derives from two rhythms:
 *   The breath: 5s twinkle cycle. Pauses are 1/4, 1/2, 1, 3/2 fractions.
 *   The heartbeat: 750ms generation tick.
 *   Scroll decelerates line-to-line by phi (golden ratio).
 *
 * Requires: hzeller/rpi-rgb-led-matrix library built and installed.
 *
 * Build (from cpp/ directory):  make
 * Run:                          sudo ./game-of-life
 */

#include "bubble_font.h"
#include "led-matrix.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <signal.h>
#include <string>
#include <unistd.h>
#include <vector>
#include <set>
#include <utility>
#include <sys/time.h>

using namespace rgb_matrix;

// --- Configuration ---
static const int ROWS = 64;
static const int COLS = 64;

// --- The Breath ---
//   Everything nests inside the twinkle cycle.
//   Twinkle = 5s. Pauses are cycle fractions.
//   Scroll decelerates by φ (golden ratio).
//   Generation tick ≈ resting heartbeat.

static const int HEARTBEAT_US        = 750000;   // 80 BPM
static const double PHI              = 1.618033988749895;
static const int TWINKLE_US          = 5000000;  // 5s — the fundamental breath

static const int SCROLL_BASE_DELAY_US = 47000;
static const double SCROLL_EXPONENTS[] = {0, 1, 1.5};  // φ exponents per line
static const int PAUSE_BETWEEN_US    = HEARTBEAT_US;  // one heartbeat between lines
static const int STARGAZE_US         = TWINKLE_US;            // one full breath
static const int SEED_HOLD_US        = TWINKLE_US * 3 / 2;   // 7.5s — breath and a half
static const int DISSOLVE_PHASE_GENS = 4;
static const int DISSOLVE_TOTAL_GENS = 32;   // 8 phases × 4 gens
static const int STALE_RESET_GENS    = 50;
static const float INITIAL_DENSITY   = 0.20f;

// Last-word vertical positions
static const int FIND_Y_TOP          = 1;
static const int FIND_Y_MID          = 22;   // == (ROWS - CHAR_HEIGHT) / 2
static const int FIND_Y_BOT          = 43;
static const int FIND_Y_UPPER_BRIDGE = 11;   // centered on top/mid boundary (row 21)
static const int FIND_Y_LOWER_BRIDGE = 32;   // centered on mid/bot boundary (row 42)

// Dissolve schedule: 7 overlays after the initial dawn seed (phase 1)
static const struct { int gen; int y; } DISSOLVE_SCHEDULE[] = {
    { DISSOLVE_PHASE_GENS * 1,  FIND_Y_TOP          },  // phase 2
    { DISSOLVE_PHASE_GENS * 2,  FIND_Y_BOT          },  // phase 3
    { DISSOLVE_PHASE_GENS * 3,  FIND_Y_UPPER_BRIDGE },  // phase 4
    { DISSOLVE_PHASE_GENS * 4,  FIND_Y_LOWER_BRIDGE },  // phase 5
    { DISSOLVE_PHASE_GENS * 5,  FIND_Y_MID          },  // phase 6 (center repeat)
    { DISSOLVE_PHASE_GENS * 6,  FIND_Y_TOP          },  // phase 7 (top repeat)
    { DISSOLVE_PHASE_GENS * 7,  FIND_Y_BOT          },  // phase 8 (bottom repeat)
};
static const int NUM_DISSOLVE_OVERLAYS = 7;

// --- Circadian Rhythm ---
//   Random walk on 9 steps, centered on 750ms (80 BPM).
//   Every 8 generations: step up, down, or stay (equal odds).
//   Reflects at boundaries. Produces a bell curve around center.
static const int CIRCADIAN_STEPS[]   = {600000, 632000, 674000, 714000, 750000,
                                        800000, 857000, 938000, 1034000};
static const int CIRCADIAN_COUNT     = 9;
static const int CIRCADIAN_CENTER    = 4;
static const int CIRCADIAN_STRIDE    = 8;

// Colors
static const uint8_t ALIVE_R = 0, ALIVE_G = 255, ALIVE_B = 0;
static const uint8_t DEAD_R = 0, DEAD_G = 0, DEAD_B = 255;
static const uint8_t NIGHT_R = 0, NIGHT_G = 0, NIGHT_B = 0;
static const uint8_t STAR_R = 200, STAR_G = 220, STAR_B = 255;

// Stars
static const int NUM_STARS = 12;
static const double TWINKLE_HZ = 1.0 / 5.0;

// Dawn
static const int DAWN_STEPS = 50;
static const int DAWN_STEP_US = SEED_HOLD_US / DAWN_STEPS;

static const char *TICKER_LINES[] = {
    "Fate isnt what were up against",
    "There is no design",
    "No flaws to find",
};
static const int NUM_LINES = 3;

volatile bool interrupted = false;
static void sigint_handler(int) { interrupted = true; }

// --- Time helper ---
static double now_seconds() {
    struct timeval tv;
    gettimeofday(&tv, nullptr);
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}

// --- Color helpers ---
static uint8_t lerp(uint8_t a, uint8_t b, double t) {
    return (uint8_t)(a + (b - a) * t);
}

// --- Star field ---
struct Star {
    int row, col;
    double phase;
};

static std::vector<Star> stars;
static double stars_start_time;

static void init_stars(int y_offset, int char_height) {
    stars_start_time = now_seconds();
    stars.clear();
    int text_top = y_offset;
    int text_bot = y_offset + char_height;

    // Collect sky pixels
    std::vector<std::pair<int,int>> sky;
    for (int r = 0; r < ROWS; r++) {
        if (r >= text_top && r < text_bot) continue;
        for (int c = 0; c < COLS; c++) {
            sky.push_back({r, c});
        }
    }

    // Random sample
    for (int i = 0; i < NUM_STARS && !sky.empty(); i++) {
        int idx = rand() % sky.size();
        Star s;
        s.row = sky[idx].first;
        s.col = sky[idx].second;
        s.phase = ((double)rand() / RAND_MAX) * 2.0 * M_PI;
        stars.push_back(s);
        sky.erase(sky.begin() + idx);
    }
}

static double star_brightness(const Star &s) {
    double t = now_seconds() - stars_start_time;
    double val = sin(2.0 * M_PI * TWINKLE_HZ * t + s.phase);
    return val > 0.0 ? val : 0.0;
}

// --- Grid helpers ---

static inline uint8_t &at(uint8_t *g, int r, int c) {
    return g[r * COLS + c];
}

static int count_neighbors(uint8_t *g, int r, int c) {
    int count = 0;
    for (int dr = -1; dr <= 1; dr++) {
        for (int dc = -1; dc <= 1; dc++) {
            if (dr == 0 && dc == 0) continue;
            int nr = (r + dr + ROWS) % ROWS;
            int nc = (c + dc + COLS) % COLS;
            count += at(g, nr, nc);
        }
    }
    return count;
}

static void next_generation(uint8_t *grid, uint8_t *next) {
    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            int n = count_neighbors(grid, r, c);
            if (at(grid, r, c))
                at(next, r, c) = (n == 2 || n == 3) ? 1 : 0;
            else
                at(next, r, c) = (n == 3) ? 1 : 0;
        }
    }
}

static int population(uint8_t *g) {
    int count = 0;
    for (int i = 0; i < ROWS * COLS; i++) count += g[i];
    return count;
}

static void randomize(uint8_t *g) {
    for (int i = 0; i < ROWS * COLS; i++)
        g[i] = ((float)rand() / RAND_MAX < INITIAL_DENSITY) ? 1 : 0;
}

// --- Rendering ---

static void render_grid(FrameCanvas *canvas, uint8_t *g) {
    for (int r = 0; r < ROWS; r++) {
        for (int c = 0; c < COLS; c++) {
            if (at(g, r, c))
                canvas->SetPixel(c, r, ALIVE_R, ALIVE_G, ALIVE_B);
            else
                canvas->SetPixel(c, r, DEAD_R, DEAD_G, DEAD_B);
        }
    }
}

static void render_night_frame(FrameCanvas *canvas,
                                const std::vector<std::vector<uint8_t>> &bitmap,
                                int x_off, int y_off,
                                uint8_t bg_r, uint8_t bg_g, uint8_t bg_b,
                                double star_mult) {
    // Build text pixel set
    std::set<std::pair<int,int>> text_pixels;
    for (int row = 0; row < (int)bitmap.size(); row++) {
        int py = y_off + row;
        if (py < 0 || py >= ROWS) continue;
        for (int col = 0; col < (int)bitmap[row].size(); col++) {
            int px = x_off + col;
            if (px < 0 || px >= COLS) continue;
            if (bitmap[row][col])
                text_pixels.insert({py, px});
        }
    }

    // Fill background
    for (int r = 0; r < ROWS; r++)
        for (int c = 0; c < COLS; c++)
            canvas->SetPixel(c, r, bg_r, bg_g, bg_b);

    // Stars
    if (star_mult > 0.01) {
        for (const auto &s : stars) {
            if (text_pixels.count({s.row, s.col})) continue;
            double b = star_brightness(s) * star_mult;
            if (b > 0.05) {
                canvas->SetPixel(s.col, s.row,
                    lerp(bg_r, STAR_R, b),
                    lerp(bg_g, STAR_G, b),
                    lerp(bg_b, STAR_B, b));
            }
        }
    }

    // Text
    for (const auto &p : text_pixels)
        canvas->SetPixel(p.second, p.first, ALIVE_R, ALIVE_G, ALIVE_B);
}

// --- Ticker ---

static int scroll_delay_for_index(int line_index) {
    // Each line decelerates by φ raised to its exponent
    return (int)(SCROLL_BASE_DELAY_US * pow(PHI, SCROLL_EXPONENTS[line_index]));
}

static FrameCanvas *scroll_line(RGBMatrix *matrix, FrameCanvas *canvas,
                                 const char *text, int y_offset,
                                 int line_index = 0) {
    auto bitmap = text_to_bitmap(text);
    int text_width = bitmap.empty() ? 0 : (int)bitmap[0].size();
    int delay = scroll_delay_for_index(line_index);

    for (int x = COLS; x > -text_width && !interrupted; x--) {
        render_night_frame(canvas, bitmap, x, y_offset,
                            NIGHT_R, NIGHT_G, NIGHT_B, 1.0);
        canvas = matrix->SwapOnVSync(canvas);
        usleep(delay);
    }
    return canvas;
}

static FrameCanvas *pause_with_stars(RGBMatrix *matrix, FrameCanvas *canvas,
                                      int y_offset, int duration_us) {
    std::vector<std::vector<uint8_t>> empty_bitmap;
    int elapsed = 0;
    int step = 80000; // 80ms
    while (elapsed < duration_us && !interrupted) {
        render_night_frame(canvas, empty_bitmap, 0, y_offset,
                            NIGHT_R, NIGHT_G, NIGHT_B, 1.0);
        canvas = matrix->SwapOnVSync(canvas);
        int wait = (duration_us - elapsed < step) ? (duration_us - elapsed) : step;
        usleep(wait);
        elapsed += wait;
    }
    return canvas;
}

static FrameCanvas *scroll_final_and_dawn(RGBMatrix *matrix, FrameCanvas *canvas,
                                           const char *text, int y_offset,
                                           uint8_t *grid,
                                           int line_index = 0) {
    std::string full(text);
    std::string find_text = "find";
    auto bitmap = text_to_bitmap(full);

    int find_start = ((int)full.size() - (int)find_text.size()) * CELL_WIDTH;
    int x_stop = -find_start;

    // Scroll until last word centered
    int delay = scroll_delay_for_index(line_index);
    for (int x = COLS; x > x_stop && !interrupted; x--) {
        render_night_frame(canvas, bitmap, x, y_offset,
                            NIGHT_R, NIGHT_G, NIGHT_B, 1.0);
        canvas = matrix->SwapOnVSync(canvas);
        usleep(delay);
    }

    // Dawn transition
    auto find_bitmap = text_to_bitmap(find_text);
    printf("  Dawn transition (%d steps)...\n", DAWN_STEPS);
    for (int step = 0; step < DAWN_STEPS && !interrupted; step++) {
        double t = (double)step / DAWN_STEPS;
        uint8_t bg_r = lerp(NIGHT_R, DEAD_R, t);
        uint8_t bg_g = lerp(NIGHT_G, DEAD_G, t);
        uint8_t bg_b = lerp(NIGHT_B, DEAD_B, t);
        double star_fade = 1.0 - t;
        render_night_frame(canvas, find_bitmap, 0, y_offset,
                            bg_r, bg_g, bg_b, star_fade);
        canvas = matrix->SwapOnVSync(canvas);
        usleep(DAWN_STEP_US);
    }

    // Build seed grid
    bitmap_to_grid(find_bitmap, grid, COLS, ROWS, 0, y_offset);
    return canvas;
}

// --- Main ---

int main(int argc, char *argv[]) {
    srand(time(nullptr));
    signal(SIGINT, sigint_handler);

    RGBMatrix::Options defaults;
    defaults.rows = ROWS;
    defaults.cols = COLS;
    defaults.hardware_mapping = "adafruit-hat";
    defaults.brightness = 50;
    defaults.pwm_lsb_nanoseconds = 130;

    RuntimeOptions runtime;
    runtime.gpio_slowdown = 2;

    RGBMatrix *matrix = RGBMatrix::CreateFromFlags(&argc, &argv,
                                                     &defaults, &runtime);
    if (!matrix) {
        fprintf(stderr, "Could not create matrix. Check your flags.\n");
        return 1;
    }

    FrameCanvas *canvas = matrix->CreateFrameCanvas();
    int y_offset = (ROWS - CHAR_HEIGHT) / 2;

    uint8_t *grid = new uint8_t[ROWS * COLS]();
    uint8_t *next = new uint8_t[ROWS * COLS]();

    // Init stars
    init_stars(y_offset, CHAR_HEIGHT);

    // --- Startup Ticker ---
    printf("=== Startup Ticker ===\n\n");

    // Stargazing pause
    printf("  Stargazing...\n");
    canvas = pause_with_stars(matrix, canvas, y_offset, STARGAZE_US);

    for (int i = 0; i < NUM_LINES - 1 && !interrupted; i++) {
        printf("  Scrolling: \"%s\"\n", TICKER_LINES[i]);
        canvas = scroll_line(matrix, canvas, TICKER_LINES[i], y_offset, i);
        canvas = pause_with_stars(matrix, canvas, y_offset, PAUSE_BETWEEN_US);
    }

    if (!interrupted) {
        printf("  Scrolling: \"%s\" (stopping on last word)\n",
               TICKER_LINES[NUM_LINES - 1]);
        canvas = scroll_final_and_dawn(matrix, canvas,
                                        TICKER_LINES[NUM_LINES - 1],
                                        y_offset, grid,
                                        NUM_LINES - 1);
    }

    // --- Game of Life ---
    printf("\n=== Dissolving (triple last word) ===\n");

    auto find_bitmap = text_to_bitmap("find");
    int gen_count = 0;
    int stale_count = 0;
    int last_pop = 0;
    bool dissolving = true;
    int dissolve_phase = 1;  // 1=center only, 2–8=overlays
    int circadian_pos = CIRCADIAN_CENTER;

    while (!interrupted) {
        render_grid(canvas, grid);
        canvas = matrix->SwapOnVSync(canvas);

        next_generation(grid, next);
        uint8_t *tmp = grid;
        grid = next;
        next = tmp;
        gen_count++;

        int pop = population(grid);
        if (pop == last_pop) stale_count++;
        else stale_count = 0;
        last_pop = pop;

        if (gen_count <= 30 || gen_count % 25 == 0)
            printf("  Gen %d: pop=%d\n", gen_count, pop);

        // Phased dissolve: overlay new last word at phase boundaries
        if (dissolving) {
            int idx = dissolve_phase - 1;  // schedule is 0-indexed
            if (idx < NUM_DISSOLVE_OVERLAYS
                    && gen_count >= DISSOLVE_SCHEDULE[idx].gen) {
                printf("  Phase %d: overlaying last word at y=%d\n",
                       dissolve_phase + 1, DISSOLVE_SCHEDULE[idx].y);
                overlay_bitmap_to_grid(find_bitmap, grid, COLS, ROWS,
                                       0, DISSOLVE_SCHEDULE[idx].y);
                dissolve_phase++;
                stale_count = 0;
            } else if (idx >= NUM_DISSOLVE_OVERLAYS
                           && gen_count >= DISSOLVE_TOTAL_GENS) {
                printf("  Dissolve complete, entering cruise (natural seed)\n");
                dissolving = false;
                stale_count = 0;
            }
        }

        if (!dissolving && (stale_count >= STALE_RESET_GENS || pop == 0)) {
            printf("  Resetting at gen %d (pop=%d)\n", gen_count, pop);
            randomize(grid);
            stale_count = 0;
        }

        // Circadian rhythm: random walk every CIRCADIAN_STRIDE gens
        if (gen_count % CIRCADIAN_STRIDE == 0) {
            int move = (rand() % 3) - 1;  // -1, 0, or 1
            int new_pos = circadian_pos + move;
            if (new_pos < 0) new_pos = 1;
            else if (new_pos >= CIRCADIAN_COUNT) new_pos = CIRCADIAN_COUNT - 2;
            circadian_pos = new_pos;
            if (move != 0) {
                int bpm = 60000000 / CIRCADIAN_STEPS[new_pos];
                printf("  Circadian: step %d (%dms, ~%d BPM)\n",
                       new_pos, CIRCADIAN_STEPS[new_pos] / 1000, bpm);
            }
        }

        usleep(CIRCADIAN_STEPS[circadian_pos]);
    }

    printf("\nStopped after %d generations.\n", gen_count);
    matrix->Clear();
    delete[] grid;
    delete[] next;
    delete matrix;
    return 0;
}
