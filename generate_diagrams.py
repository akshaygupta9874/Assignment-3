#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
generate_diagrams.py
Generates publication-grade architectural diagrams, protocol flowcharts,
and multi-process POSIX Shared Memory workflow diagrams for the CSMA Technical Report.

Engineered with:
- Geometrically verified coordinates and boundaries guaranteeing zero text clipping.
- Generous padding, margins, and pastel color palettes.
- Multi-Process POSIX Shared Memory architecture with process-shared mutexes.
- Strict isolation of Jamming (0x55555555) and Truncated BEB to CSMA/CD only.
==============================================================================
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "results" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Helper: Draw Rounded Box with Centered Text & Strict Boundary Controls
# ------------------------------------------------------------------------------
def draw_rounded_box(ax, text, x, y, w, h, bg='#EBF5FB', border='#2980B9',
                     fontsize=11.0, text_color='#111111', pad=0.15, lw=2.0, zorder=3):
    box = patches.FancyBboxPatch((x - w/2, y - h/2), w, h,
                                 boxstyle=f"round,pad={pad}",
                                 facecolor=bg, edgecolor=border, lw=lw, zorder=zorder)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, zorder=zorder+1, linespacing=1.22)
    return box

# ------------------------------------------------------------------------------
# Helper: Draw Diamond Decision Box
# ------------------------------------------------------------------------------
def draw_diamond_box(ax, text, x, y, w, h, bg='#FEF9E7', border='#F39C12',
                     fontsize=11.0, text_color='#111111', lw=2.0, zorder=3):
    pts = [[x, y + h/2], [x + w/2, y], [x, y - h/2], [x - w/2, y]]
    diamond = patches.Polygon(pts, facecolor=bg, edgecolor=border, lw=lw, zorder=zorder)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, zorder=zorder+1, linespacing=1.18)
    return diamond

# ------------------------------------------------------------------------------
# Helper: Draw Directional Arrow with Optional Label
# ------------------------------------------------------------------------------
def draw_arrow_connector(ax, x1, y1, x2, y2, label="", color='#2C3E50', lw=2.0,
                         label_pos=0.5, label_side='right', fontsize=10.0, label_color='#B03A2E', zorder=2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=16),
                zorder=zorder)
    if label:
        lx = x1 + (x2 - x1) * label_pos
        ly = y1 + (y2 - y1) * label_pos
        offset_x = 0.25 if label_side == 'right' else -0.25
        ha = 'left' if label_side == 'right' else 'right'
        ax.text(lx + offset_x, ly, label, fontsize=fontsize, color=label_color,
                fontweight='bold', ha=ha, va='center', zorder=zorder+3,
                bbox=dict(boxstyle="round,pad=0.20", facecolor='white', edgecolor='none', alpha=0.95))

# ==============================================================================
# Diagram 1: Multi-Process System Architecture & POSIX Shared Memory Bus
# ==============================================================================
def create_system_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 11), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11.5)
    ax.axis('off')

    # Title
    ax.text(6.0, 11.05, "CONCURRENT MULTI-THREADED SYSTEM ARCHITECTURE: BROADCAST BUS",
            ha='center', va='center', fontsize=16, fontweight='bold', color='#1A252F')

    # TOP: Shared Channel Bus Coordinator Box
    srv_text = (
        "SHARED PHYSICAL BROADCAST CHANNEL (ChannelBus with Mutex & Cond Vars)\n\n"
        "• State Machine: IDLE (0.0V)  |  BUSY (1.0V)  |  COLLISION (>= 2.0V)\n"
        "• Constructive Superposition: V_bus = active_transmitters * 1.0V\n"
        "• Thread Synchronization: POSIX pthread_mutex_t & pthread_cond_t\n"
        "• Fast Collision Dispatcher: pthread_cond_broadcast() on destructive voltage spike\n"
        "• Global Metrics: Microsecond tracking of idle, busy, and collision intervals"
    )
    draw_rounded_box(ax, srv_text, 6.0, 9.1, 11.0, 2.9, bg='#EBF5FB', border='#2980B9',
                     fontsize=11.5, text_color='#1A5276', pad=0.15)

    # Bi-directional Arrow between Coordinator and Bus
    ax.annotate('', xy=(6.0, 6.55), xytext=(6.0, 7.65),
                arrowprops=dict(arrowstyle="<->", color='#2980B9', lw=2.8), zorder=4)
    ax.text(6.0, 7.1, "Shared Channel Bus State & Voltage Superposition Sampling",
            fontsize=11.5, color='#1B4F72', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.25", facecolor='#FFFFFF', edgecolor='#2980B9', lw=1.6, zorder=5))

    # MIDDLE: Emulated Shared Broadcast Coaxial Bus
    wire = patches.Rectangle((0.6, 5.9), 10.8, 0.65, facecolor='#2C3E50', edgecolor='#1A252F', lw=2.6, zorder=3)
    ax.add_patch(wire)
    ax.text(6.0, 6.22, "EMULATED SHARED PHYSICAL BROADCAST BUS (COAXIAL MEDIUM)",
            ha='center', va='center', color='white', fontsize=12.5, fontweight='bold', zorder=4)

    # 3 Contending Station Nodes (x = 2.2, 6.0, 9.8) with width=3.2
    stations_data = [
        ("STATION 1 (Worker Thread)\nNon-Persistent CSMA\n\n• Senses shared wire voltage\n• If BUSY: random backoff\n  T = R * Slot (R in [1, 16])\n• Defers sensing during backoff\n• POSIX thread execution\n• Mutex synchronized access",
         2.2, '#FDEDEC', '#E74C3C'),
        ("STATION 2 (Worker Thread)\n1-Persistent CSMA\n\n• Continuous wire listening\n• If IDLE: transmit immediately\n  with probability p = 1.0\n• Zero deferral on light load\n• Herd collisions under\n  heavy contending load",
         6.0, '#FEF9E7', '#F39C12'),
        ("STATION 3 (Worker Thread)\nIEEE 802.3 CSMA/CD\n\n• Listen-While-Talk (LWT)\n  (Superposition sensing)\n• Microsecond abort (< 2*Tau)\n• 32-bit Jam (0x55555555)\n• Truncated BEB (2^K slots)\n• Strict CD-only backoff",
         9.8, '#EAF2F8', '#2980B9'),
    ]

    for text, x, bg, border in stations_data:
        # Cable drop line
        ax.plot([x, x], [5.9, 4.4], color='#7F8C8D', lw=2.6, zorder=2)
        ax.plot(x, 5.9, 'o', color=border, markersize=11, zorder=4)

        # Thread Sync Badge
        ax.text(x, 5.15, "POSIX Thread\n(pthread_create)", ha='center', va='center',
                fontsize=10.0, fontweight='bold', color='#1B4F72',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor=border, lw=1.5, zorder=5))

        # Station Box
        draw_rounded_box(ax, text, x, 2.3, 3.2, 3.8, bg=bg, border=border,
                         fontsize=11.0, text_color='#111111', pad=0.14)

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_system_architecture.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 2: Space-Time Collision Cone & Physical Superposition
# ==============================================================================
def create_vulnerable_period_and_energy_diagram():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), dpi=300, gridspec_kw={'height_ratios': [1.15, 1.0]})

    # -------------------------------------------------------------------------
    # (A) Space-Time Wavefront Collision Geometry (Top)
    # -------------------------------------------------------------------------
    ax1.set_xlim(0, 12)
    ax1.set_ylim(-0.2, 9.0)
    ax1.axis('off')
    ax1.set_title('(A) Space-Time Model of Vulnerable Window Tau = Tp & Wavefront Collision Geometry',
                  fontsize=15, fontweight='bold', pad=12, color='#1A252F')

    # Distance Axis (x) & Time Axis (t)
    ax1.annotate('', xy=(11.0, 0.8), xytext=(1.2, 0.8),
                 arrowprops=dict(arrowstyle="-|>", color='#2C3E50', lw=2.4))
    ax1.text(11.1, 0.8, "Distance x along bus", fontsize=12.5, fontweight='bold', va='center', color='#2C3E50')

    ax1.annotate('', xy=(1.2, 8.4), xytext=(1.2, 0.8),
                 arrowprops=dict(arrowstyle="-|>", color='#2C3E50', lw=2.4))
    ax1.text(1.1, 8.6, "Time t", fontsize=12.5, fontweight='bold', ha='center', color='#2C3E50')

    # Station vertical timelines: Station A at x=2.4, Station B at x=9.4
    ax1.plot([2.4, 2.4], [0.8, 8.0], 'k--', lw=2.0, alpha=0.45)
    ax1.text(2.4, 0.35, "Station A (x=0)", ha='center', fontweight='bold', fontsize=13, color='#1B4F72')

    ax1.plot([9.4, 9.4], [0.8, 8.0], 'k--', lw=2.0, alpha=0.45)
    ax1.text(9.4, 0.35, "Station B (x=L)", ha='center', fontweight='bold', fontsize=13, color='#78281F')

    # Time markers on t-axis
    ax1.text(0.9, 1.5, "t = 0", ha='right', va='center', fontsize=12, fontweight='bold', color='#1B4F72')
    ax1.text(0.9, 4.5, "t = Tau", ha='right', va='center', fontsize=12, fontweight='bold', color='#C0392B')
    ax1.text(0.9, 7.5, "t = 2 Tau", ha='right', va='center', fontsize=12, fontweight='bold', color='#111111')

    # Station A transmits rightward wavefront from (2.4, 1.5) to (9.4, 4.5)
    ax1.plot([2.4, 9.4], [1.5, 4.5], color='#2980B9', lw=3.2, zorder=3)
    ax1.text(3.8, 2.3, "Station A Wavefront (Rightward: +v)",
             fontsize=10.5, fontweight='bold', color='#1B4F72',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#EBF5FB', edgecolor='#2980B9', lw=1.2))

    # Vulnerable Window bracket at Station B from t=1.5 to t=4.5
    ax1.plot([9.6, 9.85, 9.85, 9.6], [1.5, 1.5, 4.5, 4.5], color='#C0392B', lw=2.2)
    ax1.text(10.05, 3.0, "VULNERABLE WINDOW\nDuration Tau = Tp\nMedium at B reads 0.0V\nStation B senses IDLE!",
             color='#C0392B', fontsize=10.5, fontweight='bold', va='center')

    # Station B transmits at tB = 4.1 (just before Tau expires at B!)
    ax1.plot([9.4, 2.4], [4.1, 7.1], color='#E74C3C', lw=3.2, zorder=3)
    ax1.plot(9.4, 4.1, 'o', color='#E74C3C', markersize=10, zorder=4)

    # Note on LEFT side of Station B
    ax1.annotate('B senses IDLE at t = Tau - eps\nand begins transmitting!',
                 xy=(9.3, 4.1), xytext=(7.8, 3.5), ha='right', va='top',
                 arrowprops=dict(arrowstyle='->', color='#900C3F', lw=1.5),
                 fontsize=9.8, fontweight='bold', color='#900C3F',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='#FADBD8', edgecolor='#E74C3C', lw=1.2))

    # Collision point at (8.93, 4.30)
    ax1.plot(8.93, 4.30, '*', color='#F39C12', mec='#C0392B', mew=1.5, markersize=26, zorder=6)
    ax1.annotate('COLLISION OCCURS ON WIRE!\nx ~ L, t ~ Tau - eps/2',
                 xy=(8.93, 4.30), xytext=(6.5, 5.2), ha='center',
                 arrowprops=dict(arrowstyle='->', color='#C0392B', lw=1.8),
                 fontsize=10.5, fontweight='bold', color='#922B21',
                 bbox=dict(boxstyle="round,pad=0.25", facecolor='#FADBD8', edgecolor='#C0392B', lw=1.5), zorder=7)

    # B detects collision at t=4.5
    ax1.plot(9.4, 4.5, 'X', color='#C0392B', markersize=13, zorder=6)

    # Returning collision wave reaches Station A at t = 7.1 <= 2*Tau
    ax1.plot(2.4, 7.1, 'X', color='#C0392B', markersize=14, zorder=6)
    ax1.annotate('Worst-Case Collision Detection at Transmitter (t <= 2*Tau):\n'
                 '• Returning collision wave reaches Station A at t = 2*Tp - eps\n'
                 '• Transmitter must continue transmitting until 2*Tp to detect collision\n'
                 '• Fundamental Ethernet Requirement: Frame Time T_fr >= 2*Tp (L_min = 64B)',
                 xy=(2.4, 7.1), xytext=(3.0, 7.9),
                 arrowprops=dict(arrowstyle='->', color='#1B4F72', lw=2.0),
                 fontsize=10.5, fontweight='bold', color='#1B4F72',
                 bbox=dict(boxstyle="round,pad=0.25", facecolor='#EBF5FB', edgecolor='#2980B9', lw=1.6))

    # -------------------------------------------------------------------------
    # (B) Tri-State Bus Voltage Superposition Model (Bottom)
    # -------------------------------------------------------------------------
    ax2.set_xlim(0, 11)
    ax2.set_ylim(-0.3, 3.2)
    ax2.set_title('(B) Tri-State Bus Voltage Superposition Model (0.0V, 1.0V, >= 2.0V Collision Spike)',
                  fontsize=15, fontweight='bold', pad=12, color='#1A252F')

    ax2.set_xlabel('Timeline along Shared Medium (ms)', fontsize=12.5, fontweight='bold')
    ax2.set_ylabel('Bus Voltage (Volts)', fontsize=12.5, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)

    # Voltage trace:
    t_vals = [0.0, 1.8, 1.8, 3.8, 3.8, 6.0, 6.1, 6.3, 6.5, 6.7, 6.9, 7.1, 7.3, 7.3, 10.5]
    v_vals = [0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 0.8, 2.0, 0.8, 2.0, 0.8, 2.0, 0.8, 0.0, 0.0]
    ax2.plot(t_vals, v_vals, color='#1B4F72', lw=3.0, label="Bus Voltage")

    # Threshold line at 1.5V
    ax2.axhline(1.5, color='#C0392B', linestyle=':', lw=2.2, label="Collision Threshold (1.5V)")
    ax2.text(0.3, 1.62, "COLLISION DETECTION THRESHOLD (>= 1.5V)", color='#C0392B', fontsize=11.5, fontweight='bold')

    # Badges
    ax2.text(0.9, 0.45, "IDLE\n(0.0V)", ha='center', fontsize=11.5, fontweight='bold', color='#27AE60',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#EAFAF1', edgecolor='#27AE60', lw=1.4))
    ax2.text(2.8, 0.45, "BUSY\n(1.0V)", ha='center', fontsize=11.5, fontweight='bold', color='#B7950B',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FEF9E7', edgecolor='#D4AC0D', lw=1.4))
    ax2.text(4.8, 2.45, "DESTRUCTIVE COLLISION\n(V = 2.0V >= 1.5V Threshold)", ha='center',
             fontsize=11.0, fontweight='bold', color='#C0392B',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FADBD8', edgecolor='#C0392B', lw=1.5))
    ax2.annotate('32-Bit JAM\n(0x55555555)', xy=(6.7, 2.0), xytext=(7.5, 2.45),
                 ha='center', fontsize=11.0, fontweight='bold', color='#7D3C98',
                 arrowprops=dict(arrowstyle='->', color='#7D3C98', lw=1.8),
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='#F4ECF7', edgecolor='#7D3C98', lw=1.4))
    ax2.text(9.3, 0.45, "CLEARED\n(Truncated BEB)", ha='center', fontsize=11.5, fontweight='bold', color='#2E86C1',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#EBF5FB', edgecolor='#2E86C1', lw=1.4))

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_vulnerable_period_and_energy.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 3: Comparative CSMA Protocol Workflows (2x2 Grid)
# ==============================================================================
def create_csma_flowcharts():
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 14), dpi=300)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.94, bottom=0.05, wspace=0.22, hspace=0.24)

    # -------------------------------------------------------------------------
    # (A) Non-Persistent CSMA (Top-Left)
    # -------------------------------------------------------------------------
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 11)
    ax1.axis('off')
    ax1.set_title('(A) Non-Persistent CSMA (Random Deferral)', fontsize=14, fontweight='bold', color='#1A252F', pad=10)

    # Main trunk at x = 4.2
    draw_rounded_box(ax1, "Frame Ready to Transmit", 4.2, 10.0, 5.2, 0.9, bg='#E8F8F5', border='#1ABC9C', fontsize=11.0)
    draw_arrow_connector(ax1, 4.2, 9.55, 4.2, 8.7)

    # Diamond at (4.2, 7.9)
    draw_diamond_box(ax1, "Channel Idle?\n(V == 0.0V)", 4.2, 7.9, 5.0, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=11.0)

    # YES: Channel Idle -> Transmit
    draw_arrow_connector(ax1, 4.2, 7.15, 4.2, 5.95)
    ax1.text(4.4, 6.55, "Yes\n(Idle)", fontsize=10.0, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax1, "Transmit Entire Frame\nDuration = T_frame", 4.2, 5.3, 5.2, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=11.0)
    draw_arrow_connector(ax1, 4.2, 4.75, 4.2, 3.85)

    draw_rounded_box(ax1, "Transmission Complete\nAwait ACK / Success", 4.2, 3.3, 5.2, 0.9, bg='#EBF5FB', border='#2980B9', fontsize=11.0)

    # NO: Channel Busy -> Random Backoff box on right lane (x = 8.3)
    draw_arrow_connector(ax1, 6.7, 7.9, 8.3, 7.9)
    ax1.text(7.3, 8.15, "Busy", fontsize=10.0, fontweight='bold', color='#C0392B', ha='center')

    draw_arrow_connector(ax1, 8.3, 7.9, 8.3, 6.8)
    draw_rounded_box(ax1, "Random Backoff\nT_B = R * Slot\n(R in [1, 16])\nDefer Sensing", 8.3, 5.6, 2.8, 2.2,
                     bg='#FDEDEC', border='#E74C3C', fontsize=10.0)

    # Loop back from Backoff box up to before diamond
    ax1.plot([8.3, 8.3], [4.5, 1.8], color='#C0392B', lw=1.8)
    ax1.plot([8.3, 1.0], [1.8, 1.8], color='#C0392B', lw=1.8)
    ax1.plot([1.0, 1.0], [1.8, 9.1], color='#C0392B', lw=1.8)
    draw_arrow_connector(ax1, 1.0, 9.1, 4.2, 9.1, color='#C0392B', lw=1.8)
    ax1.text(1.2, 2.1, "After Backoff: Retry Sense", fontsize=9.5, fontweight='bold', color='#C0392B')

    # Summary badge at bottom
    ax1.text(4.2, 0.6, "Characteristics: Low collision rate, higher idle delay under low load",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    # -------------------------------------------------------------------------
    # (B) 1-Persistent CSMA (Top-Right)
    # -------------------------------------------------------------------------
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 11)
    ax2.axis('off')
    ax2.set_title('(B) 1-Persistent CSMA (Greedy Sensing)', fontsize=14, fontweight='bold', color='#1A252F', pad=10)

    # Main trunk at x = 5.0
    draw_rounded_box(ax2, "Frame Ready to Transmit", 5.0, 10.0, 5.4, 0.9, bg='#E8F8F5', border='#1ABC9C', fontsize=11.0)
    draw_arrow_connector(ax2, 5.0, 9.55, 5.0, 8.7)

    # Diamond at (5.0, 7.9)
    draw_diamond_box(ax2, "Channel Idle?\n(V == 0.0V)", 5.0, 7.9, 5.0, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=11.0)

    # Busy loop on the left: Continuous listening
    ax2.plot([2.5, 1.2], [7.9, 7.9], color='#F39C12', lw=1.8)
    ax2.plot([1.2, 1.2], [7.9, 9.1], color='#F39C12', lw=1.8)
    draw_arrow_connector(ax2, 1.2, 9.1, 5.0, 9.1, color='#F39C12', lw=1.8)
    ax2.text(1.3, 8.5, "Busy:\nKeep Listening\n(Greedy p=1.0)", fontsize=9.5, fontweight='bold', color='#B9770E')

    # YES: Channel Free -> Transmit Immediately (p=1.0)
    draw_arrow_connector(ax2, 5.0, 7.15, 5.0, 5.95)
    ax2.text(5.2, 6.55, "Channel Free\n(p = 1.0)", fontsize=10.0, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax2, "Transmit Immediately\nDuration = T_frame", 5.0, 5.3, 5.4, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=11.0)
    draw_arrow_connector(ax2, 5.0, 4.75, 5.0, 3.95)

    draw_rounded_box(ax2, "Collision Hazard on Wire!\nIf multiple stations waited,\nall transmit together -> COLLISION!",
                     5.0, 3.1, 6.6, 1.5, bg='#FDEDEC', border='#E74C3C', fontsize=10.5, text_color='#922B21')

    # Summary badge at bottom
    ax2.text(5.0, 0.6, "Characteristics: Zero delay on idle channel, severe herd collisions at high load",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    # -------------------------------------------------------------------------
    # (C) p-Persistent CSMA (Bottom-Left)
    # -------------------------------------------------------------------------
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 11)
    ax3.axis('off')
    ax3.set_title('(C) p-Persistent CSMA (Slotted Compromise)', fontsize=14, fontweight='bold', color='#1A252F', pad=10)

    # Main trunk at x = 4.2
    draw_rounded_box(ax3, "Wait Channel Idle + Slot Sync", 4.2, 10.0, 5.4, 0.9, bg='#E8F8F5', border='#1ABC9C', fontsize=11.0)
    draw_arrow_connector(ax3, 4.2, 9.55, 4.2, 8.7)

    # Diamond at (4.2, 7.9): Random Roll r <= p?
    draw_diamond_box(ax3, "Random Roll:\nr <= p?", 4.2, 7.9, 4.6, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=11.0)

    # YES (prob p): Transmit in current slot
    draw_arrow_connector(ax3, 4.2, 7.15, 4.2, 5.95)
    ax3.text(4.4, 6.55, "Yes (prob p)\nTransmit", fontsize=10.0, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax3, "Transmit Frame in Slot\nDuration = T_frame", 4.2, 5.3, 5.2, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=11.0)
    draw_arrow_connector(ax3, 4.2, 4.75, 4.2, 3.85)

    draw_rounded_box(ax3, "Optimal Parameter Tuning:\np* = 1 / N_active\nMax S = 1/e ~ 36.8%", 4.2, 3.1, 5.2, 1.3,
                     bg='#EBF5FB', border='#2980B9', fontsize=10.5)

    # NO (prob 1-p): Defer 1 slot, re-sense
    draw_arrow_connector(ax3, 6.5, 7.9, 8.2, 7.9)
    ax3.text(7.3, 8.15, "No (1-p)", fontsize=10.0, fontweight='bold', color='#2980B9', ha='center')

    draw_arrow_connector(ax3, 8.2, 7.9, 8.2, 6.8)
    draw_rounded_box(ax3, "Defer 1 Slot\nWait T_slot\nRe-sense Wire", 8.2, 5.7, 2.6, 2.0,
                     bg='#EBF5FB', border='#2980B9', fontsize=10.0)

    # Loop back from Defer box to top of slot sync
    ax3.plot([8.2, 8.2], [4.7, 1.8], color='#2980B9', lw=1.8)
    ax3.plot([8.2, 1.0], [1.8, 1.8], color='#2980B9', lw=1.8)
    ax3.plot([1.0, 1.0], [1.8, 9.1], color='#2980B9', lw=1.8)
    draw_arrow_connector(ax3, 1.0, 9.1, 4.2, 9.1, color='#2980B9', lw=1.8)
    ax3.text(1.2, 2.1, "Next Slot: Re-evaluate r <= p", fontsize=9.5, fontweight='bold', color='#1B4F72')

    # Summary badge at bottom
    ax3.text(4.2, 0.6, "Characteristics: Tunable tradeoff between delay and collisions via persistence p",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    # -------------------------------------------------------------------------
    # (D) IEEE 802.3 CSMA/CD (Bottom-Right)
    # -------------------------------------------------------------------------
    ax4.set_xlim(0, 10.5)
    ax4.set_ylim(0, 11)
    ax4.axis('off')
    ax4.set_title('(D) IEEE 802.3 CSMA/CD (Listen-While-Talk)', fontsize=14, fontweight='bold', color='#1A252F', pad=10)

    # Main trunk at x = 3.8
    draw_rounded_box(ax4, "Sense Idle -> 96-bit IFG\nStart Transmitting Frame", 3.8, 10.0, 5.0, 1.0, bg='#E8F8F5', border='#1ABC9C', fontsize=10.5)
    draw_arrow_connector(ax4, 3.8, 9.5, 3.8, 8.7)

    # Diamond at (3.8, 7.9): Collision Detected (V >= 2.0V)?
    draw_diamond_box(ax4, "Collision on Wire?\n(V_bus >= 2.0V)", 3.8, 7.9, 4.8, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=10.5)

    # NO: Clean transmission -> Success
    draw_arrow_connector(ax4, 3.8, 7.15, 3.8, 5.95)
    ax4.text(4.0, 6.55, "No\n(Clean)", fontsize=10.0, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax4, "Frame Transmission Success!\nNo Jam, Zero Backoff Needed", 3.8, 5.3, 5.0, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=10.0)
    draw_arrow_connector(ax4, 3.8, 4.75, 3.8, 3.85)

    draw_rounded_box(ax4, "Delivery Complete\nReset K = 0", 3.8, 3.3, 5.0, 0.9, bg='#EBF5FB', border='#2980B9', fontsize=11.0)

    # YES: Collision Detected -> Abort & JAM & BEB in right lane (x = 8.4)
    draw_arrow_connector(ax4, 6.2, 7.9, 8.4, 7.9)
    ax4.text(7.3, 8.15, "Collision!", fontsize=10.0, fontweight='bold', color='#C0392B', ha='center')

    draw_arrow_connector(ax4, 8.4, 7.9, 8.4, 6.9)
    draw_rounded_box(ax4, "1. Abort Frame (< 2*Tau)\n2. Send 32-Bit Jam\n   (0x55555555)\n3. Truncated BEB:\n   R in [0, 2^min(K,10)-1]\n4. Delay T_B = R * Slot",
                     8.4, 5.2, 3.5, 3.2, bg='#FADBD8', border='#C0392B', fontsize=9.0, text_color='#922B21')

    # Loop back from BEB box to top of sense
    ax4.plot([8.4, 8.4], [3.6, 1.8], color='#C0392B', lw=1.8)
    ax4.plot([8.4, 1.0], [1.8, 1.8], color='#C0392B', lw=1.8)
    ax4.plot([1.0, 1.0], [1.8, 9.1], color='#C0392B', lw=1.8)
    draw_arrow_connector(ax4, 1.0, 9.1, 3.8, 9.1, color='#C0392B', lw=1.8)
    ax4.text(1.2, 2.1, "After BEB Delay: Retransmit (K=K+1)", fontsize=9.5, fontweight='bold', color='#C0392B')

    # Summary badge at bottom
    ax4.text(4.2, 0.6, "Characteristics: Jamming & Truncated BEB exclusively in CSMA/CD; aborts wasted airtime",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_csma_fsm_workflows.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 4: Comprehensive CSMA/CD FSM & Space-Time Collision Timeline
# ==============================================================================
def create_csmacd_detailed_flowchart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 13.5), dpi=300, gridspec_kw={'width_ratios': [1.25, 1.0]})
    plt.subplots_adjust(left=0.03, right=0.97, top=0.93, bottom=0.04, wspace=0.20)

    # -------------------------------------------------------------------------
    # (A) Flowchart (Left)
    # -------------------------------------------------------------------------
    ax1.set_xlim(-0.8, 15.5)
    ax1.set_ylim(-0.2, 16.5)
    ax1.axis('off')
    ax1.set_title('(A) IEEE 802.3 CSMA/CD Station Protocol Flowchart',
                  fontsize=14.5, fontweight='bold', pad=12, color='#1A252F')

    x_trunk = 3.6
    draw_rounded_box(ax1, "New Frame for Transmission\nInitialize Counter: K = 0",
                     x_trunk, 15.6, 5.4, 1.0, bg='#E8F8F5', border='#1ABC9C', fontsize=10.0)
    draw_arrow_connector(ax1, x_trunk, 15.1, x_trunk, 14.3)

    draw_diamond_box(ax1, "Channel Idle?\n(V_wire == 0.0V)", x_trunk, 13.5, 4.8, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=10.0)

    # Busy loop on left
    ax1.plot([x_trunk - 2.4, 0.6], [13.5, 13.5], color='#F39C12', lw=1.8)
    ax1.plot([0.6, 0.6], [13.5, 14.65], color='#F39C12', lw=1.8)
    draw_arrow_connector(ax1, 0.6, 14.65, x_trunk, 14.65, color='#F39C12', lw=1.8)
    ax1.text(0.75, 14.1, "Busy:\nWait 1-P", fontsize=9.0, fontweight='bold', color='#B9770E')

    # Yes -> Wait IFG
    draw_arrow_connector(ax1, x_trunk, 12.75, x_trunk, 11.95)
    ax1.text(x_trunk + 0.25, 12.35, "Yes (Idle)", fontsize=9.5, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax1, "Wait 96-bit IFG (9.6 us)\nBegin Transmission & LWT",
                     x_trunk, 11.35, 5.4, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=10.0)
    draw_arrow_connector(ax1, x_trunk, 10.8, x_trunk, 9.95)

    # Collision Diamond
    draw_diamond_box(ax1, "Collision on Wire?\n(V_bus >= 2.0V)", x_trunk, 9.2, 4.8, 1.5, bg='#FEF9E7', border='#F39C12', fontsize=10.0)

    # No (Clean)
    draw_arrow_connector(ax1, x_trunk, 8.45, x_trunk, 7.4)
    ax1.text(x_trunk + 0.25, 7.95, "No (Clean)", fontsize=9.5, fontweight='bold', color='#27AE60', va='center')

    draw_rounded_box(ax1, "Frame Delivered Successfully!\nT_fr >= 2*Tau (L_min = 64B)\nNo Collision Observed",
                     x_trunk, 6.75, 5.4, 1.2, bg='#D5F5E3', border='#2ECC71', fontsize=9.5)
    draw_arrow_connector(ax1, x_trunk, 6.15, x_trunk, 5.35)

    draw_rounded_box(ax1, "Transmission Complete\nReset K = 0 | Deliver Frame",
                     x_trunk, 4.8, 5.4, 1.0, bg='#EBF5FB', border='#2980B9', fontsize=10.0)

    # Collision path to right: Column 2 at x = 9.8
    x_col2 = 9.8
    draw_arrow_connector(ax1, x_trunk + 2.4, 9.2, x_col2, 9.2)
    ax1.text((x_trunk + 2.4 + x_col2)/2, 9.45, "Collision!", fontsize=10.0, fontweight='bold', color='#C0392B', ha='center')

    draw_arrow_connector(ax1, x_col2, 9.2, x_col2, 8.5)

    draw_rounded_box(ax1, "1. Abort Frame (< 2*Tau)\n2. Emit 32-Bit Jam Signal\n   (Pattern: 0x55555555)\n3. Increment Counter: K = K + 1",
                     x_col2, 7.6, 5.0, 1.7, bg='#FADBD8', border='#C0392B', fontsize=9.2, text_color='#922B21')
    draw_arrow_connector(ax1, x_col2, 6.75, x_col2, 5.9)

    # K > 15 Diamond
    draw_diamond_box(ax1, "K > 15\nAttempts?", x_col2, 5.2, 3.4, 1.4, bg='#FEF9E7', border='#F39C12', fontsize=9.5)

    # YES (K > 15) -> Drop Packet badge
    draw_arrow_connector(ax1, x_col2 + 1.7, 5.2, 12.4, 5.2, color='#C0392B')
    ax1.text(12.0, 5.45, "Yes", fontsize=9.5, fontweight='bold', color='#C0392B', ha='center')
    draw_rounded_box(ax1, "Excess Collisions:\nDrop Frame\n(K > 15 Abort)",
                     13.7, 5.2, 2.5, 1.2, bg='#FDEDEC', border='#C0392B', fontsize=8.8, text_color='#922B21')

    # NO (K <= 15) -> Truncated BEB
    draw_arrow_connector(ax1, x_col2, 4.5, x_col2, 3.85)
    ax1.text(x_col2 + 0.25, 4.15, "No", fontsize=9.5, fontweight='bold', color='#2980B9')

    draw_rounded_box(ax1, "Truncated BEB Delay:\nR in [0, 2^min(K, 10) - 1]\nT_B = R * Slot (Slot = 2*Tau)",
                     x_col2, 3.0, 5.0, 1.6, bg='#EBF5FB', border='#2980B9', fontsize=9.2)

    # Loop back from BEB box around outside perimeter
    ax1.plot([x_col2, x_col2], [2.2, 1.2], color='#2980B9', lw=1.8)
    ax1.plot([x_col2, 0.5], [1.2, 1.2], color='#2980B9', lw=1.8)
    ax1.plot([0.5, 0.5], [1.2, 14.65], color='#2980B9', lw=1.8)
    draw_arrow_connector(ax1, 0.5, 14.65, x_trunk, 14.65, color='#2980B9', lw=1.8)
    ax1.text(5.1, 1.45, "After Backoff T_B: Retransmit Frame (Retry with K = K + 1)",
             fontsize=9.2, fontweight='bold', color='#1B4F72', ha='center')

    # Summary badge
    ax1.text(7.2, 0.35, "Strict Rule: Jamming signal and Truncated BEB backoff are exclusive to CSMA/CD",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    # -------------------------------------------------------------------------
    # (B) Collision & Jamming Timeline (Right)
    # -------------------------------------------------------------------------
    ax2.set_xlim(0, 10)
    ax2.set_ylim(-0.2, 16.5)
    ax2.axis('off')
    ax2.set_title('(B) Space-Time Collision & Jamming Timeline',
                  fontsize=14.5, fontweight='bold', pad=12, color='#1A252F')

    x_A = 2.0
    x_bus = 5.0
    x_B = 8.0

    ax2.plot([x_A, x_A], [1.2, 15.2], color='#2980B9', lw=2.4)
    ax2.text(x_A, 15.6, "Station A\n(x = 0)", ha='center', va='bottom', fontweight='bold', color='#2980B9', fontsize=11.5)

    ax2.plot([x_bus, x_bus], [1.2, 15.2], color='#2C3E50', lw=2.4)
    ax2.text(x_bus, 15.6, "Coaxial Bus\n(Medium)", ha='center', va='bottom', fontweight='bold', color='#2C3E50', fontsize=11.5)

    ax2.plot([x_B, x_B], [1.2, 15.2], color='#E74C3C', lw=2.4)
    ax2.text(x_B, 15.6, "Station B\n(x = L)", ha='center', va='bottom', fontweight='bold', color='#E74C3C', fontsize=11.5)

    # A transmits at t = 0
    ax2.plot(x_A, 14.5, 'o', color='#2980B9', markersize=9, zorder=5)
    ax2.text(x_A - 0.25, 14.5, "t = 0:\nA Transmits", ha='right', va='center', fontsize=10.0, fontweight='bold', color='#1B4F72')

    # Wavefront from A to B
    ax2.plot([x_A, x_B], [14.5, 11.7], color='#2980B9', lw=2.2, linestyle='-')

    # B transmits at t = Tau - eps
    ax2.plot(x_B, 12.8, 'o', color='#E74C3C', markersize=9, zorder=5)
    ax2.text(x_B + 0.25, 12.8, "t = Tau - eps:\nB senses idle & transmits", ha='left', va='center', fontsize=10.0, fontweight='bold', color='#922B21')

    # Wavefront from B to A
    ax2.plot([x_B, x_A], [12.8, 10.0], color='#E74C3C', lw=2.2, linestyle='-')

    # Collision intersection
    ax2.plot(6.82, 12.25, '*', color='#C0392B', markersize=22, zorder=6)

    # Callout
    draw_rounded_box(ax2, "COLLISION ON WIRE!\nV_bus >= 2.0V", 4.6, 12.25, 3.2, 0.9,
                     bg='#FADBD8', border='#C0392B', fontsize=10.0, text_color='#922B21')
    draw_arrow_connector(ax2, 6.2, 12.25, 6.65, 12.25, color='#C0392B', lw=1.6)

    # Collision reaches B
    ax2.plot(x_B, 11.7, 'X', color='#C0392B', markersize=11, zorder=5)
    ax2.text(x_B + 0.25, 11.7, "B detects collision\n& aborts frame", ha='left', va='center', fontsize=9.5, fontweight='bold', color='#C0392B')

    # Collision reaches A
    ax2.plot(x_A, 10.0, 'X', color='#C0392B', markersize=11, zorder=5)
    ax2.text(x_A - 0.25, 10.0, "t = 2*Tau:\nA detects collision\n& aborts frame!", ha='right', va='center', fontsize=9.5, fontweight='bold', color='#C0392B')

    # 6. Jamming Signal
    jam_rect = patches.FancyBboxPatch((1.4, 7.4), 7.2, 1.8, boxstyle="round,pad=0.15",
                                      facecolor='#FEF9E7', edgecolor='#F39C12', lw=2.0, zorder=4)
    ax2.add_patch(jam_rect)
    ax2.text(5.0, 8.3, "32-BIT JAMMING TRANSMISSION (0x55555555)\nBoth stations emit jam pattern (duration 3.2 to 4.8 us)\nGuarantees all bus stations recognize collision",
             ha='center', va='center', fontsize=10.2, fontweight='bold', color='#7D6608', zorder=5, linespacing=1.2)

    # 7. Truncated BEB
    beb_rect = patches.FancyBboxPatch((1.2, 3.4), 7.6, 2.8, boxstyle="round,pad=0.15",
                                      facecolor='#EBF5FB', edgecolor='#2980B9', lw=2.0, zorder=4)
    ax2.add_patch(beb_rect)
    ax2.text(5.0, 4.8, "TRUNCATED BINARY EXPONENTIAL BACKOFF (BEB)\nStation A selects R_A in [0, 2^min(K_A, 10) - 1]\nStation B selects R_B in [0, 2^min(K_B, 10) - 1]\nBackoff Delay T_B = R * Slot (Slot = 2*Tau)\nRandom slot choice desynchronizes stations",
             ha='center', va='center', fontsize=10.0, fontweight='bold', color='#1B4F72', zorder=5, linespacing=1.25)

    # 8. Re-attempt
    ax2.text(x_A, 2.0, "Station A Retries\nafter R_A * Slot", ha='center', fontsize=9.5, fontweight='bold', color='#2980B9',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor='#2980B9', lw=1.2))
    ax2.text(x_B, 2.0, "Station B Retries\nafter R_B * Slot", ha='center', fontsize=9.5, fontweight='bold', color='#E74C3C',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor='#E74C3C', lw=1.2))

    # Summary
    ax2.text(5.0, 0.35, "Minimum frame size L_min = 64 Bytes guarantees transmission lasts >= 2*Tau",
             fontsize=10.0, fontweight='bold', color='#1B4F72', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='#F2F4F4', edgecolor='#BDC3C7', lw=1.2))

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_csmacd_detailed_flowchart.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 5: Multi-Process Execution Pipelines (Station & Shared Memory Bus)
# ==============================================================================
def create_code_workflow_diagram():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.0, 14.0), dpi=300, gridspec_kw={'width_ratios': [1.0, 1.0]})
    plt.subplots_adjust(left=0.03, right=0.97, top=0.94, bottom=0.03, wspace=0.18)

    # (A) Station Thread Pipeline (Left)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0.2, 16.5)
    ax1.axis('off')
    ax1.set_title('(A) Station Thread Pipeline (POSIX pthreads)',
                  fontsize=16.0, fontweight='bold', pad=14, color='#1A252F')

    stages_station = [
        ("1. Thread Spawning & Channel Attach\n"
         "• Main spawns N concurrent station threads\n"
         "• Passes shared ChannelBus pointer in StationArgs",
         15.0, 1.48, '#E8F8F5', '#1ABC9C'),

        ("2. Carrier Sense via POSIX Mutex\n"
         "• pthread_mutex_lock(&bus->lock)\n"
         "• Reads wire voltage: 0.0V (IDLE) vs 1.0V (BUSY)",
         12.8, 1.48, '#EBF5FB', '#2980B9'),

        ("3. MAC State Machine Execution\n"
         "• Non-P: random backoff | 1-P: greedy wait\n"
         "• p-P: roll prob p | CD: transmit & listen",
         10.6, 1.48, '#FEF9E7', '#F39C12'),

        ("4. Transmission Start & Voltage Drive\n"
         "• Increments bus->active_transmitters counter\n"
         "• Medium voltage V_bus = active_transmitters * 1.0V",
         8.4, 1.48, '#FCF3CF', '#D4AC0D'),

        ("5. Listen-While-Talk (LWT Polling)\n"
         "• Slices transmission time into 100 us steps\n"
         "• Polls bus->collision_flag on every step",
         6.2, 1.48, '#FDEDEC', '#E74C3C'),

        ("6. Collision Preemption & Backoff\n"
         "• If V >= 2.0V: abort TX (< 2*Tau) + emit 32-bit JAM\n"
         "• Executes Truncated BEB backoff (CSMA/CD only)",
         4.0, 1.48, '#FADBD8', '#C0392B'),

        ("7. Clean Delivery & Thread Exit\n"
         "• If clean: frame delivered, record metrics\n"
         "• Main joins all station threads via pthread_join()",
         1.8, 1.48, '#D5F5E3', '#2ECC71'),
    ]

    for i in range(len(stages_station)):
        text, y, h, bg, border = stages_station[i]
        draw_rounded_box(ax1, text, 5.0, y, 9.2, h, bg=bg, border=border, fontsize=12.2)
        if i < len(stages_station) - 1:
            next_y = stages_station[i+1][1]
            draw_arrow_connector(ax1, 5.0, y - h/2 - 0.04, 5.0, next_y + stages_station[i+1][2]/2 + 0.04, lw=2.4)

    # (B) Shared Channel Synchronization Pipeline (Right)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0.2, 16.5)
    ax2.axis('off')
    ax2.set_title('(B) Shared Channel Medium Pipeline (POSIX Mutex/Cond)',
                  fontsize=16.0, fontweight='bold', pad=14, color='#1A252F')

    stages_server = [
        ("1. Channel Bus & Mutex Initialization\n"
         "• Initializes ChannelBus structure\n"
         "• pthread_mutex_init & pthread_cond_init",
         15.0, 1.48, '#EBF5FB', '#2980B9'),

        ("2. Station Thread Coordination\n"
         "• Fast mutex protects shared bus state\n"
         "• Coordinates N concurrent station worker threads",
         12.8, 1.48, '#E8F8F5', '#1ABC9C'),

        ("3. Continuous Wire Time Integration\n"
         "• Microsecond tracking of medium state:\n"
         "• Integrates channel_idle_time, busy_time, collision_time",
         10.6, 1.48, '#FEF9E7', '#F39C12'),

        ("4. Superposition Voltage Calculation\n"
         "• Evaluates constructive electrical superposition:\n"
         "• V_bus = active_transmitters * 1.0V",
         8.4, 1.48, '#FCF3CF', '#D4AC0D'),

        ("5. Hardware Collision Dispatcher\n"
         "• If V_bus >= 2.0V: sets collision_flag = true\n"
         "• Broadcasts pthread_cond_broadcast(&collision)",
         6.2, 1.48, '#FADBD8', '#C0392B'),

        ("6. Medium De-assertion & Clear\n"
         "• Completed stations decrement active count\n"
         "• Bus state returns to IDLE (0.0V) upon clear",
         4.0, 1.48, '#D5F5E3', '#2ECC71'),

        ("7. Global Performance Metrics Logging\n"
         "• Aggregates per-station metrics, prints summary\n"
         "• Exports benchmarks to live_c_benchmarks.csv",
         1.8, 1.48, '#EAF2F8', '#2980B9'),
    ]

    for i in range(len(stages_server)):
        text, y, h, bg, border = stages_server[i]
        draw_rounded_box(ax2, text, 5.0, y, 9.2, h, bg=bg, border=border, fontsize=12.2)
        if i < len(stages_server) - 1:
            next_y = stages_server[i+1][1]
            draw_arrow_connector(ax2, 5.0, y - h/2 - 0.04, 5.0, next_y + stages_server[i+1][2]/2 + 0.04, lw=2.4)

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_code_workflow.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name} (enlarged font sizes: title=16.0pt, boxes=12.2pt)")

def main():
    print("==================================================================")
    print("  Generating Publication-Grade CSMA Diagrams & Flowcharts         ")
    print("==================================================================")
    create_system_architecture_diagram()
    create_csma_flowcharts()
    create_csmacd_detailed_flowchart()
    create_code_workflow_diagram()
    print("\n[+] All active publication diagrams regenerated successfully!")

if __name__ == "__main__":
    main()
