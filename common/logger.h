/* ==============================================================================
 * logger.h
 * High-precision dual-output logger for CSMA simulation
 * ============================================================================== */

#ifndef LOGGER_H
#define LOGGER_H

#include <stdio.h>
#include <stdbool.h>

typedef enum {
    LOG_LVL_DEBUG = 0,
    LOG_LVL_INFO  = 1,
    LOG_LVL_WARN  = 2,
    LOG_LVL_COLL  = 3,
    LOG_LVL_SUCC  = 4,
    LOG_LVL_ERROR = 5
} LogLevel;

void logger_init(const char *log_filepath, const char *prefix);
void logger_close(void);
void log_event(LogLevel level, const char *fmt, ...);

#endif /* LOGGER_H */
