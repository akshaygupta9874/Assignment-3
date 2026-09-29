# ==============================================================================
# Makefile
# CSE/PC/B/S/314 Computer Networks Lab - Assignment 3: CSMA Protocols
# ==============================================================================

CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2 -Icommon -Istation
LDFLAGS ?= -lm

COMMON_SRCS = common/channel_wire.c common/logger.c
SERVER_SRCS = channel/channel_server.c $(COMMON_SRCS)
STATION_SRCS = station/station.c station/mac_strategies.c $(COMMON_SRCS)

BIN_DIR = bin
LOG_DIR = logs
RESULTS_DIR = results

TARGETS = $(BIN_DIR)/channel_server $(BIN_DIR)/station

.PHONY: all clean dirs

all: dirs $(TARGETS)

dirs:
	@mkdir -p $(BIN_DIR) $(LOG_DIR) $(RESULTS_DIR)/charts $(RESULTS_DIR)/data

$(BIN_DIR)/channel_server: $(SERVER_SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "  [BUILD] Successfully built $@"

$(BIN_DIR)/station: $(STATION_SRCS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "  [BUILD] Successfully built $@"

clean:
	rm -rf $(BIN_DIR)/* $(LOG_DIR)/*
	@echo "  [CLEAN] Cleaned binaries and logs."
