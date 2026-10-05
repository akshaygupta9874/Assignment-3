/* ==============================================================================
 * logger.c
 * Implementation of formatted thread-safe event logger
 * Uses POSIX mutex to ensure atomic log serialization across concurrent threads.
 * Provides clean, readable logging with millisecond timestamps and minimal clutter.
 * ============================================================================== */

#include "logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <time.h>
#include <sys/time.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

static FILE *g_log_fp = NULL;
static char g_prefix[64] = "CSMA";
static pthread_mutex_t g_log_mutex = PTHREAD_MUTEX_INITIALIZER;
static __thread char t_thread_name[32] = "";
static LogLevel g_min_level = LOG_LVL_INFO;

#define ANSI_RESET   "\x1b[0m"
#define ANSI_RED     "\x1b[31;1m"
#define ANSI_GREEN   "\x1b[32;1m"
#define ANSI_YELLOW  "\x1b[33;1m"
#define ANSI_BLUE    "\x1b[34;1m"
#define ANSI_MAGENTA "\x1b[35;1m"
#define ANSI_CYAN    "\x1b[36;1m"
#define ANSI_GRAY    "\x1b[90m"

void logger_init(const char *log_filepath, const char *prefix) {
    pthread_mutex_lock(&g_log_mutex);
    if (prefix) {
        snprintf(g_prefix, sizeof(g_prefix), "%s", prefix);
    }
    if (log_filepath) {
        if (g_log_fp) {
            fclose(g_log_fp);
            g_log_fp = NULL;
        }
        g_log_fp = fopen(log_filepath, "w");
        if (!g_log_fp) {
            fprintf(stderr, "[WARN] Could not open log file %s\n", log_filepath);
        }
    }
    pthread_mutex_unlock(&g_log_mutex);
}

void logger_close(void) {
    pthread_mutex_lock(&g_log_mutex);
    if (g_log_fp) {
        fflush(g_log_fp);
        fclose(g_log_fp);
        g_log_fp = NULL;
    }
    pthread_mutex_unlock(&g_log_mutex);
}

void logger_set_min_level(LogLevel min_level) {
    pthread_mutex_lock(&g_log_mutex);
    g_min_level = min_level;
    pthread_mutex_unlock(&g_log_mutex);
}

void logger_set_thread_name(const char *name) {
    if (name) {
        snprintf(t_thread_name, sizeof(t_thread_name), "%s", name);
    }
}

void log_event(LogLevel level, const char *fmt, ...) {
    if (level < g_min_level) {
        return;
    }

    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *tm_info = localtime(&tv.tv_sec);

    char time_str[32];
    strftime(time_str, sizeof(time_str), "%H:%M:%S", tm_info);
    long msec = tv.tv_usec / 1000;

    const char *lvl_name = "INFO ";
    const char *color = ANSI_RESET;

    switch (level) {
        case LOG_LVL_DEBUG: lvl_name = "DEBUG"; color = ANSI_CYAN;    break;
        case LOG_LVL_LOCK:  lvl_name = "LOCK "; color = ANSI_GRAY;    break;
        case LOG_LVL_INFO:  lvl_name = "INFO "; color = ANSI_RESET;   break;
        case LOG_LVL_WARN:  lvl_name = "WARN "; color = ANSI_YELLOW;  break;
        case LOG_LVL_COLL:  lvl_name = "COLL "; color = ANSI_RED;     break;
        case LOG_LVL_SUCC:  lvl_name = "SUCC "; color = ANSI_GREEN;   break;
        case LOG_LVL_ERROR: lvl_name = "ERROR"; color = ANSI_RED;     break;
    }

    /* Clean, non-redundant source tag */
    char tag[80];
    if (t_thread_name[0] != '\0') {
        snprintf(tag, sizeof(tag), "[%s]", t_thread_name);
    } else {
        snprintf(tag, sizeof(tag), "[%s]", g_prefix);
    }

    char buffer[2048];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    /* Atomic write under lock */
    pthread_mutex_lock(&g_log_mutex);

    static int s_is_tty = -1;
    if (s_is_tty == -1) {
        s_is_tty = isatty(fileno(stdout));
    }

    /* Clean console output (colors only if terminal) */
    if (s_is_tty) {
        printf("[%s.%03ld] %s[%s]%s %-14s %s\n",
               time_str, msec, color, lvl_name, ANSI_RESET, tag, buffer);
    } else {
        printf("[%s.%03ld] [%s] %-14s %s\n",
               time_str, msec, lvl_name, tag, buffer);
    }
    fflush(stdout);

    /* Clean plain text file output (always free of ANSI codes) */
    if (g_log_fp) {
        fprintf(g_log_fp, "[%s.%03ld] [%s] %-14s %s\n",
                time_str, msec, lvl_name, tag, buffer);
        fflush(g_log_fp);
    }

    pthread_mutex_unlock(&g_log_mutex);
}
