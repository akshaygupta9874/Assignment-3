/* ==============================================================================
 * channel_wire.h
 * TCP socket abstraction, framing, and timing primitives
 * ============================================================================== */

#ifndef CHANNEL_WIRE_H
#define CHANNEL_WIRE_H

#include "csma_common.h"

/* TCP Socket Creation and Management */
int  tcp_server_listen(int port);
int  tcp_client_connect(const char *ip, int port);
void set_socket_nodelay(int fd);
void set_socket_nonblocking(int fd, bool nonblocking);

/* Exact-Byte TCP Stream Framing */
int  tcp_send_exact(int fd, const void *buf, size_t len);
int  tcp_recv_exact(int fd, void *buf, size_t len);

/* High-Level Channel Message IPC */
int  tcp_send_msg(int fd, const ChannelMessage *msg);
int  tcp_recv_msg(int fd, ChannelMessage *msg, int timeout_ms);

#endif /* CHANNEL_WIRE_H */
