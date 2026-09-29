/* ==============================================================================
 * csma_common.h
 * CSE/PC/B/S/314 Computer Networks Lab - Assignment 3
 * MAC Protocol Simulation: CSMA (Non-Persistent, 1-Persistent, p-Persistent, CSMA/CD)
 *
 * Implements IEEE 802.3 MAC architecture, shared physical channel emulation,
 * carrier sensing, collision detection, jamming signals, and backoff algorithms.
 * ============================================================================== */

#ifndef CSMA_COMMON_H
#define CSMA_COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/select.h>

#ifdef __cplusplus
extern "C" {
#endif

/* --------------------------------------------------------------------------
 * Physical & MAC Layer Timing Constants (IEEE 802.3 Standard Alignment)
 * -------------------------------------------------------------------------- */
#define DEFAULT_CHANNEL_PORT    9099
#define DEFAULT_SERVER_IP       "127.0.0.1"

#define MAC_ADDR_LEN            6
#define DEFAULT_PAYLOAD_SIZE    46      /* Minimum Ethernet data payload (46 bytes) */
#define MIN_FRAME_SIZE          64      /* 64 bytes standard Ethernet minimum frame */
#define MAX_PAYLOAD_SIZE        1500    /* 1500 bytes MTU */
#define JAM_SIGNAL_SIZE         4       /* 32-bit jamming pattern (0x55555555) */

/* Maximum Backoff Parameters (IEEE 802.3 Binary Exponential Backoff) */
#define BEB_MAX_ATTEMPTS        16      /* K_max = 15; abort at 16th collision */
#define BEB_TRUNCATION_LIMIT    10      /* Max exponent window: 2^10 = 1024 slots */

/* Protocol Identifier */
typedef enum {
    STRATEGY_NON_PERSISTENT  = 1,
    STRATEGY_ONE_PERSISTENT  = 2,
    STRATEGY_P_PERSISTENT    = 3,
    STRATEGY_CSMA_CD         = 4,
    STRATEGY_CSMA_CA         = 5
} MacStrategy;

/* Shared Medium Channel States */
typedef enum {
    CHAN_STATE_IDLE      = 0,   /* Energy = 0.0, medium is idle */
    CHAN_STATE_BUSY      = 1,   /* Energy = 1.0, exactly 1 active transmission */
    CHAN_STATE_COLLISION = 2    /* Energy >= 2.0, collision detected on wire */
} ChannelState;

/* IPC Control Message Codes */
typedef enum {
    MSG_TYPE_REGISTER       = 101,  /* Station joins network */
    MSG_TYPE_REGISTER_ACK   = 102,  /* Server confirms station registration */
    MSG_TYPE_SENSE_REQ      = 103,  /* Station samples channel energy / carrier */
    MSG_TYPE_SENSE_RESP     = 104,  /* Server responds with channel state & energy */
    MSG_TYPE_TX_START       = 105,  /* Station begins transmitting frame */
    MSG_TYPE_TX_COLLISION   = 106,  /* Channel notifies station of collision */
    MSG_TYPE_JAM_START      = 107,  /* Station emits jamming signal */
    MSG_TYPE_JAM_END        = 108,  /* Jamming signal completed */
    MSG_TYPE_TX_FINISH      = 109,  /* Station finished transmitting whole frame */
    MSG_TYPE_TX_SUCCESS     = 110,  /* Frame received without collision */
    MSG_TYPE_GET_STATS      = 111,  /* Query global channel metrics */
    MSG_TYPE_STATS_RESP     = 112,  /* Return channel metrics */
    MSG_TYPE_RESET_STATS    = 113,  /* Reset channel state */
    MSG_TYPE_UNREGISTER     = 114   /* Station disconnects */
} MsgType;

/* --------------------------------------------------------------------------
 * Frame Formats: IEEE 802.3 Data Frame & Control Messages
 * -------------------------------------------------------------------------- */
#pragma pack(push, 1)

/* Standard MAC Frame matching Assignment 2 & IEEE 802.3 */
typedef struct {
    uint8_t   dst_mac[MAC_ADDR_LEN];    /* Destination MAC (6 bytes) */
    uint8_t   src_mac[MAC_ADDR_LEN];    /* Source MAC (6 bytes) */
    uint16_t  length;                   /* Payload Length (2 bytes) */
    uint8_t   seq_num;                  /* Sequence Number (1 byte) */
    uint8_t   station_id;               /* Logical Station ID (1 byte) */
    uint8_t   payload[DEFAULT_PAYLOAD_SIZE]; /* 46-byte Data Payload */
    uint32_t  fcs;                      /* CRC-32 Trailer (4 bytes) */
} MacFrame;

/* Channel Summary Statistics Structure */
typedef struct {
    uint32_t total_transmissions_attempted;
    uint32_t total_successful_frames;
    uint32_t total_collisions;
    uint32_t total_jam_signals;
    double   total_simulated_time_ms;
    double   channel_busy_time_ms;
    double   channel_collision_time_ms;
    double   channel_idle_time_ms;
    double   total_bytes_transmitted;
    double   throughput_bps;
    double   channel_efficiency;
} ChannelGlobalStats;

/* Control message transferred over TCP stream socket (fixed-size framing) */
typedef struct {
    uint32_t  magic;            /* Protocol Magic: 0x8023C5AA */
    uint16_t  msg_type;         /* MsgType enum */
    uint16_t  station_id;       /* Originating station ID */
    uint32_t  frame_seq;        /* Frame sequence number */
    uint32_t  frame_len_bytes;  /* Size of transmitted frame */
    uint8_t   channel_state;    /* ChannelState enum */
    float     energy_level;     /* 0.0 (idle), 1.0 (busy), 2.0+ (collision) */
    double    sim_time_ms;      /* Simulation timestamp */
    uint32_t  data_u32;         /* Auxiliary data / error count */
    union {
        MacFrame           frame_data;
        ChannelGlobalStats stats_data;
        uint8_t            raw[128];
    } body;
} ChannelMessage;

#define frame_data body.frame_data
#define stats_data body.stats_data

#define CSMA_MAGIC 0x8023C5AAu

#pragma pack(pop)

/* --------------------------------------------------------------------------
 * Function Prototypes
 * -------------------------------------------------------------------------- */

/* Time helpers */
uint64_t current_time_us(void);
double   current_time_ms(void);
void     sleep_ms(double ms);

/* CRC-32 IEEE 802.3 Checksum */
uint32_t calculate_crc32(const uint8_t *data, size_t length);
bool     verify_crc32(const uint8_t *data, size_t length, uint32_t expected_crc);

/* Frame Builders */
void create_mac_frame(MacFrame *frame, uint8_t station_id, uint8_t seq,
                      const uint8_t *payload, uint16_t payload_len);

/* Strategy string helpers */
const char* mac_strategy_to_string(MacStrategy strategy);
MacStrategy parse_mac_strategy(const char *str);

#ifdef __cplusplus
}
#endif

#endif /* CSMA_COMMON_H */
