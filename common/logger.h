/* ==============================================================================
 * logger.h
 * High-precision thread-safe dual-output logger for CSMA simulation
 * Features: microsecond timestamps, thread identification, atomic mutex locking
 * ============================================================================== */

#ifndef LOGGER_H
#define LOGGER_H

#include <stdio.h>
#include <stdbool.h>
#include <pthread.h>

typedef enum {
    LOG_LVL_DEBUG = 0,
    LOG_LVL_LOCK  = 1,
    LOG_LVL_INFO  = 2,
    LOG_LVL_WARN  = 3,
    LOG_LVL_COLL  = 4,
    LOG_LVL_SUCC  = 5,
    LOG_LVL_ERROR = 6
} LogLevel;

void logger_init(const char *log_filepath, const char *prefix);
void logger_close(void);
void logger_set_min_level(LogLevel min_level);
void logger_set_thread_name(const char *name);
void log_event(LogLevel level, const char *fmt, ...);

#endif /* LOGGER_H */
