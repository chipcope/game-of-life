/*
 * Conway's Game of Life on a 64x64 RGB LED Matrix.
 *
 * Requires: hzeller/rpi-rgb-led-matrix library built and installed.
 *
 * Build:
 *   g++ -o game-of-life game_of_life.cc \
 *       -I /path/to/rpi-rgb-led-matrix/include \
 *       -L /path/to/rpi-rgb-led-matrix/lib \
 *       -lrgbmatrix -lpthread -lrt -lm -O3 -Wall
 *
 * Run:
 *   sudo ./game-of-life --led-rows=64 --led-cols=64 --led-gpio-mapping=adafruit-hat
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
            // Render current state
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
