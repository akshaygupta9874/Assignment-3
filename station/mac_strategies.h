/* ==============================================================================
 * mac_strategies.h
 * Header for CSMA MAC Strategies over TCP Sockets
 * ============================================================================== */

#ifndef MAC_STRATEGIES_H
#define MAC_STRATEGIES_H

#include "../common/csma_common.h"
#include "../common/channel_wire.h"

typedef struct {
    uint16_t station_id;
    MacStrategy strategy;
    double p_value;             /* For p-persistent CSMA */
    double slot_time_ms;        /* Slot duration >= 2 * Tau */
    double frame_tx_time_ms;    /* Transmission duration for standard frame */
    int max_backoff_attempts;   /* Max retries (16 for BEB) */
} MacConfig;

typedef struct {
    uint32_t attempts;
    uint32_t successes;
    uint32_t collisions;
    uint32_t channel_busy_senses;
    double total_backoff_time_ms;
    double total_delay_ms;
} StationMetrics;

/* Primitives for Carrier Sensing & Collision Detection over TCP */
bool carrier_sense(int sockfd, uint16_t station_id, ChannelState *out_state, float *out_energy);

bool detect_collision_during_tx(int sockfd, uint16_t station_id,
                                uint32_t seq, double tx_duration_ms);

void transmit_jam_signal(int sockfd, uint16_t station_id, double jam_duration_ms);

/* Backoff Algorithms */
double calculate_beb_delay(int collision_count, double slot_time_ms);
double calculate_non_persistent_delay(double slot_time_ms);
bool   evaluate_p_persistence(double p);

/* Core Transmission Protocol Drivers over TCP */
bool transmit_frame_non_persistent(int sockfd, const MacConfig *config,
                                  MacFrame *frame, StationMetrics *metrics);

bool transmit_frame_one_persistent(int sockfd, const MacConfig *config,
                                  MacFrame *frame, StationMetrics *metrics);

bool transmit_frame_p_persistent(int sockfd, const MacConfig *config,
                                MacFrame *frame, StationMetrics *metrics);

bool transmit_frame_csma_cd(int sockfd, const MacConfig *config,
                           MacFrame *frame, StationMetrics *metrics);

#endif /* MAC_STRATEGIES_H */
