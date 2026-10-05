/* ==============================================================================
 * csma_sim.c
 * Concurrent Multi-Threaded CSMA & CSMA/CD Simulation (IEEE 802.3 Standard)
 * Fully Interactive Menu-Driven System with Dual Terminal & File Logging
 *
 * Implements:
 * 1. Interactive terminal menu for strategy selection, station counts, and sweeps
 * 2. N concurrent station nodes executed as POSIX threads (pthread_create/join)
 * 3. Shared physical broadcast channel with constructive voltage superposition
 *    (0.0V = IDLE, 1.0V = BUSY, >= 2.0V = COLLISION)
 * 4. POSIX mutexes and condition variables for thread-safe medium synchronization
 * 5. Microsecond Listen-While-Talk preemption, 32-bit jam signals (0x55555555),
 *    and Truncated Binary Exponential Backoff (BEB) strictly in CSMA/CD
 * 6. Uniform random backoff and zero jam signals in non-CD strategies
 * 7. Thread-safe dual logger writing to both console and log files:
 *    - logs/csma_simulation.log (latest run)
 *    - logs/csma_sim_<strategy>.log (historical per-strategy log)
 * 8. Built-in log viewer option in the interactive menu
 * ============================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <strings.h>
#include <stdarg.h>
#include <unistd.h>
#include <pthread.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <math.h>

#define MAX_STATIONS          64
#define DEFAULT_SLOT_TIME_MS  4.0   /* Slot time (2 * Tau) */
#define DEFAULT_PROP_DELAY_MS 2.0   /* One-way propagation delay Tau */
#define DEFAULT_FRAME_TIME_MS 8.0   /* Frame transmission time */
#define DEFAULT_JAM_TIME_MS   1.0   /* 32-bit jam sequence duration */
#define BEB_MAX_ATTEMPTS      16    /* Max attempts before abort */
#define BEB_TRUNCATION_LIMIT  10    /* Truncation ceiling (2^10 = 1024 slots) */
#define FRAME_BYTE_SIZE       64    /* Minimum Ethernet frame size */
#define JAM_PATTERN_32BIT     0x55555555U

/* ANSI Terminal Colors */
#define COLOR_RESET   "\033[0m"
#define COLOR_BOLD    "\033[1m"
#define COLOR_RED     "\033[31m"
#define COLOR_GREEN   "\033[32m"
#define COLOR_YELLOW  "\033[33m"
#define COLOR_BLUE    "\033[34m"
#define COLOR_MAGENTA "\033[35m"
#define COLOR_CYAN    "\033[36m"

typedef enum {
    STRATEGY_CSMA_CD        = 1,
    STRATEGY_1_PERSISTENT   = 2,
    STRATEGY_NON_PERSISTENT = 3,
    STRATEGY_P_PERSISTENT   = 4
} MacStrategy;

typedef enum {
    CHAN_IDLE      = 0,
    CHAN_BUSY      = 1,
    CHAN_COLLISION = 2
} ChannelState;

/* Per-Station Performance Metrics */
typedef struct {
    int      station_id;
    uint32_t attempts;
    uint32_t successes;
    uint32_t collisions;
    uint32_t busy_senses;
    double   total_backoff_ms;
    double   total_latency_ms;
} StationMetrics;

/* Shared Physical Channel Medium */
typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t  idle_cond;
    pthread_cond_t  collision_cond;

    ChannelState    state;
    float           voltage;
    int             active_transmitters;
    int             active_station_ids[MAX_STATIONS];
    bool            collision_flag;

    /* Timing parameters */
    double          slot_time_ms;
    double          prop_delay_ms;
    double          frame_tx_time_ms;
    double          jam_duration_ms;
    double          first_tx_start_ms;

    /* Global simulation metrics */
    uint32_t        total_tx_attempts;
    uint32_t        total_successful_frames;
    uint32_t        total_collisions;
    uint32_t        total_jams;
    double          channel_idle_time_ms;
    double          channel_busy_time_ms;
    double          channel_collision_time_ms;
    double          last_state_change_ms;
} ChannelBus;

/* Thread Arguments per Station */
typedef struct {
    int            station_id;
    MacStrategy    strategy;
    int            num_frames;
    double         p_val;
    ChannelBus    *bus;
    StationMetrics metrics;
} StationThreadArgs;

static volatile bool g_running = true;

/* Global Dual-Logging Handlers */
static FILE *g_log_latest = NULL;
static FILE *g_log_strat  = NULL;
static pthread_mutex_t g_log_mutex = PTHREAD_MUTEX_INITIALIZER;

/* --------------------------------------------------------------------------
 * Thread-Safe Dual Logger (Console + Log Files)
 * -------------------------------------------------------------------------- */
static void log_event(const char *color, const char *tag, const char *fmt, ...) {
    char time_str[32];
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *tm_info = localtime(&tv.tv_sec);
    strftime(time_str, sizeof(time_str), "%H:%M:%S", tm_info);

    char msg[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(msg, sizeof(msg), fmt, args);
    va_end(args);

    pthread_mutex_lock(&g_log_mutex);

    /* 1. Terminal stdout with ANSI colors */
    printf("%s[%s.%03d] [%-4s] %s%s\n",
           color, time_str, (int)(tv.tv_usec / 1000), tag, msg, COLOR_RESET);
    fflush(stdout);

    /* 2. File outputs without ANSI escape codes */
    if (g_log_latest) {
        fprintf(g_log_latest, "[%s.%03d] [%-4s] %s\n",
                time_str, (int)(tv.tv_usec / 1000), tag, msg);
        fflush(g_log_latest);
    }
    if (g_log_strat) {
        fprintf(g_log_strat, "[%s.%03d] [%-4s] %s\n",
                time_str, (int)(tv.tv_usec / 1000), tag, msg);
        fflush(g_log_strat);
    }

    pthread_mutex_unlock(&g_log_mutex);
}

static void log_raw(const char *fmt, ...) {
    char msg[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(msg, sizeof(msg), fmt, args);
    va_end(args);

    pthread_mutex_lock(&g_log_mutex);
    printf("%s", msg);
    fflush(stdout);

    if (g_log_latest) {
        fprintf(g_log_latest, "%s", msg);
        fflush(g_log_latest);
    }
    if (g_log_strat) {
        fprintf(g_log_strat, "%s", msg);
        fflush(g_log_strat);
    }
    pthread_mutex_unlock(&g_log_mutex);
}

/* --------------------------------------------------------------------------
 * High-Resolution Time Utilities
 * -------------------------------------------------------------------------- */
static double get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((double)ts.tv_sec * 1000.0) + ((double)ts.tv_nsec / 1000000.0);
}

static void sleep_ms(double ms) {
    if (ms <= 0.0) return;
    struct timespec req, rem;
    req.tv_sec = (time_t)(ms / 1000.0);
    req.tv_nsec = (long)((ms - (req.tv_sec * 1000.0)) * 1000000.0);
    while (nanosleep(&req, &rem) == -1) {
        req = rem;
    }
}

static const char *strategy_to_string(MacStrategy s) {
    switch (s) {
        case STRATEGY_CSMA_CD:        return "CSMA/CD (IEEE 802.3)";
        case STRATEGY_1_PERSISTENT:   return "1-Persistent CSMA";
        case STRATEGY_NON_PERSISTENT: return "Non-Persistent CSMA";
        case STRATEGY_P_PERSISTENT:   return "p-Persistent CSMA";
        default:                      return "Unknown";
    }
}

static const char *strategy_to_slug(MacStrategy s) {
    switch (s) {
        case STRATEGY_CSMA_CD:        return "csma_cd";
        case STRATEGY_1_PERSISTENT:   return "1_persistent";
        case STRATEGY_NON_PERSISTENT: return "non_persistent";
        case STRATEGY_P_PERSISTENT:   return "p_persistent";
        default:                      return "csma";
    }
}

static void update_channel_timing_locked(ChannelBus *b, double now_ms) {
    double delta = now_ms - b->last_state_change_ms;
    if (delta > 0) {
        if (b->state == CHAN_IDLE) {
            b->channel_idle_time_ms += delta;
        } else if (b->state == CHAN_BUSY) {
            b->channel_busy_time_ms += delta;
        } else if (b->state == CHAN_COLLISION) {
            b->channel_collision_time_ms += delta;
        }
    }
    b->last_state_change_ms = now_ms;
}

/* --------------------------------------------------------------------------
 * Backoff Algorithms
 * -------------------------------------------------------------------------- */
/* IEEE 802.3 Truncated BEB - EXCLUSIVELY for CSMA/CD */
static double calculate_beb_delay(int k, double slot_ms, unsigned int *seed) {
    if (k > BEB_TRUNCATION_LIMIT) k = BEB_TRUNCATION_LIMIT;
    int max_slots = (1 << k);
    int r = rand_r(seed) % max_slots;
    return (double)r * slot_ms;
}

/* Fixed Uniform Random Backoff (1 to 16 slots) - for Non-CD Strategies */
static double calculate_uniform_delay(double slot_ms, unsigned int *seed) {
    int r = 1 + (rand_r(seed) % 16);
    return (double)r * slot_ms;
}

/* --------------------------------------------------------------------------
 * Station Worker Thread Routine
 * Simulates an autonomous station contending for the shared broadcast channel.
 * -------------------------------------------------------------------------- */
static void *station_worker_thread(void *arg) {
    StationThreadArgs *args = (StationThreadArgs *)arg;
    ChannelBus *b = args->bus;
    int id = args->station_id;
    MacStrategy strategy = args->strategy;
    int num_frames = args->num_frames;
    double p_val = args->p_val;

    /* High-entropy per-thread seed */
    struct timeval tv;
    gettimeofday(&tv, NULL);
    unsigned int seed = (unsigned int)(tv.tv_usec ^ (id * 2654435761U));

    /* Realistic asynchronous station arrival jitter (0 to 6 ms) */
    double arrival_jitter_ms = (double)(rand_r(&seed) % 60) / 10.0;
    sleep_ms(arrival_jitter_ms);

    for (int seq = 1; seq <= num_frames && g_running; seq++) {
        double frame_start_ms = get_time_ms();
        bool delivered = false;
        int collision_attempts = 0;

        while (!delivered && collision_attempts < BEB_MAX_ATTEMPTS && g_running) {
            args->metrics.attempts++;

            /* ==============================================================
             * 1. CARRIER SENSING STAGE
             * ============================================================== */
            if (strategy == STRATEGY_NON_PERSISTENT) {
                pthread_mutex_lock(&b->lock);
                double now = get_time_ms();
                bool perceived_idle = (b->state == CHAN_IDLE) ||
                    (b->active_transmitters > 0 && (now - b->first_tx_start_ms < b->prop_delay_ms));
                float cur_v = b->voltage;
                pthread_mutex_unlock(&b->lock);

                if (!perceived_idle) {
                    args->metrics.busy_senses++;
                    double boff = calculate_uniform_delay(b->slot_time_ms, &seed);
                    args->metrics.total_backoff_ms += boff;
                    log_event(COLOR_YELLOW, "WARN", "[Station %02d] Channel BUSY (%.1fV) -> Backing off %.2f ms",
                              id, cur_v, boff);
                    sleep_ms(boff);
                    continue;
                }
            } else if (strategy == STRATEGY_1_PERSISTENT || strategy == STRATEGY_CSMA_CD) {
                pthread_mutex_lock(&b->lock);
                while (g_running) {
                    double now = get_time_ms();
                    bool perceived_idle = (b->state == CHAN_IDLE) ||
                        (b->active_transmitters > 0 && (now - b->first_tx_start_ms < b->prop_delay_ms));
                    if (perceived_idle) break;
                    args->metrics.busy_senses++;
                    pthread_cond_wait(&b->idle_cond, &b->lock);
                }
                pthread_mutex_unlock(&b->lock);
            } else if (strategy == STRATEGY_P_PERSISTENT) {
                while (g_running) {
                    pthread_mutex_lock(&b->lock);
                    while (g_running) {
                        double now = get_time_ms();
                        bool perceived_idle = (b->state == CHAN_IDLE) ||
                            (b->active_transmitters > 0 && (now - b->first_tx_start_ms < b->prop_delay_ms));
                        if (perceived_idle) break;
                        args->metrics.busy_senses++;
                        pthread_cond_wait(&b->idle_cond, &b->lock);
                    }
                    pthread_mutex_unlock(&b->lock);

                    /* Slotted transmission roll */
                    double r_val = (double)rand_r(&seed) / (double)RAND_MAX;
                    if (r_val <= p_val) {
                        break;
                    } else {
                        sleep_ms(b->slot_time_ms);
                        args->metrics.total_backoff_ms += b->slot_time_ms;
                        pthread_mutex_lock(&b->lock);
                        bool preempted = (b->state != CHAN_IDLE);
                        pthread_mutex_unlock(&b->lock);
                        if (preempted) {
                            double boff = calculate_uniform_delay(b->slot_time_ms, &seed);
                            args->metrics.total_backoff_ms += boff;
                            log_event(COLOR_YELLOW, "WARN", "[Station %02d] Preempted in slot -> Backing off %.2f ms",
                                      id, boff);
                            sleep_ms(boff);
                        }
                    }
                }
            }

            /* ==============================================================
             * 2. TRANSMISSION START & CONSTRUCTIVE VOLTAGE SUPERPOSITION
             * ============================================================== */
            pthread_mutex_lock(&b->lock);
            double now = get_time_ms();
            update_channel_timing_locked(b, now);

            b->total_tx_attempts++;
            int my_slot = b->active_transmitters++;
            b->active_station_ids[my_slot] = id;

            if (b->active_transmitters == 1) {
                b->state = CHAN_BUSY;
                b->voltage = 1.0f;
                b->collision_flag = false;
                b->first_tx_start_ms = now;
                log_event(COLOR_CYAN, "INFO", "[Station %02d] Transmitting frame #%d (attempt %d)",
                          id, seq, collision_attempts + 1);
            } else {
                /* Multiple active transmissions -> CONSTRUCTIVE VOLTAGE SUPERPOSITION */
                b->state = CHAN_COLLISION;
                b->voltage = (float)b->active_transmitters;
                b->collision_flag = true;
                b->total_collisions++;
                log_event(COLOR_RED, "COLL", "[Station %02d] Collision voltage spike: %.1fV on wire!",
                          id, b->voltage);
                pthread_cond_broadcast(&b->collision_cond);
            }
            pthread_mutex_unlock(&b->lock);

            /* ==============================================================
             * 3. TRANSMISSION WINDOW & LISTEN-WHILE-TALK PREEMPTION
             * ============================================================== */
            double tx_duration = b->frame_tx_time_ms;
            double t_tx_start = get_time_ms();
            bool collided = false;

            if (strategy == STRATEGY_CSMA_CD) {
                /* Continuous Listen-While-Talk sampling every 100 us */
                while ((get_time_ms() - t_tx_start) < tx_duration && g_running) {
                    pthread_mutex_lock(&b->lock);
                    if (b->collision_flag) {
                        collided = true;
                        pthread_mutex_unlock(&b->lock);
                        break;
                    }
                    pthread_mutex_unlock(&b->lock);
                    usleep(100);
                }
            } else {
                /* Non-CD: transmits for full frame duration before detecting collision */
                sleep_ms(tx_duration);
                pthread_mutex_lock(&b->lock);
                collided = b->collision_flag;
                pthread_mutex_unlock(&b->lock);
            }

            /* ==============================================================
             * 4. COLLISION RESOLUTION / JAMMING / BACKOFF
             * ============================================================== */
            if (collided) {
                args->metrics.collisions++;
                collision_attempts++;

                if (strategy == STRATEGY_CSMA_CD) {
                    /* Emits 32-bit Jamming signal STRICTLY in CSMA/CD */
                    pthread_mutex_lock(&b->lock);
                    b->total_jams++;
                    pthread_mutex_unlock(&b->lock);
                    sleep_ms(b->jam_duration_ms);
                }

                /* Release channel */
                pthread_mutex_lock(&b->lock);
                now = get_time_ms();
                update_channel_timing_locked(b, now);

                for (int i = 0; i < b->active_transmitters; i++) {
                    if (b->active_station_ids[i] == id) {
                        for (int j = i; j < b->active_transmitters - 1; j++) {
                            b->active_station_ids[j] = b->active_station_ids[j + 1];
                        }
                        b->active_transmitters--;
                        break;
                    }
                }

                if (b->active_transmitters == 0) {
                    b->state = CHAN_IDLE;
                    b->voltage = 0.0f;
                    b->collision_flag = false;
                    pthread_cond_broadcast(&b->idle_cond);
                } else if (b->active_transmitters == 1) {
                    b->state = CHAN_BUSY;
                    b->voltage = 1.0f;
                }
                pthread_mutex_unlock(&b->lock);

                /* Backoff calculation */
                double boff;
                if (strategy == STRATEGY_CSMA_CD) {
                    boff = calculate_beb_delay(collision_attempts, b->slot_time_ms, &seed);
                    args->metrics.total_backoff_ms += boff;
                    log_event(COLOR_MAGENTA, "JAM ", "[Station %02d] Aborted -> 32-bit JAM (0x%08X), BEB backoff %.2f ms (try %d)",
                              id, JAM_PATTERN_32BIT, boff, collision_attempts);
                } else {
                    boff = calculate_uniform_delay(b->slot_time_ms, &seed);
                    args->metrics.total_backoff_ms += boff;
                    log_event(COLOR_RED, "COLL", "[Station %02d] Collided -> Uniform random backoff %.2f ms (try %d)",
                              id, boff, collision_attempts);
                }
                sleep_ms(boff);
                continue;
            }

            /* ==============================================================
             * 5. SUCCESSFUL TRANSMISSION COMPLETE
             * ============================================================== */
            pthread_mutex_lock(&b->lock);
            now = get_time_ms();
            update_channel_timing_locked(b, now);

            b->total_successful_frames++;
            args->metrics.successes++;
            delivered = true;
            args->metrics.total_latency_ms += (now - frame_start_ms);

            for (int i = 0; i < b->active_transmitters; i++) {
                if (b->active_station_ids[i] == id) {
                    for (int j = i; j < b->active_transmitters - 1; j++) {
                        b->active_station_ids[j] = b->active_station_ids[j + 1];
                    }
                    b->active_transmitters--;
                    break;
                }
            }

            if (b->active_transmitters == 0) {
                b->state = CHAN_IDLE;
                b->voltage = 0.0f;
                b->collision_flag = false;
                pthread_cond_broadcast(&b->idle_cond);
            }
            pthread_mutex_unlock(&b->lock);

            double lat = now - frame_start_ms;
            double inst_tp_kbps = (lat > 0) ? ((FRAME_BYTE_SIZE * 8.0) / lat) : 0.0;
            log_event(COLOR_GREEN, "SUCC", "[Station %02d] Frame #%d delivered successfully! (latency: %.2f ms, throughput: %.2f kbps)",
                      id, seq, lat, inst_tp_kbps);

            /* Inter-frame spacing representing station transmission pacing */
            sleep_ms(1.0 + (double)(rand_r(&seed) % 30) / 10.0);
        }

        if (!delivered) {
            log_event(COLOR_RED, "FAIL", "[Station %02d] Frame #%d aborted after %d attempts",
                      id, seq, BEB_MAX_ATTEMPTS);
        }
    }

    return NULL;
}

typedef struct {
    MacStrategy strategy;
    int num_stations;
    int num_frames;
    double sim_duration;
    unsigned int total_tx_attempts;
    unsigned int total_successful_frames;
    unsigned int total_collisions;
    unsigned int total_jams;
    double throughput_bps;
    double efficiency;
    double delivery_rate;
} SimSummary;

/* --------------------------------------------------------------------------
 * Execute a Multi-Threaded Simulation Run with File Logging
 * -------------------------------------------------------------------------- */
static void execute_simulation(int num_stations, MacStrategy strategy, int num_frames, double p_val,
                               bool append_strat, SimSummary *out_summary) {
    mkdir("logs", 0777);

    char strat_log_path[128];
    snprintf(strat_log_path, sizeof(strat_log_path), "logs/csma_sim_%s.log", strategy_to_slug(strategy));

    /* Open log files for writing */
    pthread_mutex_lock(&g_log_mutex);
    g_log_latest = fopen("logs/csma_simulation.log", "w");
    g_log_strat  = fopen(strat_log_path, append_strat ? "a" : "w");
    pthread_mutex_unlock(&g_log_mutex);

    log_raw("\n==========================================================================\n");
    log_raw("    CONCURRENT MULTI-THREADED CSMA & CSMA/CD SIMULATOR (POSIX pthreads)  \n");
    log_raw("==========================================================================\n");
    log_raw("Contending Station Threads  : %d\n", num_stations);
    log_raw("MAC Protocol Strategy       : %s\n", strategy_to_string(strategy));
    log_raw("Frames per Station          : %d\n", num_frames);
    if (strategy == STRATEGY_P_PERSISTENT) {
        log_raw("Persistence Probability p   : %.2f (Optimal ~ 1/N)\n", p_val);
    }
    log_raw("Slot Time (2 * Tau)         : %.2f ms\n", DEFAULT_SLOT_TIME_MS);
    log_raw("Frame Transmission Time     : %.2f ms (64 Bytes)\n", DEFAULT_FRAME_TIME_MS);
    log_raw("Jamming Signal Pattern      : 32-bit (0x%08X)\n", JAM_PATTERN_32BIT);
    log_raw("Synchronization Primitives  : POSIX pthread_mutex_t & pthread_cond_t\n");
    log_raw("Detailed Execution Log File : logs/csma_simulation.log\n");
    log_raw("==========================================================================\n\n");

    ChannelBus bus;
    memset(&bus, 0, sizeof(ChannelBus));
    pthread_mutex_init(&bus.lock, NULL);
    pthread_cond_init(&bus.idle_cond, NULL);
    pthread_cond_init(&bus.collision_cond, NULL);

    bus.state = CHAN_IDLE;
    bus.voltage = 0.0f;
    bus.active_transmitters = 0;
    bus.collision_flag = false;
    bus.slot_time_ms = DEFAULT_SLOT_TIME_MS;
    bus.prop_delay_ms = DEFAULT_PROP_DELAY_MS;
    bus.frame_tx_time_ms = DEFAULT_FRAME_TIME_MS;
    bus.jam_duration_ms = DEFAULT_JAM_TIME_MS;
    bus.last_state_change_ms = get_time_ms();

    pthread_t threads[MAX_STATIONS];
    StationThreadArgs args[MAX_STATIONS];

    double sim_start = get_time_ms();

    /* Spawn all station threads simultaneously */
    for (int i = 0; i < num_stations; i++) {
        args[i].station_id = i + 1;
        args[i].strategy = strategy;
        args[i].num_frames = num_frames;
        args[i].p_val = p_val;
        args[i].bus = &bus;
        memset(&args[i].metrics, 0, sizeof(StationMetrics));
        args[i].metrics.station_id = i + 1;

        if (pthread_create(&threads[i], NULL, station_worker_thread, &args[i]) != 0) {
            fprintf(stderr, "Failed to create thread for Station %d\n", i + 1);
            return;
        }
    }

    /* Wait for all station threads to finish */
    for (int i = 0; i < num_stations; i++) {
        pthread_join(threads[i], NULL);
    }

    double sim_duration = (get_time_ms() - sim_start) / 1000.0;
    double delivery_rate = ((double)bus.total_successful_frames / (double)(num_stations * num_frames > 0 ? (num_stations * num_frames) : 1)) * 100.0;

    /* Print Per-Station Breakdown Table */
    log_raw("\n====================================================================================================\n");
    log_raw("PER-STATION THREAD PERFORMANCE BREAKDOWN\n");
    log_raw("----------------------------------------------------------------------------------------------------\n");
    log_raw("%-10s | %-7s | %-7s | %-10s | %-16s | %-14s | %-14s\n",
            "Station", "Tries", "Success", "Collisions", "Throughput (bps)", "Avg Delay (ms)", "Backoff (ms)");
    log_raw("----------------------------------------------------------------------------------------------------\n");
    for (int i = 0; i < num_stations; i++) {
        StationMetrics *m = &args[i].metrics;
        double avg_lat = (m->successes > 0) ? (m->total_latency_ms / m->successes) : 0.0;
        double stn_tp_bps = (sim_duration > 0) ? ((m->successes * FRAME_BYTE_SIZE * 8.0) / sim_duration) : 0.0;
        log_raw("Station %02d | %-7u | %-7u | %-10u | %12.2f bps | %-14.2f | %-14.2f\n",
                m->station_id, m->attempts, m->successes, m->collisions,
                stn_tp_bps, avg_lat, m->total_backoff_ms);
    }

    /* Print Global Simulation Performance Summary */
    double total_bytes = bus.total_successful_frames * FRAME_BYTE_SIZE;
    double throughput_bps = (sim_duration > 0) ? ((total_bytes * 8.0) / sim_duration) : 0.0;
    double useful_tx_time_ms = bus.total_successful_frames * bus.frame_tx_time_ms;
    double efficiency = (sim_duration > 0) ? (useful_tx_time_ms / (sim_duration * 1000.0)) : 0.0;
    if (efficiency > 1.0) efficiency = 1.0;

    log_raw("==========================================================================\n");
    log_raw("GLOBAL SIMULATION PERFORMANCE SUMMARY\n");
    log_raw("--------------------------------------------------------------------------\n");
    log_raw("Elapsed Simulation Time    : %.3f seconds\n", sim_duration);
    log_raw("Total Frame Attempts       : %u\n", bus.total_tx_attempts);
    log_raw("Total Frames Delivered     : %u\n", bus.total_successful_frames);
    log_raw("Total Collisions Detected  : %u\n", bus.total_collisions);
    log_raw("Total 32-bit Jam Signals   : %u\n", bus.total_jams);
    log_raw("Throughput Delivered       : %.2f bps (%.2f kbps)\n", throughput_bps, throughput_bps / 1000.0);
    log_raw("Channel Physical Capacity  : 64000.00 bps (64.00 kbps)\n");
    log_raw("Channel Access Efficiency  : %.2f%%\n", efficiency * 100.0);
    log_raw("Delivery Success Ratio     : %.1f%%\n", delivery_rate);
    log_raw("==========================================================================\n\n");

    /* Record Summary if requested */
    if (out_summary) {
        out_summary->strategy = strategy;
        out_summary->num_stations = num_stations;
        out_summary->num_frames = num_frames;
        out_summary->sim_duration = sim_duration;
        out_summary->total_tx_attempts = bus.total_tx_attempts;
        out_summary->total_successful_frames = bus.total_successful_frames;
        out_summary->total_collisions = bus.total_collisions;
        out_summary->total_jams = bus.total_jams;
        out_summary->throughput_bps = throughput_bps;
        out_summary->efficiency = efficiency;
        out_summary->delivery_rate = delivery_rate;
    }

    /* Destroy synchronization primitives */
    pthread_mutex_destroy(&bus.lock);
    pthread_cond_destroy(&bus.idle_cond);
    pthread_cond_destroy(&bus.collision_cond);

    /* Append live empirical benchmarks to results/data/live_c_benchmarks.csv */
    FILE *fp_csv = fopen("results/data/live_c_benchmarks.csv", "a");
    if (fp_csv) {
        fprintf(fp_csv, "%s,%d,%d,%u,%u,%u,%u,%.4f,%.2f\n",
                strategy_to_slug(strategy), num_stations, num_frames,
                bus.total_tx_attempts, bus.total_successful_frames,
                bus.total_collisions, bus.total_jams,
                efficiency, sim_duration);
        fclose(fp_csv);
    }

    pthread_mutex_lock(&g_log_mutex);
    if (g_log_latest) {
        fclose(g_log_latest);
        g_log_latest = NULL;
    }
    if (g_log_strat) {
        fclose(g_log_strat);
        g_log_strat = NULL;
    }
    pthread_mutex_unlock(&g_log_mutex);

    /* Symlink / copy for one_persistent compatibility */
    if (strategy == STRATEGY_1_PERSISTENT) {
        unlink("logs/csma_sim_one_persistent.log");
        if (link("logs/csma_sim_1_persistent.log", "logs/csma_sim_one_persistent.log") != 0) {
            /* Fallback silent ignore */
        }
    }

    printf(COLOR_GREEN "[+] Complete simulation log written to:\n" COLOR_RESET);
    printf("    • logs/csma_simulation.log (latest execution log)\n");
    printf("    • %s (dedicated protocol log)\n", strat_log_path);
}

/* --------------------------------------------------------------------------
 * Execute All 4 MAC Protocols Sequentially (Batch Simulation)
 * -------------------------------------------------------------------------- */
static void execute_all_strategies(int num_stations, int num_frames, double p_val) {
    MacStrategy strats[] = {
        STRATEGY_CSMA_CD,
        STRATEGY_1_PERSISTENT,
        STRATEGY_NON_PERSISTENT,
        STRATEGY_P_PERSISTENT
    };
    SimSummary summaries[4];

    printf("\n" COLOR_BOLD "==========================================================================\n" COLOR_RESET);
    printf(COLOR_BOLD ">>> EXECUTING ALL 4 MAC PROTOCOLS SEQUENTIALLY (N = %d, Frames = %d)\n" COLOR_RESET,
           num_stations, num_frames);
    printf("    Independent execution logs will be generated in logs/ for each protocol.\n");
    printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);

    for (int i = 0; i < 4; i++) {
        printf("\n" COLOR_CYAN ">>> [Protocol %d/4] Executing %s...\n" COLOR_RESET,
               i + 1, strategy_to_string(strats[i]));
        execute_simulation(num_stations, strats[i], num_frames, p_val, false, &summaries[i]);
    }

    /* Print Comparative Benchmark Table */
    printf("\n" COLOR_BOLD "========================================================================================================================\n" COLOR_RESET);
    printf(COLOR_BOLD "                             COMPARATIVE BENCHMARK SUMMARY (N = %d Stations, %d Frames/Station)                           \n" COLOR_RESET,
           num_stations, num_frames);
    printf(COLOR_BOLD "========================================================================================================================\n" COLOR_RESET);
    printf("%-24s | %-8s | %-8s | %-10s | %-6s | %-16s | %-12s | %-10s | %-8s\n",
           "MAC Strategy", "Attempts", "Success", "Collisions", "Jams", "Throughput (bps)", "Goodput", "Efficiency", "Success%");
    printf("------------------------------------------------------------------------------------------------------------------------\n");
    for (int i = 0; i < 4; i++) {
        printf("%-24s | %-8u | %-8u | %-10u | %-6u | %12.2f bps | %7.2f kbps | %9.2f%% | %7.1f%%\n",
               strategy_to_string(summaries[i].strategy),
               summaries[i].total_tx_attempts,
               summaries[i].total_successful_frames,
               summaries[i].total_collisions,
               summaries[i].total_jams,
               summaries[i].throughput_bps,
               summaries[i].throughput_bps / 1000.0,
               summaries[i].efficiency * 100.0,
               summaries[i].delivery_rate);
    }
    printf(COLOR_BOLD "========================================================================================================================\n" COLOR_RESET);
    printf(COLOR_GREEN "[+] All 4 protocol logs generated successfully in logs/ directory:\n" COLOR_RESET);
    printf("    • logs/csma_sim_csma_cd.log\n");
    printf("    • logs/csma_sim_1_persistent.log (and csma_sim_one_persistent.log)\n");
    printf("    • logs/csma_sim_non_persistent.log\n");
    printf("    • logs/csma_sim_p_persistent.log\n");
    printf("    • logs/csma_simulation.log (latest)\n");
}

/* --------------------------------------------------------------------------
 * Contention Sweep across Station Counts (N = 2, 4, 8, 16, 24, 32)
 * -------------------------------------------------------------------------- */
static void execute_contention_sweep(MacStrategy strategy, int num_frames, double p_val) {
    int sweep_ns[] = {2, 4, 8, 16, 24, 32};
    int count = sizeof(sweep_ns) / sizeof(sweep_ns[0]);

    printf("\n" COLOR_BOLD "==========================================================================\n" COLOR_RESET);
    printf(COLOR_BOLD ">>> Running Multi-Threaded Station Contention Sweep (%s)\n" COLOR_RESET, strategy_to_string(strategy));
    printf("    Spawning POSIX station threads across N = 2, 4, 8, 16, 24, 32\n");
    printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);

    for (int i = 0; i < count; i++) {
        int n = sweep_ns[i];
        printf("\n--------------------------------------------------------------------------\n");
        printf("[+] Launching %d contending threads (Frames/Stn: %d, Strategy: %s)...\n",
               n, num_frames, strategy_to_string(strategy));
        printf("--------------------------------------------------------------------------\n");
        execute_simulation(n, strategy, num_frames, p_val, (i > 0), NULL);
    }

    printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
    printf(COLOR_GREEN "[+] Contention sweep completed across all station thread configurations!\n" COLOR_RESET);
    printf("[+] All empirical data recorded in: results/data/live_c_benchmarks.csv\n");
    printf("[+] Log file updated: logs/csma_simulation.log\n");
    printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
}

/* --------------------------------------------------------------------------
 * Interactive Simulation Log Viewer
 * -------------------------------------------------------------------------- */
static int get_input_int(const char *prompt, int default_val, int min_val, int max_val);

static void display_log_menu(void) {
    while (1) {
        printf("\n" COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf(COLOR_BOLD "                       SIMULATION LOG VIEWER MENU                         \n" COLOR_RESET);
        printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf("1) Latest Simulation Run (logs/csma_simulation.log)\n");
        printf("2) CSMA/CD IEEE 802.3 Log (logs/csma_sim_csma_cd.log)\n");
        printf("3) 1-Persistent CSMA Log (logs/csma_sim_1_persistent.log)\n");
        printf("4) Non-Persistent CSMA Log (logs/csma_sim_non_persistent.log)\n");
        printf("5) p-Persistent CSMA Log (logs/csma_sim_p_persistent.log)\n");
        printf("6) Return to Main Menu\n");
        int sel = get_input_int("Select log to view (1-6)", 1, 1, 6);
        if (sel == 6) break;

        const char *log_file = "logs/csma_simulation.log";
        if (sel == 2) log_file = "logs/csma_sim_csma_cd.log";
        else if (sel == 3) log_file = "logs/csma_sim_1_persistent.log";
        else if (sel == 4) log_file = "logs/csma_sim_non_persistent.log";
        else if (sel == 5) log_file = "logs/csma_sim_p_persistent.log";

        FILE *fp = fopen(log_file, "r");
        if (!fp) {
            printf(COLOR_YELLOW "\n[!] Log file '%s' not found. Please run this simulation first!\n" COLOR_RESET, log_file);
            continue;
        }

        printf("\n" COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf(COLOR_BOLD "                 DISPLAYING: %s\n" COLOR_RESET, log_file);
        printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        char line[512];
        int count = 0;
        while (fgets(line, sizeof(line), fp)) {
            printf("%s", line);
            count++;
        }
        fclose(fp);
        printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf(COLOR_GREEN "[+] Total %d lines displayed from %s\n" COLOR_RESET, count, log_file);
    }
}

/* --------------------------------------------------------------------------
 * Interactive Terminal Input Helpers
 * -------------------------------------------------------------------------- */
static int get_input_int(const char *prompt, int default_val, int min_val, int max_val) {
    char buf[64];
    while (1) {
        printf("%s [Default: %d]: ", prompt, default_val);
        fflush(stdout);
        if (fgets(buf, sizeof(buf), stdin) == NULL) return default_val;
        size_t len = strlen(buf);
        if (len > 0 && buf[len - 1] == '\n') buf[len - 1] = '\0';
        if (buf[0] == '\0') return default_val;
        int val = atoi(buf);
        if (val >= min_val && val <= max_val) return val;
        printf(COLOR_RED "Invalid input. Please enter an integer between %d and %d.\n" COLOR_RESET, min_val, max_val);
    }
}

static double get_input_double(const char *prompt, double default_val, double min_val, double max_val) {
    char buf[64];
    while (1) {
        printf("%s [Default: %.2f]: ", prompt, default_val);
        fflush(stdout);
        if (fgets(buf, sizeof(buf), stdin) == NULL) return default_val;
        size_t len = strlen(buf);
        if (len > 0 && buf[len - 1] == '\n') buf[len - 1] = '\0';
        if (buf[0] == '\0') return default_val;
        double val = atof(buf);
        if (val >= min_val && val <= max_val) return val;
        printf(COLOR_RED "Invalid input. Please enter a value between %.2f and %.2f.\n" COLOR_RESET, min_val, max_val);
    }
}

static MacStrategy select_strategy(void) {
    printf("\nSelect MAC Protocol Strategy:\n");
    printf("  1) CSMA/CD (IEEE 802.3 Preemptive Collision Detection with BEB) [Default]\n");
    printf("  2) 1-Persistent CSMA\n");
    printf("  3) Non-Persistent CSMA\n");
    printf("  4) p-Persistent CSMA (Slotted Contention)\n");
    int choice = get_input_int("Enter choice (1-4)", 1, 1, 4);
    switch (choice) {
        case 2:  return STRATEGY_1_PERSISTENT;
        case 3:  return STRATEGY_NON_PERSISTENT;
        case 4:  return STRATEGY_P_PERSISTENT;
        case 1:
        default: return STRATEGY_CSMA_CD;
    }
}

/* --------------------------------------------------------------------------
 * Main Function: Pure Interactive Full Menu (Zero CLI Arguments)
 * -------------------------------------------------------------------------- */
int main(void) {
    while (1) {
        printf("\n" COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf(COLOR_BOLD "     CSE/PC/B/S/314: MULTI-THREADED CSMA & CSMA/CD SIMULATOR MENU        \n" COLOR_RESET);
        printf(COLOR_BOLD "   Jadavpur University - Department of Computer Science & Engineering    \n" COLOR_RESET);
        printf(COLOR_BOLD "==========================================================================\n" COLOR_RESET);
        printf("1) Run Multi-Threaded Simulation (Single Strategy)\n");
        printf("2) Run All 4 MAC Protocols Sequentially (Generates All Strategy Logs)\n");
        printf("3) Run Station Contention Sweep across Station Counts (N = 2 to 32)\n");
        printf("4) View Simulation Logs (Interactive Log Selection)\n");
        printf("5) Exit\n");

        int choice = get_input_int("Select option (1-5)", 1, 1, 5);

        if (choice == 1) {
            MacStrategy strat = select_strategy();
            int n_stn = get_input_int("Enter number of contending station threads (2 - 64)", 4, 2, MAX_STATIONS);
            int n_frames = get_input_int("Enter frames to transmit per station (1 - 50)", 5, 1, 50);
            double p_val = 0.25;
            if (strat == STRATEGY_P_PERSISTENT) {
                p_val = get_input_double("Enter Persistence Probability p (0.01 - 1.00)", 0.25, 0.01, 1.00);
            }
            execute_simulation(n_stn, strat, n_frames, p_val, false, NULL);
        } else if (choice == 2) {
            int n_stn = get_input_int("Enter number of contending station threads (2 - 64)", 10, 2, MAX_STATIONS);
            int n_frames = get_input_int("Enter frames to transmit per station (1 - 50)", 5, 1, 50);
            double p_val = get_input_double("Enter Persistence Probability p for p-Persistent (0.01 - 1.00)", 0.10, 0.01, 1.00);
            execute_all_strategies(n_stn, n_frames, p_val);
        } else if (choice == 3) {
            MacStrategy strat = select_strategy();
            int n_frames = get_input_int("Enter frames per station for sweep (1 - 20)", 4, 1, 20);
            double p_val = 0.25;
            if (strat == STRATEGY_P_PERSISTENT) {
                p_val = get_input_double("Enter Persistence Probability p (0.01 - 1.00)", 0.25, 0.01, 1.00);
            }
            execute_contention_sweep(strat, n_frames, p_val);
        } else if (choice == 4) {
            display_log_menu();
        } else if (choice == 5) {
            printf("\nExiting simulation menu. Goodbye!\n");
            break;
        }
    }

    return 0;
}
