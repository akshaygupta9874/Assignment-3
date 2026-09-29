/* ==============================================================================
 * channel_server.c
 * Emulated Shared Channel & Frame Receiver Process over TCP Sockets
 *
 * Implements:
 * 1. Physical shared medium emulation maintaining state (IDLE, BUSY, COLLISION)
 * 2. Real-time Energy Level tracking (0.0=Idle, 1.0=Normal Busy, 2.0+=Collision)
 * 3. Bus propagation delay & vulnerable interval simulation
 * 4. Jamming signal broadcast & handling for CSMA/CD
 * 5. Destination receiver sink with IEEE 802.3 CRC-32 verification
 * 6. Global throughput, collision count, delay, and efficiency metrics
 * 7. Non-blocking multi-client TCP multiplexing with exact stream framing
 * ============================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/select.h>
#include <sys/time.h>

#include "../common/csma_common.h"
#include "../common/channel_wire.h"
#include "../common/logger.h"

#define MAX_STATIONS 64

typedef struct {
    int      fd;
    uint16_t station_id;
    bool     active;
    uint32_t frames_sent;
    uint32_t frames_success;
    uint32_t collisions;
} ConnectedClient;

typedef struct {
    int      client_fd;
    uint16_t station_id;
    uint32_t frame_seq;
    double   start_time_ms;
    double   duration_ms;
    MacFrame frame;
} ActiveTransmission;

/* Channel Server State */
static volatile bool g_running = true;
static int g_listen_fd = -1;
static ChannelState g_channel_state = CHAN_STATE_IDLE;
static float g_energy_level = 0.0f;

/* Timing parameters (configurable via CLI) */
static double g_prop_delay_ms = 2.0;    /* One-way propagation delay Tau */
static double g_slot_time_ms = 4.0;     /* Slot time >= 2 * Tau */
static double g_jam_duration_ms = 1.0;  /* Jamming signal duration */

/* Connected TCP Clients */
static ConnectedClient g_clients[MAX_STATIONS];

/* Active transmissions on the wire */
static ActiveTransmission g_active_txs[MAX_STATIONS];
static int g_num_active_txs = 0;

/* Statistics */
static ChannelGlobalStats g_stats;
static double g_sim_start_time_ms = 0.0;
static double g_last_state_change_ms = 0.0;

static void handle_signal(int sig) {
    (void)sig;
    g_running = false;
}

static void close_client(int idx) {
    if (idx >= 0 && idx < MAX_STATIONS && g_clients[idx].active) {
        log_event(LOG_LVL_INFO, "Station %d (socket fd %d) disconnected",
                  g_clients[idx].station_id, g_clients[idx].fd);
        close(g_clients[idx].fd);
        g_clients[idx].fd = -1;
        g_clients[idx].active = false;
        g_clients[idx].station_id = 0;
    }
}

static void update_channel_state_timing(double now_ms) {
    double delta = now_ms - g_last_state_change_ms;
    if (delta > 0) {
        if (g_channel_state == CHAN_STATE_IDLE) {
            g_stats.channel_idle_time_ms += delta;
        } else if (g_channel_state == CHAN_STATE_BUSY) {
            g_stats.channel_busy_time_ms += delta;
        } else if (g_channel_state == CHAN_STATE_COLLISION) {
            g_stats.channel_collision_time_ms += delta;
        }
    }
    g_last_state_change_ms = now_ms;
}

static void evaluate_channel_state(double now_ms) {
    update_channel_state_timing(now_ms);

    if (g_num_active_txs == 0) {
        g_channel_state = CHAN_STATE_IDLE;
        g_energy_level = 0.0f;
    } else if (g_num_active_txs == 1) {
        g_channel_state = CHAN_STATE_BUSY;
        g_energy_level = 1.0f;
    } else {
        g_channel_state = CHAN_STATE_COLLISION;
        g_energy_level = (float)g_num_active_txs; /* Constructive superposition of voltages! */
    }
}

static void notify_collision_to_active_transmitters(void) {
    ChannelMessage coll_msg;
    memset(&coll_msg, 0, sizeof(coll_msg));
    coll_msg.magic = CSMA_MAGIC;
    coll_msg.msg_type = MSG_TYPE_TX_COLLISION;
    coll_msg.channel_state = CHAN_STATE_COLLISION;
    coll_msg.energy_level = g_energy_level;
    coll_msg.sim_time_ms = current_time_ms();

    for (int i = 0; i < g_num_active_txs; i++) {
        coll_msg.station_id = g_active_txs[i].station_id;
        coll_msg.frame_seq = g_active_txs[i].frame_seq;
        tcp_send_msg(g_active_txs[i].client_fd, &coll_msg);
        log_event(LOG_LVL_COLL, "Channel notified Station %d of COLLISION on frame seq %u (energy=%.1f)",
                  g_active_txs[i].station_id, g_active_txs[i].frame_seq, g_energy_level);
    }
}

int main(int argc, char *argv[]) {
    int port = DEFAULT_CHANNEL_PORT;
    if (argc >= 2) port = atoi(argv[1]);
    if (argc >= 3) g_prop_delay_ms = atof(argv[2]);
    if (argc >= 4) g_slot_time_ms = atof(argv[3]);

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    char logfile[128];
    snprintf(logfile, sizeof(logfile), "logs/channel_server.log");
    logger_init(logfile, "CHANNEL");

    g_listen_fd = tcp_server_listen(port);
    if (g_listen_fd < 0) {
        log_event(LOG_LVL_ERROR, "Failed to bind Channel Server on TCP port %d", port);
        return 1;
    }

    g_sim_start_time_ms = current_time_ms();
    g_last_state_change_ms = g_sim_start_time_ms;
    memset(&g_stats, 0, sizeof(g_stats));
    for (int i = 0; i < MAX_STATIONS; i++) {
        g_clients[i].fd = -1;
        g_clients[i].active = false;
    }

    log_event(LOG_LVL_INFO, "=========================================================");
    log_event(LOG_LVL_INFO, "CSMA Emulated Shared Channel Server listening on TCP port %d", port);
    log_event(LOG_LVL_INFO, "Parameters: Prop Delay Tau = %.2f ms, Slot Time = %.2f ms",
              g_prop_delay_ms, g_slot_time_ms);
    log_event(LOG_LVL_INFO, "Initial Channel State: IDLE, Energy Level: 0.0V");
    log_event(LOG_LVL_INFO, "=========================================================");

    ChannelMessage rx_msg;

    while (g_running) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(g_listen_fd, &readfds);
        int max_fd = g_listen_fd;

        for (int i = 0; i < MAX_STATIONS; i++) {
            if (g_clients[i].active && g_clients[i].fd >= 0) {
                FD_SET(g_clients[i].fd, &readfds);
                if (g_clients[i].fd > max_fd) max_fd = g_clients[i].fd;
            }
        }

        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 1000; /* 1 ms poll for channel physics */

        int ready = select(max_fd + 1, &readfds, NULL, NULL, &tv);
        double now = current_time_ms();

        /* 1. Process active transmissions ending naturally on the wire */
        for (int i = 0; i < g_num_active_txs; ) {
            if (now >= g_active_txs[i].start_time_ms + g_active_txs[i].duration_ms) {
                uint16_t st_id = g_active_txs[i].station_id;
                uint32_t seq = g_active_txs[i].frame_seq;
                int client_fd = g_active_txs[i].client_fd;

                if (g_channel_state == CHAN_STATE_COLLISION || g_num_active_txs > 1) {
                    log_event(LOG_LVL_COLL, "Frame seq %u from Station %d finished with COLLISION (destroyed on wire)",
                              seq, st_id);
                } else {
                    g_stats.total_successful_frames++;
                    g_stats.total_bytes_transmitted += sizeof(MacFrame);

                    for (int k = 0; k < MAX_STATIONS; k++) {
                        if (g_clients[k].active && g_clients[k].station_id == st_id) {
                            g_clients[k].frames_success++;
                            break;
                        }
                    }

                    bool crc_valid = verify_crc32((const uint8_t *)&g_active_txs[i].frame,
                                                  sizeof(MacFrame) - sizeof(uint32_t),
                                                  g_active_txs[i].frame.fcs);

                    log_event(LOG_LVL_SUCC, "Frame seq %u from Station %d DELIVERED intact (CRC: %s, Length: %u B)",
                              seq, st_id, crc_valid ? "VALID" : "CORRUPT", g_active_txs[i].frame.length);

                    /* Send ACK to station over TCP */
                    ChannelMessage ack_msg;
                    memset(&ack_msg, 0, sizeof(ack_msg));
                    ack_msg.magic = CSMA_MAGIC;
                    ack_msg.msg_type = MSG_TYPE_TX_SUCCESS;
                    ack_msg.station_id = st_id;
                    ack_msg.frame_seq = seq;
                    ack_msg.channel_state = CHAN_STATE_IDLE;
                    ack_msg.energy_level = 0.0f;
                    ack_msg.sim_time_ms = now;
                    tcp_send_msg(client_fd, &ack_msg);
                }

                /* Remove active transmission */
                for (int j = i; j < g_num_active_txs - 1; j++) {
                    g_active_txs[j] = g_active_txs[j + 1];
                }
                g_num_active_txs--;
                evaluate_channel_state(now);
            } else {
                i++;
            }
        }

        if (ready <= 0) continue;

        /* 2. Accept incoming TCP connection requests */
        if (FD_ISSET(g_listen_fd, &readfds)) {
            struct sockaddr_in cli_addr;
            socklen_t cli_len = sizeof(cli_addr);
            int new_fd = accept(g_listen_fd, (struct sockaddr *)&cli_addr, &cli_len);
            if (new_fd >= 0) {
                set_socket_nodelay(new_fd);
                int slot = -1;
                for (int i = 0; i < MAX_STATIONS; i++) {
                    if (!g_clients[i].active) {
                        slot = i;
                        break;
                    }
                }
                if (slot >= 0) {
                    g_clients[slot].fd = new_fd;
                    g_clients[slot].station_id = 0;
                    g_clients[slot].active = true;
                    g_clients[slot].frames_sent = 0;
                    g_clients[slot].frames_success = 0;
                    g_clients[slot].collisions = 0;
                    log_event(LOG_LVL_INFO, "Accepted new TCP connection from %s:%d (fd %d, client slot %d)",
                              inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), new_fd, slot);
                } else {
                    log_event(LOG_LVL_WARN, "Maximum client capacity reached; rejecting connection");
                    close(new_fd);
                }
            }
        }

        /* 3. Process incoming messages from connected station clients */
        for (int i = 0; i < MAX_STATIONS; i++) {
            if (!g_clients[i].active || g_clients[i].fd < 0) continue;

            if (FD_ISSET(g_clients[i].fd, &readfds)) {
                int ret = tcp_recv_msg(g_clients[i].fd, &rx_msg, 0);
                if (ret <= 0) {
                    /* Station disconnected */
                    close_client(i);
                    continue;
                }

                if (rx_msg.magic != CSMA_MAGIC) continue;

                switch (rx_msg.msg_type) {
                    case MSG_TYPE_REGISTER: {
                        g_clients[i].station_id = rx_msg.station_id;
                        log_event(LOG_LVL_INFO, "Station %d registered on TCP socket fd %d",
                                  rx_msg.station_id, g_clients[i].fd);

                        ChannelMessage ack;
                        memset(&ack, 0, sizeof(ack));
                        ack.magic = CSMA_MAGIC;
                        ack.msg_type = MSG_TYPE_REGISTER_ACK;
                        ack.station_id = rx_msg.station_id;
                        ack.sim_time_ms = now;
                        tcp_send_msg(g_clients[i].fd, &ack);
                        break;
                    }

                    case MSG_TYPE_SENSE_REQ: {
                        ChannelMessage resp;
                        memset(&resp, 0, sizeof(resp));
                        resp.magic = CSMA_MAGIC;
                        resp.msg_type = MSG_TYPE_SENSE_RESP;
                        resp.station_id = rx_msg.station_id;

                        bool perceived_idle = (g_num_active_txs == 0);
                        if (g_num_active_txs > 0) {
                            double elapsed_since_first_tx = now - g_active_txs[0].start_time_ms;
                            if (elapsed_since_first_tx < g_prop_delay_ms) {
                                perceived_idle = true; /* Vulnerable propagation window! */
                            }
                        }

                        resp.channel_state = perceived_idle ? CHAN_STATE_IDLE : g_channel_state;
                        resp.energy_level = perceived_idle ? 0.0f : g_energy_level;
                        resp.sim_time_ms = now;
                        tcp_send_msg(g_clients[i].fd, &resp);
                        break;
                    }

                    case MSG_TYPE_TX_START: {
                        g_stats.total_transmissions_attempted++;
                        g_clients[i].frames_sent++;

                        if (g_num_active_txs < MAX_STATIONS) {
                            ActiveTransmission *at = &g_active_txs[g_num_active_txs++];
                            at->client_fd = g_clients[i].fd;
                            at->station_id = rx_msg.station_id;
                            at->frame_seq = rx_msg.frame_seq;
                            at->start_time_ms = now;
                            at->duration_ms = (rx_msg.frame_len_bytes > 0) ?
                                              (rx_msg.frame_len_bytes * 0.1) : 10.0;
                            at->frame = rx_msg.frame_data;
                        }

                        evaluate_channel_state(now);

                        if (g_channel_state == CHAN_STATE_COLLISION) {
                            g_stats.total_collisions++;
                            g_clients[i].collisions++;
                            log_event(LOG_LVL_COLL, ">>> COLLISION DETECTED! Active Transmitters: %d, Energy: %.1fV",
                                      g_num_active_txs, g_energy_level);
                            notify_collision_to_active_transmitters();
                        } else {
                            log_event(LOG_LVL_INFO, "Station %d started TX frame seq %u (dur=%.1f ms). Channel -> BUSY",
                                      rx_msg.station_id, rx_msg.frame_seq,
                                      g_active_txs[g_num_active_txs-1].duration_ms);
                        }
                        break;
                    }

                    case MSG_TYPE_JAM_START: {
                        g_stats.total_jam_signals++;
                        log_event(LOG_LVL_WARN, "Station %d emitting 32-bit JAMMING signal on medium",
                                  rx_msg.station_id);

                        /* Abort this station's active transmission */
                        for (int k = 0; k < g_num_active_txs; k++) {
                            if (g_active_txs[k].station_id == rx_msg.station_id) {
                                for (int j = k; j < g_num_active_txs - 1; j++) {
                                    g_active_txs[j] = g_active_txs[j + 1];
                                }
                                g_num_active_txs--;
                                break;
                            }
                        }
                        sleep_ms(g_jam_duration_ms);
                        evaluate_channel_state(now);
                        break;
                    }

                    case MSG_TYPE_GET_STATS: {
                        update_channel_state_timing(now);
                        g_stats.total_simulated_time_ms = now - g_sim_start_time_ms;
                        if (g_stats.total_simulated_time_ms > 0) {
                            g_stats.throughput_bps = (g_stats.total_bytes_transmitted * 8.0) /
                                                     (g_stats.total_simulated_time_ms / 1000.0);
                            g_stats.channel_efficiency = g_stats.channel_busy_time_ms /
                                                         (g_stats.total_simulated_time_ms + 1e-6);
                        }

                        ChannelMessage s_resp;
                        memset(&s_resp, 0, sizeof(s_resp));
                        s_resp.magic = CSMA_MAGIC;
                        s_resp.msg_type = MSG_TYPE_STATS_RESP;
                        s_resp.sim_time_ms = now;
                        memcpy(&s_resp.stats_data, &g_stats, sizeof(ChannelGlobalStats));
                        tcp_send_msg(g_clients[i].fd, &s_resp);
                        break;
                    }

                    case MSG_TYPE_RESET_STATS: {
                        log_event(LOG_LVL_INFO, "Resetting channel stats for fresh benchmark run");
                        memset(&g_stats, 0, sizeof(g_stats));
                        g_sim_start_time_ms = current_time_ms();
                        g_last_state_change_ms = g_sim_start_time_ms;
                        g_num_active_txs = 0;
                        g_channel_state = CHAN_STATE_IDLE;
                        g_energy_level = 0.0f;
                        break;
                    }

                    case MSG_TYPE_UNREGISTER: {
                        log_event(LOG_LVL_INFO, "Station %d requested unregistration", rx_msg.station_id);
                        close_client(i);
                        break;
                    }

                    default:
                        break;
                }
            }
        }
    }

    double now = current_time_ms();
    update_channel_state_timing(now);
    g_stats.total_simulated_time_ms = now - g_sim_start_time_ms;

    log_event(LOG_LVL_INFO, "=========================================================");
    log_event(LOG_LVL_INFO, "CHANNEL SERVER SHUTTING DOWN - FINAL METRICS SUMMARY (TCP)");
    log_event(LOG_LVL_INFO, "Total Transmission Attempts : %u", g_stats.total_transmissions_attempted);
    log_event(LOG_LVL_INFO, "Total Successful Deliveries : %u", g_stats.total_successful_frames);
    log_event(LOG_LVL_INFO, "Total Collisions            : %u", g_stats.total_collisions);
    log_event(LOG_LVL_INFO, "Total Jam Signals Handled   : %u", g_stats.total_jam_signals);
    log_event(LOG_LVL_INFO, "Total Simulation Time       : %.2f ms", g_stats.total_simulated_time_ms);
    log_event(LOG_LVL_INFO, "Channel Idle Time           : %.2f ms (%.1f%%)",
              g_stats.channel_idle_time_ms,
              (g_stats.channel_idle_time_ms / (g_stats.total_simulated_time_ms + 1e-6)) * 100.0);
    log_event(LOG_LVL_INFO, "Channel Busy (Useful) Time  : %.2f ms (%.1f%%)",
              g_stats.channel_busy_time_ms,
              (g_stats.channel_busy_time_ms / (g_stats.total_simulated_time_ms + 1e-6)) * 100.0);
    log_event(LOG_LVL_INFO, "Channel Collision Time      : %.2f ms (%.1f%%)",
              g_stats.channel_collision_time_ms,
              (g_stats.channel_collision_time_ms / (g_stats.total_simulated_time_ms + 1e-6)) * 100.0);
    log_event(LOG_LVL_INFO, "Channel Efficiency (S)      : %.4f",
              g_stats.channel_busy_time_ms / (g_stats.total_simulated_time_ms + 1e-6));
    log_event(LOG_LVL_INFO, "=========================================================");

    for (int i = 0; i < MAX_STATIONS; i++) {
        if (g_clients[i].active && g_clients[i].fd >= 0) {
            close(g_clients[i].fd);
        }
    }
    if (g_listen_fd >= 0) {
        close(g_listen_fd);
    }
    logger_close();
    return 0;
}
