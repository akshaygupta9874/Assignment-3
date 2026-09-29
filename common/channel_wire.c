/* ==============================================================================
 * channel_wire.c
 * Implementation of TCP socket helpers, stream framing, CRC-32, and time utilities
 * ============================================================================== */

#include "channel_wire.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <netinet/tcp.h>
#include <sys/time.h>

/* --------------------------------------------------------------------------
 * High-Resolution Time Utilities
 * -------------------------------------------------------------------------- */
uint64_t current_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((uint64_t)ts.tv_sec * 1000000ULL) + ((uint64_t)ts.tv_nsec / 1000ULL);
}

double current_time_ms(void) {
    return (double)current_time_us() / 1000.0;
}

void sleep_ms(double ms) {
    if (ms <= 0.0) return;
    struct timespec req, rem;
    req.tv_sec = (time_t)(ms / 1000.0);
    req.tv_nsec = (long)((ms - (req.tv_sec * 1000.0)) * 1000000.0);
    while (nanosleep(&req, &rem) == -1 && errno == EINTR) {
        req = rem;
    }
}

/* --------------------------------------------------------------------------
 * CRC-32 (IEEE 802.3 Ethernet Polynomial: 0xEDB88320 reflected)
 * -------------------------------------------------------------------------- */
static uint32_t crc32_tab[256];
static bool crc32_initialized = false;

static void init_crc32_table(void) {
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int j = 0; j < 8; j++) {
            if (c & 1)
                c = 0xEDB88320L ^ (c >> 1);
            else
                c = c >> 1;
        }
        crc32_tab[i] = c;
    }
    crc32_initialized = true;
}

uint32_t calculate_crc32(const uint8_t *data, size_t length) {
    if (!crc32_initialized) {
        init_crc32_table();
    }
    uint32_t crc = 0xFFFFFFFFL;
    for (size_t i = 0; i < length; i++) {
        crc = crc32_tab[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFFL;
}

bool verify_crc32(const uint8_t *data, size_t length, uint32_t expected_crc) {
    return calculate_crc32(data, length) == expected_crc;
}

/* --------------------------------------------------------------------------
 * Frame Construction
 * -------------------------------------------------------------------------- */
void create_mac_frame(MacFrame *frame, uint8_t station_id, uint8_t seq,
                      const uint8_t *payload, uint16_t payload_len) {
    memset(frame, 0, sizeof(MacFrame));

    /* Locally Administered MAC Addresses */
    frame->dst_mac[0] = 0x02; frame->dst_mac[1] = 0x00; frame->dst_mac[2] = 0x00;
    frame->dst_mac[3] = 0x00; frame->dst_mac[4] = 0x00; frame->dst_mac[5] = 0xFF; /* Broadcast Receiver */

    frame->src_mac[0] = 0x02; frame->src_mac[1] = 0x00; frame->src_mac[2] = 0x00;
    frame->src_mac[3] = 0x00; frame->src_mac[4] = 0x00; frame->src_mac[5] = station_id;

    if (payload_len > DEFAULT_PAYLOAD_SIZE) {
        payload_len = DEFAULT_PAYLOAD_SIZE;
    }
    frame->length = payload_len;
    frame->seq_num = seq;
    frame->station_id = station_id;

    if (payload && payload_len > 0) {
        memcpy(frame->payload, payload, payload_len);
    }

    /* Compute CRC-32 over Header + Payload */
    size_t data_len = sizeof(MacFrame) - sizeof(uint32_t);
    frame->fcs = calculate_crc32((const uint8_t *)frame, data_len);
}

/* --------------------------------------------------------------------------
 * TCP Socket and Framing Primitives
 * -------------------------------------------------------------------------- */
void set_socket_nodelay(int fd) {
    int opt = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt));
}

void set_socket_nonblocking(int fd, bool nonblocking) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return;
    if (nonblocking)
        flags |= O_NONBLOCK;
    else
        flags &= ~O_NONBLOCK;
    fcntl(fd, F_SETFL, flags);
}

int tcp_server_listen(int port) {
    int serverfd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverfd < 0) {
        perror("server socket failed");
        return -1;
    }

    int opt = 1;
    setsockopt(serverfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family      = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port        = htons((uint16_t)port);

    if (bind(serverfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("server bind failed");
        close(serverfd);
        return -1;
    }

    if (listen(serverfd, 64) < 0) {
        perror("server listen failed");
        close(serverfd);
        return -1;
    }

    return serverfd;
}

int tcp_client_connect(const char *ip, int port) {
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port   = htons((uint16_t)port);
    inet_pton(AF_INET, ip, &server_addr.sin_addr);

    for (int attempt = 0; attempt < 30; attempt++) {
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        if (fd < 0) {
            perror("client socket create failed");
            return -1;
        }

        set_socket_nodelay(fd);

        if (connect(fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) == 0) {
            return fd; /* Successfully connected! */
        }

        close(fd);
        usleep(50000); /* 50 ms pause before retry */
    }

    return -1;
}

int tcp_send_exact(int fd, const void *buf, size_t len) {
    size_t total = 0;
    const char *p = (const char *)buf;
    while (total < len) {
        ssize_t n = send(fd, p + total, len - total, 0);
        if (n <= 0) {
            if (n < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) {
                usleep(1000);
                continue;
            }
            return -1;
        }
        total += (size_t)n;
    }
    return (int)total;
}

int tcp_recv_exact(int fd, void *buf, size_t len) {
    size_t total = 0;
    char *p = (char *)buf;
    while (total < len) {
        ssize_t n = recv(fd, p + total, len - total, 0);
        if (n <= 0) {
            if (n < 0 && (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)) {
                usleep(1000);
                continue;
            }
            return (n == 0) ? 0 : -1; /* 0 = EOF (peer disconnected) */
        }
        total += (size_t)n;
    }
    return (int)total;
}

int tcp_send_msg(int fd, const ChannelMessage *msg) {
    return tcp_send_exact(fd, msg, sizeof(ChannelMessage));
}

int tcp_recv_msg(int fd, ChannelMessage *msg, int timeout_ms) {
    if (timeout_ms >= 0) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(fd, &readfds);

        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;

        int ready = select(fd + 1, &readfds, NULL, NULL, &tv);
        if (ready <= 0) {
            return ready; /* 0 = timeout, -1 = select error */
        }
    }

    return tcp_recv_exact(fd, msg, sizeof(ChannelMessage));
}

/* --------------------------------------------------------------------------
 * Strategy Parsers and Utilities
 * -------------------------------------------------------------------------- */
const char* mac_strategy_to_string(MacStrategy strategy) {
    switch (strategy) {
        case STRATEGY_NON_PERSISTENT: return "Non-Persistent CSMA";
        case STRATEGY_ONE_PERSISTENT: return "1-Persistent CSMA";
        case STRATEGY_P_PERSISTENT:   return "p-Persistent CSMA";
        case STRATEGY_CSMA_CD:        return "CSMA/CD";
        case STRATEGY_CSMA_CA:        return "CSMA/CA";
        default:                      return "Unknown Strategy";
    }
}

MacStrategy parse_mac_strategy(const char *str) {
    if (!str) return STRATEGY_CSMA_CD;
    if (strcasecmp(str, "non_persistent") == 0 || strcmp(str, "1") == 0 || strcasecmp(str, "non_p") == 0)
        return STRATEGY_NON_PERSISTENT;
    if (strcasecmp(str, "one_persistent") == 0 || strcmp(str, "2") == 0 || strcasecmp(str, "1_p") == 0)
        return STRATEGY_ONE_PERSISTENT;
    if (strcasecmp(str, "p_persistent") == 0 || strcmp(str, "3") == 0 || strcasecmp(str, "p_p") == 0)
        return STRATEGY_P_PERSISTENT;
    if (strcasecmp(str, "csma_cd") == 0 || strcmp(str, "4") == 0 || strcasecmp(str, "cd") == 0)
        return STRATEGY_CSMA_CD;
    if (strcasecmp(str, "csma_ca") == 0 || strcmp(str, "5") == 0 || strcasecmp(str, "ca") == 0)
        return STRATEGY_CSMA_CA;
    return STRATEGY_CSMA_CD;
}
