/* ==============================================================================
 * logger.c
 * Implementation of formatted thread-safe/process-safe event logger
 * ============================================================================== */

#include "logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <time.h>
#include <sys/time.h>
#include <string.h>

static FILE *g_log_fp = NULL;
static char g_prefix[64] = "CSMA";

#define ANSI_RESET   "\x1b[0m"
#define ANSI_RED     "\x1b[31;1m"
#define ANSI_GREEN   "\x1b[32;1m"
#define ANSI_YELLOW  "\x1b[33;1m"
#define ANSI_BLUE    "\x1b[34;1m"
#define ANSI_MAGENTA "\x1b[35;1m"
#define ANSI_CYAN    "\x1b[36;1m"

void logger_init(const char *log_filepath, const char *prefix) {
    if (prefix) {
        snprintf(g_prefix, sizeof(g_prefix), "%s", prefix);
    }
    if (log_filepath) {
        g_log_fp = fopen(log_filepath, "w");
        if (!g_log_fp) {
            fprintf(stderr, "[WARN] Could not open log file %s\n", log_filepath);
        }
    }
}

void logger_close(void) {
    if (g_log_fp) {
        fflush(g_log_fp);
        fclose(g_log_fp);
        g_log_fp = NULL;
    }
}

void log_event(LogLevel level, const char *fmt, ...) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *tm_info = localtime(&tv.tv_sec);

    char time_str[32];
    strftime(time_str, sizeof(time_str), "%H:%M:%S", tm_info);
    int ms = (int)(tv.tv_usec / 1000);

    const char *lvl_name = "INFO";
    const char *color = ANSI_RESET;

    switch (level) {
        case LOG_LVL_DEBUG: lvl_name = "DEBUG"; color = ANSI_CYAN; break;
        case LOG_LVL_INFO:  lvl_name = "INFO "; color = ANSI_RESET; break;
        case LOG_LVL_WARN:  lvl_name = "WARN "; color = ANSI_YELLOW; break;
        case LOG_LVL_COLL:  lvl_name = "COLL "; color = ANSI_RED; break;
        case LOG_LVL_SUCC:  lvl_name = "SUCC "; color = ANSI_GREEN; break;
        case LOG_LVL_ERROR: lvl_name = "ERROR"; color = ANSI_RED; break;
    }

    char buffer[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    /* Output to stdout with color */
    printf("[%s.%03d] [%s] %s[%s]%s %s\n",
           time_str, ms, g_prefix, color, lvl_name, ANSI_RESET, buffer);
    fflush(stdout);

    /* Output to file without color */
    if (g_log_fp) {
        fprintf(g_log_fp, "[%s.%03d] [%s] [%s] %s\n",
                time_str, ms, g_prefix, lvl_name, buffer);
        fflush(g_log_fp);
    }
}
