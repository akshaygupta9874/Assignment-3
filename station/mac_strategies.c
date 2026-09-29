/* ==============================================================================
 * mac_strategies.c
 * Implementation of CSMA MAC Protocol Algorithms over Stream TCP Sockets
 *
 * Implements:
 * 1. Carrier Sensing Primitives over TCP
 * 2. Collision Detection ("Listen-While-Talk") over TCP
 * 3. 32-bit Jamming Signal Transmission over TCP
 * 4. Truncated Binary Exponential Backoff (IEEE 802.3)
 * 5. Non-Persistent, 1-Persistent, p-Persistent CSMA & CSMA/CD
 * ============================================================================== */

#include "mac_strategies.h"
#include "../common/logger.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* --------------------------------------------------------------------------
 * Carrier Sensing Primitives
 * -------------------------------------------------------------------------- */
bool carrier_sense(int sockfd, uint16_t station_id, ChannelState *out_state, float *out_energy) {
    ChannelMessage req;
    memset(&req, 0, sizeof(req));
    req.magic = CSMA_MAGIC;
    req.msg_type = MSG_TYPE_SENSE_REQ;
    req.station_id = station_id;
    req.sim_time_ms = current_time_ms();

    if (tcp_send_msg(sockfd, &req) <= 0) {
        if (out_state)  *out_state = CHAN_STATE_BUSY;
        if (out_energy) *out_energy = 1.0f;
        return false;
    }

    ChannelMessage resp;
    int ret = tcp_recv_msg(sockfd, &resp, 100); /* 100 ms timeout */

    if (ret > 0 && resp.magic == CSMA_MAGIC && resp.msg_type == MSG_TYPE_SENSE_RESP) {
        if (out_state)  *out_state = (ChannelState)resp.channel_state;
        if (out_energy) *out_energy = resp.energy_level;
        return (resp.channel_state == CHAN_STATE_IDLE);
    }

    if (out_state)  *out_state = CHAN_STATE_BUSY;
    if (out_energy) *out_energy = 1.0f;
    return false;
}

/* --------------------------------------------------------------------------
 * Collision Detection ("Listen-While-Talk")
 * Monitors TCP socket during frame transmission for asynchronous collision alert
 * -------------------------------------------------------------------------- */
bool detect_collision_during_tx(int sockfd, uint16_t station_id,
                                uint32_t seq, double tx_duration_ms) {
    (void)seq;
    double start_ms = current_time_ms();
    double end_ms = start_ms + tx_duration_ms;

    while (current_time_ms() < end_ms) {
        double rem_ms = end_ms - current_time_ms();
        if (rem_ms <= 0) break;
        int wait_step = (rem_ms > 2.0) ? 2 : (int)rem_ms;
        if (wait_step <= 0) wait_step = 1;

        ChannelMessage msg;
        int ret = tcp_recv_msg(sockfd, &msg, wait_step);

        if (ret > 0 && msg.magic == CSMA_MAGIC) {
            if (msg.msg_type == MSG_TYPE_TX_COLLISION && msg.station_id == station_id) {
                return true; /* Collision detected while transmitting! */
            }
        }
    }
    return false;
}

/* --------------------------------------------------------------------------
 * Jamming Signal Emission (IEEE 802.3 Standard)
 * Transmits 32-bit alternating pattern 0x55555555 over TCP to inform channel
 * -------------------------------------------------------------------------- */
void transmit_jam_signal(int sockfd, uint16_t station_id, double jam_duration_ms) {
    ChannelMessage jam_msg;
    memset(&jam_msg, 0, sizeof(jam_msg));
    jam_msg.magic = CSMA_MAGIC;
    jam_msg.msg_type = MSG_TYPE_JAM_START;
    jam_msg.station_id = station_id;
    jam_msg.data_u32 = 0x55555555; /* 32-bit jam pattern */
    jam_msg.sim_time_ms = current_time_ms();

    tcp_send_msg(sockfd, &jam_msg);
    sleep_ms(jam_duration_ms);
}

/* --------------------------------------------------------------------------
 * Backoff Algorithms
 * -------------------------------------------------------------------------- */
double calculate_beb_delay(int collision_count, double slot_time_ms) {
    int k = collision_count;
    if (k > BEB_TRUNCATION_LIMIT) {
        k = BEB_TRUNCATION_LIMIT;
    }
    int max_slots = (1 << k); /* 2^k */
    int r = rand() % max_slots;
    return (double)r * slot_time_ms;
}

double calculate_non_persistent_delay(double slot_time_ms) {
    int r = 1 + (rand() % 16);
    return (double)r * slot_time_ms;
}

bool evaluate_p_persistence(double p) {
    double r = (double)rand() / (double)RAND_MAX;
    return (r <= p);
}

/* --------------------------------------------------------------------------
 * Strategy 1: Non-Persistent CSMA over TCP
 * -------------------------------------------------------------------------- */
bool transmit_frame_non_persistent(int sockfd, const MacConfig *config,
                                  MacFrame *frame, StationMetrics *metrics) {
    int attempts = 0;
    double t_start = current_time_ms();

    while (attempts < config->max_backoff_attempts) {
        attempts++;
        metrics->attempts++;

        ChannelState state;
        float energy;

        /* Step 1: Sense medium */
        bool is_idle = carrier_sense(sockfd, config->station_id, &state, &energy);
        if (!is_idle) {
            metrics->channel_busy_senses++;
            double backoff_ms = calculate_non_persistent_delay(config->slot_time_ms);
            metrics->total_backoff_time_ms += backoff_ms;
            log_event(LOG_LVL_WARN, "Station %d [Non-P]: Channel BUSY (energy=%.1f). Backing off %.1f ms",
                      config->station_id, energy, backoff_ms);
            sleep_ms(backoff_ms);
            continue;
        }

        /* Step 2: Channel is IDLE -> transmit immediately */
        log_event(LOG_LVL_INFO, "Station %d [Non-P]: Channel IDLE. Transmitting frame seq %u (attempt %d)",
                  config->station_id, frame->seq_num, attempts);

        ChannelMessage tx_msg;
        memset(&tx_msg, 0, sizeof(tx_msg));
        tx_msg.magic = CSMA_MAGIC;
        tx_msg.msg_type = MSG_TYPE_TX_START;
        tx_msg.station_id = config->station_id;
        tx_msg.frame_seq = frame->seq_num;
        tx_msg.frame_len_bytes = sizeof(MacFrame);
        tx_msg.frame_data = *frame;
        tx_msg.sim_time_ms = current_time_ms();

        tcp_send_msg(sockfd, &tx_msg);

        /* Wait for frame transmission duration */
        sleep_ms(config->frame_tx_time_ms);

        /* Await ACK or collision response from channel */
        ChannelMessage resp;
        int ret = tcp_recv_msg(sockfd, &resp, 100);

        if (ret > 0 && resp.magic == CSMA_MAGIC && resp.msg_type == MSG_TYPE_TX_SUCCESS) {
            metrics->successes++;
            metrics->total_delay_ms += (current_time_ms() - t_start);
            log_event(LOG_LVL_SUCC, "Station %d [Non-P]: Frame seq %u ACKED successfully",
                      config->station_id, frame->seq_num);
            return true;
        } else {
            metrics->collisions++;
            double backoff_ms = calculate_non_persistent_delay(config->slot_time_ms);
            metrics->total_backoff_time_ms += backoff_ms;
            log_event(LOG_LVL_COLL, "Station %d [Non-P]: Frame seq %u COLLIDED. Backing off %.1f ms",
                      config->station_id, frame->seq_num, backoff_ms);
            sleep_ms(backoff_ms);
        }
    }

    log_event(LOG_LVL_ERROR, "Station %d [Non-P]: Frame seq %u EXCEEDED max attempts (%d)",
              config->station_id, frame->seq_num, config->max_backoff_attempts);
    return false;
}

/* --------------------------------------------------------------------------
 * Strategy 2: 1-Persistent CSMA over TCP
 * -------------------------------------------------------------------------- */
bool transmit_frame_one_persistent(int sockfd, const MacConfig *config,
                                  MacFrame *frame, StationMetrics *metrics) {
    int attempts = 0;
    double t_start = current_time_ms();

    while (attempts < config->max_backoff_attempts) {
        attempts++;
        metrics->attempts++;

        /* Step 1 & 2: Continuously sense until idle */
        while (1) {
            ChannelState state;
            float energy;
            bool is_idle = carrier_sense(sockfd, config->station_id, &state, &energy);
            if (is_idle) break;
            metrics->channel_busy_senses++;
            sleep_ms(config->slot_time_ms / 2.0);
        }

        /* Step 3: Transmit immediately (p=1.0) */
        log_event(LOG_LVL_INFO, "Station %d [1-P]: Channel IDLE. Transmitting frame seq %u (prob=1.0, attempt %d)",
                  config->station_id, frame->seq_num, attempts);

        ChannelMessage tx_msg;
        memset(&tx_msg, 0, sizeof(tx_msg));
        tx_msg.magic = CSMA_MAGIC;
        tx_msg.msg_type = MSG_TYPE_TX_START;
        tx_msg.station_id = config->station_id;
        tx_msg.frame_seq = frame->seq_num;
        tx_msg.frame_len_bytes = sizeof(MacFrame);
        tx_msg.frame_data = *frame;
        tx_msg.sim_time_ms = current_time_ms();

        tcp_send_msg(sockfd, &tx_msg);

        sleep_ms(config->frame_tx_time_ms);

        ChannelMessage resp;
        int ret = tcp_recv_msg(sockfd, &resp, 100);

        if (ret > 0 && resp.magic == CSMA_MAGIC && resp.msg_type == MSG_TYPE_TX_SUCCESS) {
            metrics->successes++;
            metrics->total_delay_ms += (current_time_ms() - t_start);
            log_event(LOG_LVL_SUCC, "Station %d [1-P]: Frame seq %u ACKED successfully",
                      config->station_id, frame->seq_num);
            return true;
        } else {
            metrics->collisions++;
            double backoff_ms = calculate_beb_delay(attempts, config->slot_time_ms);
            metrics->total_backoff_time_ms += backoff_ms;
            log_event(LOG_LVL_COLL, "Station %d [1-P]: Frame seq %u COLLIDED. Backing off %.1f ms",
                      config->station_id, frame->seq_num, backoff_ms);
            sleep_ms(backoff_ms);
        }
    }

    log_event(LOG_LVL_ERROR, "Station %d [1-P]: Frame seq %u EXCEEDED max attempts (%d)",
              config->station_id, frame->seq_num, config->max_backoff_attempts);
    return false;
}

/* --------------------------------------------------------------------------
 * Strategy 3: p-Persistent CSMA over TCP
 * -------------------------------------------------------------------------- */
bool transmit_frame_p_persistent(int sockfd, const MacConfig *config,
                                MacFrame *frame, StationMetrics *metrics) {
    int attempts = 0;
    double t_start = current_time_ms();

    while (attempts < config->max_backoff_attempts) {
        attempts++;
        metrics->attempts++;

        /* Step 1: Wait until channel becomes idle */
        while (1) {
            ChannelState state;
            float energy;
            bool is_idle = carrier_sense(sockfd, config->station_id, &state, &energy);
            if (is_idle) break;
            metrics->channel_busy_senses++;
            sleep_ms(config->slot_time_ms / 2.0);
        }

        /* Step 2: Slot-based probability roll loop */
        bool transmitted = false;
        while (!transmitted) {
            if (evaluate_p_persistence(config->p_value)) {
                transmitted = true;
            } else {
                sleep_ms(config->slot_time_ms);
                metrics->total_backoff_time_ms += config->slot_time_ms;

                ChannelState state;
                float energy;
                bool is_idle = carrier_sense(sockfd, config->station_id, &state, &energy);
                if (!is_idle) {
                    double backoff_ms = calculate_beb_delay(attempts, config->slot_time_ms);
                    metrics->total_backoff_time_ms += backoff_ms;
                    log_event(LOG_LVL_WARN, "Station %d [p-P]: Preempted in slot! Backing off %.1f ms",
                              config->station_id, backoff_ms);
                    sleep_ms(backoff_ms);
                    break;
                }
            }
        }

        if (!transmitted) continue;

        log_event(LOG_LVL_INFO, "Station %d [p-P (p=%.2f)]: Transmitting frame seq %u (attempt %d)",
                  config->station_id, config->p_value, frame->seq_num, attempts);

        ChannelMessage tx_msg;
        memset(&tx_msg, 0, sizeof(tx_msg));
        tx_msg.magic = CSMA_MAGIC;
        tx_msg.msg_type = MSG_TYPE_TX_START;
        tx_msg.station_id = config->station_id;
        tx_msg.frame_seq = frame->seq_num;
        tx_msg.frame_len_bytes = sizeof(MacFrame);
        tx_msg.frame_data = *frame;
        tx_msg.sim_time_ms = current_time_ms();

        tcp_send_msg(sockfd, &tx_msg);

        sleep_ms(config->frame_tx_time_ms);

        ChannelMessage resp;
        int ret = tcp_recv_msg(sockfd, &resp, 100);

        if (ret > 0 && resp.magic == CSMA_MAGIC && resp.msg_type == MSG_TYPE_TX_SUCCESS) {
            metrics->successes++;
            metrics->total_delay_ms += (current_time_ms() - t_start);
            log_event(LOG_LVL_SUCC, "Station %d [p-P]: Frame seq %u ACKED successfully",
                      config->station_id, frame->seq_num);
            return true;
        } else {
            metrics->collisions++;
            double backoff_ms = calculate_beb_delay(attempts, config->slot_time_ms);
            metrics->total_backoff_time_ms += backoff_ms;
            log_event(LOG_LVL_COLL, "Station %d [p-P]: Frame seq %u COLLIDED. Backing off %.1f ms",
                      config->station_id, frame->seq_num, backoff_ms);
            sleep_ms(backoff_ms);
        }
    }

    log_event(LOG_LVL_ERROR, "Station %d [p-P]: Frame seq %u EXCEEDED max attempts (%d)",
              config->station_id, frame->seq_num, config->max_backoff_attempts);
    return false;
}

/* --------------------------------------------------------------------------
 * Strategy 4: CSMA/CD over TCP
 * -------------------------------------------------------------------------- */
bool transmit_frame_csma_cd(int sockfd, const MacConfig *config,
                           MacFrame *frame, StationMetrics *metrics) {
    int K = 0; /* Collision counter */
    double t_start = current_time_ms();

    while (K < config->max_backoff_attempts) {
        metrics->attempts++;

        /* Step 2: 1-Persistent carrier sense */
        while (1) {
            ChannelState state;
            float energy;
            bool is_idle = carrier_sense(sockfd, config->station_id, &state, &energy);
            if (is_idle) break;
            metrics->channel_busy_senses++;
            sleep_ms(config->slot_time_ms / 2.0);
        }

        /* Step 3: Begin transmission */
        log_event(LOG_LVL_INFO, "Station %d [CSMA/CD]: Transmitting frame seq %u (K=%d). Monitoring wire...",
                  config->station_id, frame->seq_num, K);

        ChannelMessage tx_msg;
        memset(&tx_msg, 0, sizeof(tx_msg));
        tx_msg.magic = CSMA_MAGIC;
        tx_msg.msg_type = MSG_TYPE_TX_START;
        tx_msg.station_id = config->station_id;
        tx_msg.frame_seq = frame->seq_num;
        tx_msg.frame_len_bytes = sizeof(MacFrame);
        tx_msg.frame_data = *frame;
        tx_msg.sim_time_ms = current_time_ms();

        tcp_send_msg(sockfd, &tx_msg);

        /* Step 4: Listen-While-Talk Collision Detection */
        bool collision = detect_collision_during_tx(sockfd, config->station_id,
                                                   frame->seq_num, config->frame_tx_time_ms);

        if (collision) {
            metrics->collisions++;
            K++;

            log_event(LOG_LVL_COLL, "Station %d [CSMA/CD]: COLLISION DETECTED on seq %u! Aborting data TX (K=%d)",
                      config->station_id, frame->seq_num, K);

            /* Abort data transmission and emit 32-bit Jamming Signal */
            transmit_jam_signal(sockfd, config->station_id, 1.0);

            if (K >= config->max_backoff_attempts) {
                log_event(LOG_LVL_ERROR, "Station %d [CSMA/CD]: K=%d exceeded K_max (15). Transmission ABORTED",
                          config->station_id, K);
                return false;
            }

            double beb_delay_ms = calculate_beb_delay(K, config->slot_time_ms);
            metrics->total_backoff_time_ms += beb_delay_ms;

            log_event(LOG_LVL_WARN, "Station %d [CSMA/CD]: Backing off for %.2f ms (BEB slot count: %.0f)",
                      config->station_id, beb_delay_ms, beb_delay_ms / config->slot_time_ms);

            sleep_ms(beb_delay_ms);
            continue;
        }

        /* Step 5: Clean transmission verified */
        metrics->successes++;
        metrics->total_delay_ms += (current_time_ms() - t_start);
        log_event(LOG_LVL_SUCC, "Station %d [CSMA/CD]: Frame seq %u transmission SUCCEEDED with 0 collisions in final attempt",
                  config->station_id, frame->seq_num);
        return true;
    }

    return false;
}
