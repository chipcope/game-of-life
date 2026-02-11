# Makefile for Game of Life on RGB LED Matrix
#
# Expects rpi-rgb-led-matrix to be cloned alongside this project,
# or set RGB_LIB_PATH to point to it.
#
# Build:  make
# Run:    sudo ./game-of-life
# Clean:  make clean

RGB_LIB_PATH ?= ../../rpi-rgb-led-matrix

CXXFLAGS = -O3 -Wall -Wextra -std=c++17
INCLUDES = -I$(RGB_LIB_PATH)/include -I.
LDFLAGS  = -L$(RGB_LIB_PATH)/lib -lrgbmatrix -lpthread -lrt -lm

TARGET = game-of-life
SRC    = game_of_life.cc

all: $(TARGET)

$(TARGET): $(SRC) bubble_font.h
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
