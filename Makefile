# ==============================================================================
# Makefile
# CSE/PC/B/S/314 Computer Networks Lab - Assignment 3: CSMA Protocols
# Concurrent Multi-Threaded Simulation (POSIX pthreads, Mutexes & Condition Vars)
# ==============================================================================

CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2 -pthread
LDFLAGS ?= -pthread -lm

BIN_DIR = bin
LOG_DIR = logs
RESULTS_DIR = results

TARGET = $(BIN_DIR)/csma_sim

.PHONY: all clean dirs run

all: dirs $(TARGET)

dirs:
	@mkdir -p $(BIN_DIR) $(LOG_DIR) $(RESULTS_DIR)/charts $(RESULTS_DIR)/data

$(TARGET): csma_sim.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "  [BUILD] Successfully built $@"

run: $(TARGET)
	@./$(TARGET)

clean:
	rm -rf $(BIN_DIR)/* $(LOG_DIR)/*
	@echo "  [CLEAN] Cleaned binaries and logs."
