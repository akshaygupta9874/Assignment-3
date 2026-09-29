/* ==============================================================================
 * station.c
 * Contending Network Station Client Process over Stream TCP Sockets
 *
 * Emulates an independent network node attempting frame transmission
 * using carrier sensing, collision detection, and backoff algorithms.
 * ============================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

#include "../common/csma_common.h"
#include "../common/channel_wire.h"
#include "../common/logger.h"
#include "mac_strategies.h"

static volatile bool g_running = true;

static void handle_signal(int sig) {
    (void)sig;
    g_running = false;
}

static void print_usage(const char *prog) {
    printf("Usage: %s <station_id> <strategy> [server_ip] [server_port] [num_frames] [p_value]\n", prog);
    printf("Strategies:\n");
    printf("  non_persistent | 1\n");
    printf("  one_persistent | 2\n");
    printf("  p_persistent   | 3  (requires p_value, e.g. 0.25)\n");
    printf("  csma_cd        | 4  (Carrier Sense Multiple Access with Collision Detection)\n");
    printf("Example:\n");
    printf("  %s 1 csma_cd 127.0.0.1 9099 20\n", prog);
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        print_usage(argv[0]);
        return 1;
    }

    uint16_t station_id = (uint16_t)atoi(argv[1]);
    MacStrategy strategy = parse_mac_strategy(argv[2]);

    const char *server_ip = (argc >= 4) ? argv[3] : DEFAULT_SERVER_IP;
    int server_port = (argc >= 5) ? atoi(argv[4]) : DEFAULT_CHANNEL_PORT;
    int num_frames = (argc >= 6) ? atoi(argv[5]) : 10;
    double p_value = (argc >= 7) ? atof(argv[6]) : 0.25;

    /* Initialize PRNG with unique seed per station */
    srand((unsigned int)(time(NULL) ^ (getpid() << 8) ^ station_id));

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    char logfile[128];
    snprintf(logfile, sizeof(logfile), "logs/station_%d.log", station_id);
    char prefix[32];
    snprintf(prefix, sizeof(prefix), "STATION_%d", station_id);
    logger_init(logfile, prefix);

    log_event(LOG_LVL_INFO, "Station %d connecting to Channel Server over TCP (%s:%d)...",
              station_id, server_ip, server_port);

    int sockfd = tcp_client_connect(server_ip, server_port);
    if (sockfd < 0) {
        log_event(LOG_LVL_ERROR, "Failed to connect to Channel Server at %s:%d via TCP", server_ip, server_port);
        logger_close();
        return 1;
    }

    log_event(LOG_LVL_INFO, "TCP connection established (socket fd: %d). Registering station ID %d...",
              sockfd, station_id);

    /* Register station with channel server over TCP */
    ChannelMessage reg_msg;
    memset(&reg_msg, 0, sizeof(reg_msg));
    reg_msg.magic = CSMA_MAGIC;
    reg_msg.msg_type = MSG_TYPE_REGISTER;
    reg_msg.station_id = station_id;
    reg_msg.sim_time_ms = current_time_ms();

    if (tcp_send_msg(sockfd, &reg_msg) <= 0) {
        log_event(LOG_LVL_ERROR, "Failed to transmit registration packet over TCP");
        close(sockfd);
        logger_close();
        return 1;
    }

    ChannelMessage reg_ack;
    int ret = tcp_recv_msg(sockfd, &reg_ack, 2000);
    if (ret <= 0 || reg_ack.msg_type != MSG_TYPE_REGISTER_ACK) {
        log_event(LOG_LVL_ERROR, "Failed to receive registration ACK from channel server. Is channel_server running?");
        close(sockfd);
        logger_close();
        return 1;
    }
    log_event(LOG_LVL_INFO, "Registration confirmed by channel server. MAC Strategy: %s, Frames: %d",
              mac_strategy_to_string(strategy), num_frames);

    MacConfig config;
    config.station_id = station_id;
    config.strategy = strategy;
    config.p_value = p_value;
    config.slot_time_ms = 4.0;
    config.frame_tx_time_ms = 8.0; /* 8 ms per frame transmission */
    config.max_backoff_attempts = BEB_MAX_ATTEMPTS;

    StationMetrics metrics;
    memset(&metrics, 0, sizeof(metrics));

    double batch_start_time = current_time_ms();

    for (int seq = 1; seq <= num_frames && g_running; seq++) {
        char payload_text[DEFAULT_PAYLOAD_SIZE];
        snprintf(payload_text, sizeof(payload_text),
                 "DATA_PAYLOAD_STATION_%02d_FRAME_%04d", station_id, seq);

        MacFrame frame;
        create_mac_frame(&frame, (uint8_t)station_id, (uint8_t)(seq % 256),
                         (const uint8_t *)payload_text, (uint16_t)strlen(payload_text));

        bool success = false;
        switch (strategy) {
            case STRATEGY_NON_PERSISTENT:
                success = transmit_frame_non_persistent(sockfd, &config, &frame, &metrics);
                break;
            case STRATEGY_ONE_PERSISTENT:
                success = transmit_frame_one_persistent(sockfd, &config, &frame, &metrics);
                break;
            case STRATEGY_P_PERSISTENT:
                success = transmit_frame_p_persistent(sockfd, &config, &frame, &metrics);
                break;
            case STRATEGY_CSMA_CD:
            case STRATEGY_CSMA_CA:
            default:
                success = transmit_frame_csma_cd(sockfd, &config, &frame, &metrics);
                break;
        }

        if (!success) {
            log_event(LOG_LVL_WARN, "Station %d failed to deliver frame seq %d after maximum attempts",
                      station_id, seq);
        }

        /* Brief inter-packet spacing */
        sleep_ms(2.0 + (rand() % 5));
    }

    double batch_duration_ms = current_time_ms() - batch_start_time;

    /* Unregister cleanly */
    ChannelMessage unreg_msg;
    memset(&unreg_msg, 0, sizeof(unreg_msg));
    unreg_msg.magic = CSMA_MAGIC;
    unreg_msg.msg_type = MSG_TYPE_UNREGISTER;
    unreg_msg.station_id = station_id;
    tcp_send_msg(sockfd, &unreg_msg);

    log_event(LOG_LVL_INFO, "=========================================================");
    log_event(LOG_LVL_INFO, "STATION %d RUN SUMMARY (%s over TCP)", station_id, mac_strategy_to_string(strategy));
    log_event(LOG_LVL_INFO, "Frames Attempted    : %d", num_frames);
    log_event(LOG_LVL_INFO, "Frames Successful   : %u (%.1f%%)",
              metrics.successes, (metrics.successes * 100.0) / (num_frames > 0 ? num_frames : 1));
    log_event(LOG_LVL_INFO, "Total Contention Collisions : %u", metrics.collisions);
    log_event(LOG_LVL_INFO, "Channel Busy Senses : %u", metrics.channel_busy_senses);
    log_event(LOG_LVL_INFO, "Average Frame Delay : %.2f ms",
              metrics.successes > 0 ? (metrics.total_delay_ms / metrics.successes) : 0.0);
    log_event(LOG_LVL_INFO, "Total Backoff Time  : %.2f ms", metrics.total_backoff_time_ms);
    log_event(LOG_LVL_INFO, "Total Elapsed Time  : %.2f ms", batch_duration_ms);
    log_event(LOG_LVL_INFO, "=========================================================");

    close(sockfd);
    logger_close();
    return 0;
}
