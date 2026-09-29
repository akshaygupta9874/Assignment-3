#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
generate_diagrams.py
Generates publication-grade architectural diagrams, protocol flowcharts,
and multi-process socket workflow diagrams for the CSMA Technical Lab Report.

Engineered with:
- Strict geometric layout calculations guaranteeing zero overlapping elements.
- Generous padding, margins, and ample breathing room for all text boxes.
- 1.75x enlarged typography with high-contrast text and crisp pastel fills.
- Correct aspect ratios preventing any stretching or squishing in the PDF.
==============================================================================
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "results" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------------------
# Helper: Draw Rounded Box with Centered Text & Strict Boundary Controls
# ------------------------------------------------------------------------------
def draw_rounded_box(ax, text, x, y, w, h, bg='#EBF5FB', border='#2980B9',
                     fontsize=11.5, text_color='#111111', pad=0.12, lw=2.2, zorder=3):
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
                     fontsize=11.5, text_color='#111111', lw=2.2, zorder=3):
    pts = [[x, y + h/2], [x + w/2, y], [x, y - h/2], [x - w/2, y]]
    diamond = patches.Polygon(pts, facecolor=bg, edgecolor=border, lw=lw, zorder=zorder)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight='bold', color=text_color, zorder=zorder+1, linespacing=1.18)
    return diamond

# ------------------------------------------------------------------------------
# Helper: Draw Directional Arrow with Optional Label
# ------------------------------------------------------------------------------
def draw_arrow_connector(ax, x1, y1, x2, y2, label="", color='#2C3E50', lw=2.2,
                         label_pos=0.5, label_side='right', fontsize=11.0, label_color='#B03A2E'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=16),
                zorder=2)
    if label:
        lx = x1 + (x2 - x1) * label_pos
        ly = y1 + (y2 - y1) * label_pos
        offset_x = 0.35 if label_side == 'right' else -0.35
        ha = 'left' if label_side == 'right' else 'right'
        ax.text(lx + offset_x, ly, label, fontsize=fontsize, color=label_color,
                fontweight='bold', ha=ha, va='center', zorder=5,
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none', alpha=0.95))

# ==============================================================================
# Diagram 1: System Architecture & Emulated Shared Channel Bus
# ==============================================================================
def create_system_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.5)
    ax.axis('off')

    # Title
    ax.text(8.0, 9.0, "DISTRIBUTED SYSTEM ARCHITECTURE: EMULATED SHARED BUS & STATIONS",
            ha='center', va='center', fontsize=17, fontweight='bold', color='#111111')

    # 4 Station Nodes on top (centers: 2.3, 6.1, 9.9, 13.7)
    stations = [
        ("Station 1\n(Non-Persistent)", 2.3, '#FDEDEC', '#E74C3C'),
        ("Station 2\n(1-Persistent)", 6.1, '#FEF9E7', '#F39C12'),
        ("Station 3\n(p-Persistent)", 9.9, '#E8F8F5', '#1ABC9C'),
        ("Station N\n(CSMA/CD)", 13.7, '#EAF2F8', '#2980B9'),
    ]

    for name, x, bg, border in stations:
        # Station Box: width 2.8, height 1.6 (centered at y = 7.4)
        draw_rounded_box(ax, f"{name}\nCarrier Sensing | BEB Backoff",
                         x, 7.4, 2.8, 1.6, bg=bg, border=border, fontsize=11.5, pad=0.12)

        # Drop Cable from Station (y = 6.6) to Bus (y = 4.8)
        ax.plot([x, x], [6.6, 4.8], color='#7F8C8D', lw=2.5, zorder=2)
        ax.plot(x, 4.8, 'o', color=border, markersize=10, zorder=4)

        # TCP Stream Pill Badge on cable (centered at y = 5.7)
        ax.text(x, 5.7, "TCP Stream\n(TCP_NODELAY)", ha='center', va='center',
                fontsize=10.0, fontweight='bold', color='#1B4F72',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor=border, lw=1.5, zorder=5))

    # Central Broadcast Bus (The Wire)
    # Spans x in [0.7, 15.3], y in [4.2, 4.8]
    wire = patches.Rectangle((0.7, 4.2), 14.6, 0.6, facecolor='#2B3E50', edgecolor='#1A252F', lw=2.5, zorder=3)
    ax.add_patch(wire)
    ax.text(8.0, 4.5, "EMULATED SHARED PHYSICAL BROADCAST BUS (COAXIAL WIRE / TWISTED PAIR)",
            ha='center', va='center', color='white', fontsize=13.0, fontweight='bold', zorder=4)

    # Bi-directional Arrow between Bus (y = 4.2) and Channel Server (y = 3.25)
    ax.annotate('', xy=(8.0, 3.25), xytext=(8.0, 4.2),
                arrowprops=dict(arrowstyle="<->", color='#2980B9', lw=2.8), zorder=4)

    # Badge on arrow: centered at y = 3.72
    ax.text(8.0, 3.72, "Physical Line State & Voltage Monitoring",
            fontsize=11.0, color='#1B4F72', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.22", facecolor='#FFFFFF', edgecolor='#2980B9', lw=1.5, zorder=5))

    # Bottom layout: THREE CARDS WITH STRICT ZERO OVERLAP
    # Left Card: x in [0.7, 3.55] -> center x = 2.125, width = 2.85
    # Center Card: x in [3.95, 12.05] -> center x = 8.0, width = 8.1
    # Right Card: x in [12.45, 15.3] -> center x = 13.875, width = 2.85
    left_callout = (
        "INDEPENDENT PROCESSES\n\n"
        "• Each station runs as a\n"
        "  distinct Linux OS process.\n"
        "• Preemptive kernel scheduling\n"
        "  governs true concurrency.\n"
        "• Fully decoupled address space."
    )
    draw_rounded_box(ax, left_callout, 2.15, 1.65, 2.8, 2.65, bg='#F8F9F9', border='#BDC3C7',
                     fontsize=10.5, text_color='#333333', pad=0.12)

    srv_text = (
        "CHANNEL EMULATOR & RECEIVER SINK (channel_server)\n\n"
        "• Shared Channel State Machine: [ IDLE (0.0V)  |  BUSY (1.0V)  |  COLLISION (>= 2.0V) ]\n"
        "• Electrical Voltage Superposition: V_wire = Sum(Active Transmissions) * 1.0V\n"
        "• Propagation Delay Simulation: Tau = Tp = 1.0 ms across broadcast bus\n"
        "• Asynchronous Collision Alert Dispatcher & 32-bit JAM Notification Engine\n"
        "• IEEE 802.3 Frame FCS (CRC-32) Integrity Verification & Delivery Statistics Counter"
    )
    draw_rounded_box(ax, srv_text, 8.0, 1.65, 8.0, 2.65, bg='#EBF5FB', border='#2980B9',
                     fontsize=11.0, text_color='#1A5276', pad=0.12)

    right_callout = (
        "ZERO-LATENCY TRANSPORT\n\n"
        "• TCP_NODELAY disables\n"
        "  Nagle's buffering algorithm.\n"
        "• Immediate loopback delivery\n"
        "  at microsecond resolution.\n"
        "• Exact-byte framing (64B MAC)."
    )
    draw_rounded_box(ax, right_callout, 13.85, 1.65, 2.8, 2.65, bg='#F8F9F9', border='#BDC3C7',
                     fontsize=10.5, text_color='#333333', pad=0.12)

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_system_architecture.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 2: Comparative CSMA Protocol Workflows (4 Columns, Generous Geometry)
# ==============================================================================
def create_csma_flowcharts():
    fig, axes = plt.subplots(1, 4, figsize=(22, 12), dpi=300)
    for ax in axes:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 15)
        ax.axis('off')

    # Common dimensions: boxes width 6.4 centered at 5.0 -> x in [1.8, 8.2]
    # Corridors: left [0.2, 1.7], right [8.3, 9.8]

    # 1. Non-Persistent CSMA
    ax = axes[0]
    ax.text(5, 14.4, "Non-Persistent CSMA", ha='center', fontsize=15.5, fontweight='bold', color='#C0392B')
    draw_rounded_box(ax, "Packet Ready for TX", 5, 13.2, 6.4, 1.05, bg='#FDEDEC', border='#E74C3C', fontsize=12.0)
    draw_arrow_connector(ax, 5, 12.67, 5, 11.85)

    draw_rounded_box(ax, "Sense Channel\n(Energy == 0.0V ?)", 5, 11.2, 6.4, 1.3, bg='#FEF9E7', border='#F39C12', fontsize=11.5)
    draw_arrow_connector(ax, 5, 10.55, 5, 9.45, label="Idle", label_side='left', fontsize=11.0, label_color='#27AE60')

    draw_rounded_box(ax, "Transmit Frame\nImmediately", 5, 8.8, 6.4, 1.25, bg='#E8F8F5', border='#27AE60', fontsize=11.5)
    draw_arrow_connector(ax, 5, 8.17, 5, 7.25)

    draw_rounded_box(ax, "Transmission Result:\nCollision or Clean ACK?", 5, 6.6, 6.4, 1.25, bg='#FADBD8', border='#E74C3C', fontsize=11.5)

    # Success branch (down)
    draw_arrow_connector(ax, 5, 5.97, 5, 4.75, label="ACK", label_side='left', fontsize=11.0, label_color='#27AE60')
    draw_rounded_box(ax, "Frame Delivered\n(Success!)", 5, 4.1, 6.4, 1.1, bg='#D5F5E3', border='#2ECC71', fontsize=11.5)

    # Backoff box at bottom
    draw_rounded_box(ax, "Wait Random Backoff\nInterval (Deference)", 5, 1.8, 6.4, 1.3, bg='#FDEDEC', border='#E74C3C', fontsize=11.5)

    # Busy branch from Sense Channel (out right to x=9.2, down to y=1.8, in to backoff)
    ax.plot([8.2, 9.2, 9.2, 8.2], [11.2, 11.2, 1.8, 1.8], color='#C0392B', lw=2.0, zorder=2)
    ax.annotate('', xy=(8.2, 1.8), xytext=(8.5, 1.8),
                arrowprops=dict(arrowstyle="-|>", color='#C0392B', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(9.2, 6.5, "Busy", fontsize=11.0, color='#C0392B', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # Collision branch from Result (out left to x=1.1, down to y=2.1, in to backoff)
    ax.plot([1.8, 1.1, 1.1, 1.8], [6.6, 6.6, 2.1, 2.1], color='#C0392B', lw=2.0, zorder=2)
    ax.annotate('', xy=(1.8, 2.1), xytext=(1.5, 2.1),
                arrowprops=dict(arrowstyle="-|>", color='#C0392B', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(1.1, 4.4, "Collision", fontsize=11.0, color='#C0392B', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # Re-sense loop from Backoff bottom (y=1.15) down to y=0.4, left to x=0.5, up to y=11.2, right into Sense
    ax.plot([5.0, 5.0, 0.5, 0.5, 1.8], [1.15, 0.4, 0.4, 11.2, 11.2], color='#2980B9', lw=2.0, zorder=2)
    ax.annotate('', xy=(1.8, 11.2), xytext=(1.5, 11.2),
                arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(0.5, 8.8, "Retry Sense", fontsize=10.5, color='#2980B9', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    # 2. 1-Persistent CSMA
    ax = axes[1]
    ax.text(5, 14.4, "1-Persistent CSMA", ha='center', fontsize=15.5, fontweight='bold', color='#D35400')
    draw_rounded_box(ax, "Packet Ready for TX", 5, 13.2, 6.4, 1.05, bg='#FEF9E7', border='#F39C12', fontsize=12.0)
    draw_arrow_connector(ax, 5, 12.67, 5, 11.85)

    draw_rounded_box(ax, "Sense Channel\n(Energy == 0.0V ?)", 5, 11.2, 6.4, 1.3, bg='#FEF9E7', border='#F39C12', fontsize=11.5)
    draw_arrow_connector(ax, 5, 10.55, 5, 9.45, label="Busy", label_side='right', fontsize=11.0)

    draw_rounded_box(ax, "Wait & Continuously\nSense Wire (Keep Listening)", 5, 8.8, 6.4, 1.3, bg='#FADBD8', border='#E74C3C', fontsize=11.5)
    draw_arrow_connector(ax, 5, 8.15, 5, 7.05, label="Idle Now", label_side='right', fontsize=11.0, label_color='#27AE60')

    draw_rounded_box(ax, "Transmit Frame Immediately\n(Probability p = 1.0)", 5, 6.4, 6.4, 1.3, bg='#E8F8F5', border='#27AE60', fontsize=11.5)
    draw_arrow_connector(ax, 5, 5.75, 5, 4.75)

    draw_rounded_box(ax, "Collision Detected?\n(Severe Herd Collision Risk!)", 5, 4.1, 6.4, 1.3, bg='#FDEDEC', border='#E74C3C', fontsize=11.5)
    draw_arrow_connector(ax, 5, 3.45, 5, 2.45, label="Yes (Collision)", label_side='right', fontsize=11.0)

    draw_rounded_box(ax, "Truncated BEB Backoff\n& Reschedule Transmission", 5, 1.8, 6.4, 1.3, bg='#FCF3CF', border='#F1C40F', fontsize=11.5)

    # Feedback loop: from left of BEB backoff up to Sense Channel
    ax.plot([1.8, 0.6, 0.6, 1.8], [1.8, 1.8, 11.2, 11.2], color='#D35400', lw=2.0, zorder=2)
    ax.annotate('', xy=(1.8, 11.2), xytext=(1.5, 11.2),
                arrowprops=dict(arrowstyle="-|>", color='#D35400', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(0.6, 6.5, "Retry Sense", fontsize=10.5, color='#D35400', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    # 3. p-Persistent CSMA
    ax = axes[2]
    ax.text(5, 14.4, "p-Persistent CSMA", ha='center', fontsize=15.5, fontweight='bold', color='#2980B9')
    draw_rounded_box(ax, "Packet Ready (Slotted)", 5, 13.2, 6.4, 1.05, bg='#EBF5FB', border='#2980B9', fontsize=12.0)
    draw_arrow_connector(ax, 5, 12.67, 5, 11.85)

    draw_rounded_box(ax, "Channel Idle in Slot?\n(Sense wire at slot start)", 5, 11.2, 6.4, 1.3, bg='#EBF5FB', border='#2980B9', fontsize=11.5)
    draw_arrow_connector(ax, 5, 10.55, 5, 9.47, label="Idle", label_side='right', fontsize=11.0, label_color='#27AE60')

    draw_rounded_box(ax, "Roll Biased Variable:\nRoll x <= p ? (Optimal p* = 1/N)", 5, 8.8, 6.4, 1.35, bg='#FCF3CF', border='#F1C40F', fontsize=11.5)

    # Prob p -> Transmit
    draw_arrow_connector(ax, 5, 8.12, 5, 7.05, label="Prob p", label_side='left', fontsize=11.0, label_color='#27AE60')
    draw_rounded_box(ax, "Transmit Frame\nin Current Time Slot", 5, 6.4, 6.4, 1.3, bg='#E8F8F5', border='#27AE60', fontsize=11.5)

    # Prob 1-p -> Defer (exit right to x=9.2, down to y=4.1, into Defer box)
    draw_rounded_box(ax, "Defer 1 Slot (Prob 1 - p)\nSense Channel in Next Slot", 5, 4.1, 6.4, 1.3, bg='#EBF5FB', border='#2980B9', fontsize=11.5)
    ax.plot([8.2, 9.2, 9.2, 8.2], [8.8, 8.8, 4.1, 4.1], color='#2980B9', lw=2.0, zorder=2)
    ax.annotate('', xy=(8.2, 4.1), xytext=(8.5, 4.1),
                arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(9.2, 6.45, "1 - p", fontsize=11.0, color='#2980B9', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    draw_arrow_connector(ax, 5, 3.45, 5, 2.45)
    draw_rounded_box(ax, "If Busy -> Enter Backoff\nIf Idle -> Roll Coin Again", 5, 1.8, 6.4, 1.3, bg='#FEF9E7', border='#F39C12', fontsize=11.5)

    # Feedback loop: from bottom (y=1.15) down to y=0.4, left to x=0.6, up to y=11.2, right into Sense
    ax.plot([5.0, 5.0, 0.6, 0.6, 1.8], [1.15, 0.4, 0.4, 11.2, 11.2], color='#2980B9', lw=2.0, zorder=2)
    ax.annotate('', xy=(1.8, 11.2), xytext=(1.5, 11.2),
                arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(0.6, 6.5, "Next Slot\nSense", fontsize=9.5, color='#2980B9', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    # 4. CSMA/CD (IEEE 802.3)
    ax = axes[3]
    ax.text(5, 14.4, "CSMA/CD (IEEE 802.3)", ha='center', fontsize=15.5, fontweight='bold', color='#27AE60')
    draw_rounded_box(ax, "Packet Ready (K = 0)", 5, 13.2, 6.4, 1.05, bg='#E8F8F5', border='#27AE60', fontsize=12.0)
    draw_arrow_connector(ax, 5, 12.67, 5, 11.85)

    draw_rounded_box(ax, "Sense Wire (1-Persistent)\nWait until Line is IDLE", 5, 11.2, 6.4, 1.3, bg='#E8F8F5', border='#27AE60', fontsize=11.5)
    draw_arrow_connector(ax, 5, 10.55, 5, 9.47, label="Idle", label_side='right', fontsize=11.0, label_color='#27AE60')

    # Busy loop on wire (enters cleanly into Box 2 right edge)
    ax.plot([8.2, 9.2, 9.2, 8.2], [11.0, 11.0, 11.6, 11.6], color='#E74C3C', lw=2.0, zorder=2)
    ax.annotate('', xy=(8.2, 11.6), xytext=(8.5, 11.6),
                arrowprops=dict(arrowstyle="-|>", color='#E74C3C', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(9.25, 11.3, "Busy", fontsize=10.5, color='#C0392B', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    draw_rounded_box(ax, "Wait IFG & Transmit Frame\n('Listen-While-Talk' Active)", 5, 8.8, 6.4, 1.35, bg='#D4EFDF', border='#229954', fontsize=11.5)
    draw_arrow_connector(ax, 5, 8.12, 5, 7.05)

    draw_rounded_box(ax, "Collision Detected on Wire?\n(Energy >= 2.0V or JAM alert)", 5, 6.4, 6.4, 1.3, bg='#FDEDEC', border='#E74C3C', fontsize=11.5)
    draw_arrow_connector(ax, 5, 5.75, 5, 4.80, label="Yes", label_side='right', fontsize=11.0, label_color='#C0392B')

    draw_rounded_box(ax, "ABORT Frame Immediately!\nEmit 32-bit JAM (0x55555555)\nIncrement Counter: K = K + 1", 5, 4.1, 6.4, 1.4, bg='#FADBD8', border='#C0392B', fontsize=11.0)
    draw_arrow_connector(ax, 5, 3.40, 5, 2.47)

    draw_rounded_box(ax, "Truncated BEB Backoff:\nR in [0, 2^min(K,10) - 1]\nWait R * SlotTime (2*Tp)", 5, 1.8, 6.4, 1.35, bg='#FCF3CF', border='#F1C40F', fontsize=11.5)

    # Feedback loop: from left of BEB backoff up to Sense Wire
    ax.plot([1.8, 0.6, 0.6, 1.8], [1.8, 1.8, 11.2, 11.2], color='#27AE60', lw=2.0, zorder=2)
    ax.annotate('', xy=(1.8, 11.2), xytext=(1.5, 11.2),
                arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.0, mutation_scale=14), zorder=2)
    ax.text(0.6, 6.5, "Retry Sense", fontsize=10.5, color='#27AE60', fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    plt.suptitle("COMPARATIVE FINITE STATE WORKFLOWS OF CSMA PROTOCOL FAMILIES",
                 fontsize=17, fontweight='bold', y=0.98)
    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_csma_fsm_workflows.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 3: Space-Time Vulnerable Period & Tri-State Waveform
# ==============================================================================
def create_vulnerable_period_and_energy_diagram():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8), dpi=300)

    # (A) Space-Time Model
    ax1.set_xlim(0, 12)
    ax1.set_ylim(0, 7.5)
    ax1.axis('off')
    ax1.set_title('(A) Space-Time Model: Vulnerable Period (Tau = Tp)', fontsize=15, fontweight='bold', pad=14)

    # Timelines for Station A (x = 2.5) and Station B (x = 8.8) ending cleanly above bottom callout
    ax1.plot([2.5, 2.5], [1.9, 6.3], 'k-', lw=2.5)
    ax1.plot([8.8, 8.8], [1.9, 6.3], 'k-', lw=2.5)
    ax1.text(2.5, 6.7, "Station A (Sender 1)", ha='center', fontweight='bold', fontsize=13.5, color='#1B4F72')
    ax1.text(8.8, 6.7, "Station B (Contender)", ha='center', fontweight='bold', fontsize=13.5, color='#900C3F')

    # Station A transmission cone
    poly_a = patches.Polygon([[2.5, 5.6], [8.8, 3.8], [8.8, 2.0], [2.5, 3.8]],
                             facecolor='#AED6F1', edgecolor='#2980B9', alpha=0.45, lw=2.2)
    ax1.add_patch(poly_a)
    ax1.text(3.0, 4.4, "Signal A propagating across wire (v = 200 m/us)", fontsize=10.0, color='#1B4F72',
             fontweight='bold', rotation=-16, ha='left')

    # Collision Region (Signal B begins at t < Tp, e.g. y = 4.7)
    col_poly = patches.Polygon([[6.0, 3.8], [8.8, 3.0], [8.8, 2.0], [6.0, 2.8]],
                               facecolor='#FADBD8', edgecolor='#E74C3C', alpha=0.75, lw=2.2)
    ax1.add_patch(col_poly)
    ax1.plot(6.2, 3.3, '*', color='#C0392B', markersize=24, zorder=5)
    ax1.annotate('Collision Point', xy=(6.2, 3.5), xytext=(4.8, 4.2),
                 arrowprops=dict(arrowstyle="->", color='#C0392B', lw=2.0),
                 fontsize=11.0, color='#900C3F', fontweight='bold', va='center',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='#FDEDEC', edgecolor='#C0392B', lw=1.2))

    # Collision label with callout box placed comfortably below timeline line ends
    ax1.text(5.65, 0.9, "DESTRUCTIVE COLLISION ON PHYSICAL WIRE!\nSignals overlap destructively due to non-zero propagation delay Tau (Tp)",
             fontsize=11.0, color='#922B21', fontweight='bold', ha='center', va='center',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#FDEDEC', edgecolor='#C0392B', lw=1.4))

    # Vulnerable Window on Station B timeline
    ax1.annotate('', xy=(8.8, 3.8), xytext=(8.8, 5.6),
                 arrowprops=dict(arrowstyle="<->", color='#C0392B', lw=2.5))
    ax1.text(10.3, 4.7, "Vulnerable Window\nDuration = Tau = Tp\nAny TX in this window\nguarantees collision!",
             fontsize=11.0, color='#C0392B', fontweight='bold', va='center', ha='center',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#FDEDEC', edgecolor='#E74C3C', lw=1.2))

    ax1.text(8.6, 2.45, "Signal B begins at t < Tp\n(Medium perceived idle!)", fontsize=10.5, color='#78281F',
             ha='right', bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#E74C3C', lw=1.0))

    # (B) Tri-State Energy Level Superposition Waveform
    ax2.set_xlim(0, 10)
    ax2.set_ylim(-0.3, 4.5)
    ax2.set_title('(B) Channel Energy Level During Transmission & Collision', fontsize=15, fontweight='bold', pad=14)
    ax2.set_xlabel('Time Progression (ms)', fontsize=12.5, fontweight='bold')
    ax2.set_ylabel('Detected Line Voltage (V)', fontsize=12.5, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.7)

    t = [0, 1.2, 1.2, 3.5, 3.5, 4.0, 4.0, 6.2, 6.2, 7.5, 7.5, 9.2, 9.2, 10]
    v = [0, 0,   1.0, 1.0, 0,   0,   2.2, 2.2, 0,   0,   1.0, 1.0, 0,   0]
    ax2.step(t, v, where='post', color='#2980B9', lw=2.8)

    ax2.axhline(0.0, color='#7F8C8D', linestyle=':', lw=1.5)
    ax2.axhline(1.0, color='#27AE60', linestyle='--', lw=1.6, label='Normal Line Voltage: Single TX (1.0V)')
    ax2.axhline(2.0, color='#C0392B', linestyle='--', lw=1.6, label='Collision Threshold: Multi-TX (>= 2.0V)')

    ax2.text(2.35, 1.25, "Clean Single TX\n(State: BUSY)", fontsize=11.0, color='#27AE60', fontweight='bold', ha='center')
    ax2.text(5.1, 2.50, "COLLISION DETECTED!\nEnergy Superposition (2.2V)", fontsize=11.0, color='#C0392B', fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#FDEDEC', edgecolor='#E74C3C', lw=1.2))
    ax2.text(8.35, 1.25, "Retransmission\n(State: BUSY)", fontsize=11.0, color='#2980B9', fontweight='bold', ha='center')

    ax2.legend(loc='upper right', fontsize=11)

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_vulnerable_period_and_energy.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 4: Wireless Hidden/Exposed Terminals & MACA RTS/CTS
# ==============================================================================
def create_wireless_maca_diagram():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9), dpi=300)

    # (A) Hidden Terminal Problem (Strictly isotropic equal scaling for perfect circles)
    ax1.set_xlim(0, 12)
    ax1.set_ylim(0, 9.2)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('(A) Why CSMA/CD Fails in Wireless: Hidden Terminal', fontsize=15, fontweight='bold', pad=14)

    # Node positions: A at x=3.2, B at x=6.0, C at x=8.8 (y=5.2)
    ax1.plot(3.2, 5.2, 'o', color='#2980B9', markersize=16, zorder=5)
    ax1.text(3.2, 5.85, "Node A\n(Sender 1)", ha='center', fontweight='bold', fontsize=12.5, color='#1B4F72')

    ax1.plot(6.0, 5.2, 's', color='#27AE60', markersize=16, zorder=5)
    ax1.text(6.0, 5.85, "Node B\n(Receiver AP)", ha='center', fontweight='bold', fontsize=12.5, color='#145A32')

    ax1.plot(8.8, 5.2, 'o', color='#E74C3C', markersize=16, zorder=5)
    ax1.text(8.8, 5.85, "Node C\n(Hidden Sender)", ha='center', fontweight='bold', fontsize=12.5, color='#900C3F')

    # Coverage circles: radius 2.8 (Touches receiver B at 6.0, strictly non-overlapping with counterpart)
    circ_a = patches.Circle((3.2, 5.2), 2.8, facecolor='#AED6F1', edgecolor='#2980B9', alpha=0.25, lw=1.8)
    circ_c = patches.Circle((8.8, 5.2), 2.8, facecolor='#FADBD8', edgecolor='#E74C3C', alpha=0.25, lw=1.8)
    ax1.add_patch(circ_a)
    ax1.add_patch(circ_c)

    # Transmission arrows
    ax1.annotate('', xy=(5.5, 5.2), xytext=(3.6, 5.2),
                 arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.8, mutation_scale=14), zorder=4)
    ax1.text(4.4, 4.65, "A transmits to B", fontsize=11.0, color='#1B4F72', fontweight='bold', ha='center')

    ax1.annotate('', xy=(6.5, 5.2), xytext=(8.4, 5.2),
                 arrowprops=dict(arrowstyle="-|>", color='#E74C3C', lw=2.8, mutation_scale=14), zorder=4)
    ax1.text(7.6, 4.65, "C senses idle wire\n& transmits to B", fontsize=11.0, color='#900C3F', fontweight='bold', ha='center')

    # Collision Star at Node B
    ax1.plot(6.0, 5.2, '*', color='#C0392B', markersize=24, zorder=6)

    # Collision Box placed comfortably below with zero intersection
    ax1.text(6.0, 2.0, "DESTRUCTIVE COLLISION AT RECEIVER B!\nNode A and Node C are hidden terminals outside each other's radio range.\nPhysical carrier sensing at A or C fails to detect collision at B!",
             ha='center', fontsize=11.0, fontweight='bold', color='#922B21',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#FADBD8', edgecolor='#C0392B', lw=1.5))

    # Radio range badges at bottom
    ax1.text(3.2, 0.7, "Node A Radio Range\n(Reaches B, cannot reach C)", ha='center', fontsize=10.0, color='#1B4F72',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#2980B9', lw=1.2))
    ax1.text(8.8, 0.7, "Node C Radio Range\n(Reaches B, cannot reach A)", ha='center', fontsize=10.0, color='#78281F',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#E74C3C', lw=1.2))

    # (B) MACA RTS/CTS Solution with NAV (Strictly proportioned and linked)
    ax2.set_xlim(0, 12)
    ax2.set_ylim(0, 9.2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('(B) MACA RTS/CTS Handshake with NAV Deferral', fontsize=15, fontweight='bold', pad=14)

    # Timelines for A (x=2.0), B (x=5.5), C (x=8.5)
    ax2.plot([2.0, 2.0], [0.8, 7.8], 'k-', lw=2.2)
    ax2.text(2.0, 8.2, "Station A", ha='center', fontweight='bold', color='#2980B9', fontsize=13)

    ax2.plot([5.5, 5.5], [0.8, 7.8], 'k-', lw=2.2)
    ax2.text(5.5, 8.2, "Station B", ha='center', fontweight='bold', color='#27AE60', fontsize=13)

    ax2.plot([8.5, 8.5], [0.8, 7.8], 'k-', lw=2.2)
    ax2.text(8.5, 8.2, "Station C", ha='center', fontweight='bold', color='#E74C3C', fontsize=13)

    # 1. RTS from A to B
    ax2.annotate('', xy=(5.4, 6.7), xytext=(2.1, 7.1),
                 arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.5, mutation_scale=14))
    ax2.text(3.7, 7.15, "1. RTS (Request-To-Send)", fontsize=11.0, color='#2980B9', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # 2. CTS from B to A and overheard by C
    ax2.annotate('', xy=(2.1, 5.5), xytext=(5.4, 5.8),
                 arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.5, mutation_scale=14))
    ax2.annotate('', xy=(8.4, 5.5), xytext=(5.6, 5.8),
                 arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.5, linestyle='--', mutation_scale=14))
    ax2.text(3.7, 5.85, "2. CTS (Clear-To-Send)", fontsize=11.0, color='#27AE60', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))
    ax2.text(7.0, 5.85, "CTS Overheard", fontsize=11.0, color='#27AE60', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # Station C sets NAV (Network Allocation Vector)
    nav_box = patches.Rectangle((8.35, 1.6), 0.3, 3.9, facecolor='#FDEDEC', edgecolor='#E74C3C', lw=1.8, zorder=3)
    ax2.add_patch(nav_box)
    ax2.text(10.4, 3.55, "NAV Active:\nStation C Defers TX\n(Duration = SIFS +\nDATA + ACK)",
             fontsize=10.5, color='#C0392B', fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FDEDEC', edgecolor='#E74C3C', lw=1.2))
    # Explicit indicator arrow from NAV callout to NAV box
    ax2.annotate('', xy=(8.7, 3.55), xytext=(9.4, 3.55),
                 arrowprops=dict(arrowstyle="-|>", color='#C0392B', lw=2.2, mutation_scale=14))

    # 3. DATA Frame from A to B
    ax2.annotate('', xy=(5.4, 3.7), xytext=(2.1, 4.3),
                 arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.8, mutation_scale=15))
    ax2.text(3.7, 4.2, "3. DATA Frame (Collision-Free)", fontsize=11.0, color='#2980B9', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # 4. ACK from B to A
    ax2.annotate('', xy=(2.1, 1.8), xytext=(5.4, 2.3),
                 arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.5, mutation_scale=14))
    ax2.text(3.7, 2.3, "4. ACK Delivery Confirmation", fontsize=11.0, color='#27AE60', fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_wireless_hidden_exposed_maca.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 5: Comprehensive CSMA/CD FSM & Collision Timeline
# ==============================================================================
def create_csmacd_detailed_flowchart():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 13), dpi=300, gridspec_kw={'width_ratios': [1.15, 1.0]})

    # (A) IEEE 802.3 CSMA/CD Flowchart (Strict bottom padding: ylim -0.6 to 16.5)
    ax1.set_xlim(0, 12)
    ax1.set_ylim(-0.6, 16.5)
    ax1.axis('off')
    ax1.set_title('(A) IEEE 802.3 CSMA/CD Algorithmic Flowchart', fontsize=16, fontweight='bold', color='#1B4F72', pad=14)

    # Central axis at x = 6.2
    # Step 1: Initialize
    draw_rounded_box(ax1, "Frame Ready for Transmission:\nInitialize Collision Counter: K = 0",
                     6.2, 15.2, 7.6, 1.0, bg='#E8F8F5', border='#27AE60', fontsize=12.0)
    draw_arrow_connector(ax1, 6.2, 14.7, 6.2, 13.95)

    # Step 2: Sense Channel (Diamond)
    draw_diamond_box(ax1, "Sense Channel State\n(Energy Level == 0.0V ?)",
                     6.2, 13.2, 7.6, 1.4, bg='#FEF9E7', border='#F39C12', fontsize=11.5)
    draw_arrow_connector(ax1, 6.2, 12.5, 6.2, 11.55, label="Idle", label_side='right', fontsize=11.0, label_color='#27AE60')

    # Busy 1-P loop: exit right (x=10.0), loop up to 14.4, back to sense
    ax1.plot([10.0, 11.0, 11.0, 10.0], [13.2, 13.2, 14.4, 14.4], color='#E74C3C', lw=2.0, zorder=2)
    ax1.annotate('', xy=(10.0, 14.4), xytext=(10.3, 14.4),
                 arrowprops=dict(arrowstyle="-|>", color='#E74C3C', lw=2.0, mutation_scale=14), zorder=2)
    ax1.text(11.0, 13.8, "Busy: Wait &\nKeep Sensing", fontsize=10.5, color='#C0392B', fontweight='bold', ha='left', va='center',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    # Step 3: Wait IFG & Transmit
    draw_rounded_box(ax1, "Wait Inter-Frame Gap (96 bits / IFG)\nBegin Transmitting Frame via TCP Stream",
                     6.2, 10.8, 7.6, 1.25, bg='#EBF5FB', border='#2980B9', fontsize=11.5)
    draw_arrow_connector(ax1, 6.2, 10.15, 6.2, 9.40)

    # Step 4: Listen-While-Talk
    draw_rounded_box(ax1, "Listen-While-Talk Mode:\nContinuously Monitor Socket for Collision Alert",
                     6.2, 8.7, 7.6, 1.25, bg='#D4EFDF', border='#229954', fontsize=11.5)
    draw_arrow_connector(ax1, 6.2, 8.05, 6.2, 7.35)

    # Step 5: Collision Detected? (Diamond)
    draw_diamond_box(ax1, "Collision Detected on Wire?\n(Energy >= 2.0V or Alert Received)",
                     6.2, 6.6, 7.8, 1.4, bg='#FDEDEC', border='#E74C3C', fontsize=11.5)

    # Branch: Clean Success (Left side: x = 2.2)
    ax1.plot([2.3, 2.3], [6.6, 5.25], color='#27AE60', lw=2.2, zorder=2)
    ax1.annotate('', xy=(2.3, 5.25), xytext=(2.3, 5.5),
                 arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.2, mutation_scale=15), zorder=2)
    ax1.text(3.3, 6.6, "No (Clean)", fontsize=11.0, color='#27AE60', fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.18", facecolor='white', edgecolor='none'))

    draw_rounded_box(ax1, "Clean Transmission!\nSuccess (T = 2*Tp)\nReset K = 0\nFrame Delivered",
                     2.2, 4.3, 3.0, 1.8, bg='#D5F5E3', border='#2ECC71', fontsize=11.0)

    # Branch: Collision (Right side: x = 7.8)
    draw_arrow_connector(ax1, 6.2, 5.9, 7.8, 5.1, label="Yes (Collision)", label_side='right', fontsize=11.0, label_color='#C0392B')
    draw_rounded_box(ax1, "ABORT Frame Immediately!\nEmit 32-bit JAM (0x55555555)\nCollision Counter: K = K + 1",
                     7.8, 4.3, 4.8, 1.5, bg='#FADBD8', border='#C0392B', fontsize=11.0)

    # Retries check (K > 15 ?)
    draw_arrow_connector(ax1, 7.8, 3.55, 7.8, 2.75)
    draw_diamond_box(ax1, "K > 15 ?\n(Max 16 retries)", 7.8, 2.1, 4.4, 1.2, bg='#FCF3CF', border='#F1C40F', fontsize=11.0)

    # Excessive collisions -> Drop Frame (right)
    ax1.plot([10.0, 11.0, 11.0], [2.1, 2.1, 1.4], color='#C0392B', lw=2.0, zorder=2)
    ax1.annotate('', xy=(11.0, 1.4), xytext=(11.0, 1.6),
                 arrowprops=dict(arrowstyle="-|>", color='#C0392B', lw=2.0, mutation_scale=14), zorder=2)
    ax1.text(10.5, 2.3, "Yes", fontsize=11.0, color='#C0392B', fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))
    draw_rounded_box(ax1, "Drop Frame:\nExcess Collisions", 11.0, 0.85, 1.8, 1.0, bg='#FDEDEC', border='#E74C3C', fontsize=10.0)

    # Truncated BEB (down/left to center 5.0, y=0.65, ample padding from -0.6)
    ax1.plot([5.6, 5.0, 5.0], [2.1, 2.1, 1.25], color='#27AE60', lw=2.2, zorder=2)
    ax1.annotate('', xy=(5.0, 1.25), xytext=(5.0, 1.45),
                 arrowprops=dict(arrowstyle="-|>", color='#27AE60', lw=2.2, mutation_scale=14), zorder=2)
    ax1.text(5.3, 2.3, "No", fontsize=11.0, color='#27AE60', fontweight='bold', ha='center', va='center',
             bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))
    draw_rounded_box(ax1, "Truncated BEB: Slot Range M = min(K, 10)\nDraw R in [0, 2^M - 1]  -->  Wait R * 2*Tp",
                     5.0, 0.65, 6.8, 1.15, bg='#FCF3CF', border='#F1C40F', fontsize=10.5)

    # Loop back from BEB (x=1.6) -> left corridor x=0.6 -> up to y=13.2 -> into Sense Channel (x=2.4)
    ax1.plot([1.6, 0.6, 0.6, 2.4], [0.65, 0.65, 13.2, 13.2], color='#2980B9', lw=2.0, zorder=2)
    ax1.annotate('', xy=(2.4, 13.2), xytext=(2.1, 13.2),
                 arrowprops=dict(arrowstyle="-|>", color='#2980B9', lw=2.0, mutation_scale=14), zorder=2)
    ax1.text(0.6, 8.7, "Wait Backoff &\nRetry Carrier Sense", fontsize=10.5, color='#1B4F72', fontweight='bold',
             rotation=90, va='center', ha='center', bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#2980B9'))

    # (B) Space-Time Collision Timeline (Strict geometric intersection)
    ax2.set_xlim(0, 12)
    ax2.set_ylim(-0.6, 16.5)
    ax2.axis('off')
    ax2.set_title('(B) Space-Time Timeline: Collision & 32-bit Jam Signal', fontsize=16, fontweight='bold', color='#1B4F72', pad=14)

    # Station vertical timelines (Station A at x=2.8, Station B at x=8.8)
    ax2.plot([2.8, 2.8], [0.5, 15.0], 'k-', lw=2.5)
    ax2.plot([8.8, 8.8], [0.5, 15.0], 'k-', lw=2.5)
    ax2.text(2.8, 15.5, "Station A\n(Sender 1)", ha='center', fontweight='bold', color='#2980B9', fontsize=13.5)
    ax2.text(8.8, 15.5, "Station B\n(Sender 2)", ha='center', fontweight='bold', color='#E74C3C', fontsize=13.5)

    # Time axis (Left side: x = 0.8)
    ax2.annotate('', xy=(0.8, 0.5), xytext=(0.8, 15.0),
                 arrowprops=dict(arrowstyle="->", color='#333333', lw=2.2))
    ax2.text(0.4, 7.8, "Time (t) Progression --->", rotation=90, fontsize=12.0, fontweight='bold', color='#333333', ha='center')

    # Event 0: Station A begins transmission at t = 0 (y = 14.5)
    ax2.plot(2.8, 14.5, 'o', color='#2980B9', markersize=12, zorder=5)
    ax2.text(2.55, 14.5, "t0: A begins TX", ha='right', va='center', fontsize=11.0, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#EBF5FB', edgecolor='#2980B9'))

    # Signal A wavefront line toward B: slope = (10.9 - 14.5) / (8.8 - 2.8) = -0.6
    ax2.plot([2.8, 8.8], [14.5, 10.9], color='#2980B9', lw=2.5)
    ax2.text(5.8, 13.1, "Wavefront A propagates (v = 200 m/us)", fontsize=10.0, color='#2980B9',
             ha='center', va='center', rotation=-22, bbox=dict(boxstyle="round,pad=0.15", facecolor='white', edgecolor='none'))

    # Event 1: Station B senses wire at t1 (y = 11.8) before wave A reaches it (10.9). Medium perceived IDLE!
    ax2.plot(8.8, 11.8, 'o', color='#E74C3C', markersize=12, zorder=5)
    ax2.text(9.1, 12.1, "t1: B senses wire\n(Appears IDLE: t < Tp)\nB begins TX", ha='left', va='center', fontsize=10.5,
             color='#C0392B', bbox=dict(boxstyle="round,pad=0.2", facecolor='#FDEDEC', edgecolor='#E74C3C'))

    # Signal B wavefront line toward A: slope = +0.6, leaves (8.8, 11.8), reaches A at (2.8, 8.2)
    ax2.plot([8.8, 2.8], [11.8, 8.2], color='#E74C3C', lw=2.5)

    # EXACT Wavefront Intersection Point:
    # 14.5 - 0.6*(x - 2.8) = 8.2 + 0.6*(x - 2.8) => 1.2*(x - 2.8) = 6.3 => x = 8.05, y = 11.35
    ax2.plot(8.05, 11.35, '*', color='#C0392B', markersize=24, zorder=6)
    ax2.text(5.0, 11.6, "COLLISION ON WIRE!\nEnergy doubles: V >= 2.0V", ha='center', va='center',
             fontsize=11.0, fontweight='bold', color='#922B21',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FADBD8', edgecolor='#C0392B'))
    ax2.annotate('', xy=(8.05, 11.35), xytext=(6.5, 11.6),
                 arrowprops=dict(arrowstyle="->", color='#C0392B', lw=1.8))

    # Event 2: Station B detects collision at y = 10.9 (when Wavefront A hits Station B)
    ax2.plot(8.8, 10.9, 's', color='#922B21', markersize=12, zorder=5)
    ax2.text(9.1, 10.2, "t2: B detects collision!\nABORTS frame TX\nEmits 32-bit JAM", ha='left', va='center',
             fontsize=10.5, color='#922B21', bbox=dict(boxstyle="round,pad=0.2", facecolor='#FADBD8', edgecolor='#922B21'))

    # Jam Signal from Station B (orange thick line)
    ax2.plot([8.8, 8.8], [10.9, 9.3], color='#F39C12', lw=5, solid_capstyle='butt')
    ax2.text(9.1, 9.1, "32-bit Jam", fontsize=10.0, color='#D35400', fontweight='bold')

    # Event 3: Station A detects collision at y = 8.2 (when Wavefront B hits Station A, Elapsed = 2*Tp)
    ax2.plot(2.8, 8.2, 's', color='#922B21', markersize=12, zorder=5)
    ax2.text(2.55, 8.2, "t3: A detects collision!\n(Elapsed = 2*Tp)\nABORTS frame TX\nEmits 32-bit JAM",
             ha='right', va='center', fontsize=10.5, color='#922B21',
             bbox=dict(boxstyle="round,pad=0.2", facecolor='#FADBD8', edgecolor='#922B21'))

    # Jam Signal from Station A (orange thick line)
    ax2.plot([2.8, 2.8], [8.2, 6.6], color='#F39C12', lw=5, solid_capstyle='butt')
    ax2.text(2.55, 6.6, "32-bit Jam", fontsize=10.0, color='#D35400', fontweight='bold', ha='right')

    # Resolution Summary Box
    ax2.text(5.8, 4.3, "Contention Period Truncated to 2*Tp + Jam Duration\nBoth Stations enter Truncated BEB Backoff\nChannel liberated for subsequent transmission attempts",
             ha='center', va='center', fontsize=11.0, fontweight='bold', color='#196F3D',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#E8F8F5', edgecolor='#27AE60', lw=1.5))

    # Critical Invariant Box
    ax2.text(5.8, 1.6, "CRITICAL ETHERNET INVARIANT: Frame Transmission Time T_fr >= 2 * T_p\nEnsures transmitter stays active long enough to hear returning collision wave!",
             ha='center', va='center', fontsize=10.5, fontweight='bold', color='#1B4F72',
             bbox=dict(boxstyle="round,pad=0.25", facecolor='#EBF5FB', edgecolor='#2980B9', lw=1.5))

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_csmacd_detailed_flowchart.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ==============================================================================
# Diagram 6: Multi-Process Socket Execution Workflow (Generous Geometry)
# ==============================================================================
def create_code_workflow_diagram():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 13), dpi=300, gridspec_kw={'width_ratios': [1.05, 1.0]})

    for ax in [ax1, ax2]:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 16.5)
        ax.axis('off')

    # (A) Station Process Pipeline (Left Column)
    ax1.set_title('(A) Station Client Process Workflow (station.c & mac_strategies.c)',
                  fontsize=15.5, fontweight='bold', color='#1B4F72', pad=14)

    draw_rounded_box(ax1, "1. Socket Initialization:\nconnect() to Channel Server on TCP port\nConfigure TCP_NODELAY (disable Nagle buffering)",
                     5, 14.3, 8.6, 1.25, bg='#E8F8F5', border='#27AE60', fontsize=11.5)
    draw_arrow_connector(ax1, 5, 13.65, 5, 12.80)

    draw_rounded_box(ax1, "2. Carrier Sensing RPC:\nSend MSG_TYPE_SENSE_REQ over stream socket\nReceive ChannelState (IDLE / BUSY) & Line Voltage",
                     5, 12.1, 8.6, 1.25, bg='#FEF9E7', border='#F39C12', fontsize=11.5)
    draw_arrow_connector(ax1, 5, 11.45, 5, 10.60)

    draw_rounded_box(ax1, "3. Multi-Strategy Persistence Policy Engine:\n• Non-P: If busy -> sleep(random backoff slots)\n• 1-P / CD: If busy -> loop until channel IDLE\n• p-P: If idle -> roll x <= p (transmit), else defer 1 slot",
                     5, 9.6, 8.8, 1.85, bg='#FCF3CF', border='#F1C40F', fontsize=11.0)
    draw_arrow_connector(ax1, 5, 8.65, 5, 7.80)

    draw_rounded_box(ax1, "4. Frame Assembly & Transmission:\nConstruct 64-Byte IEEE 802.3 MAC Frame\nCompute 32-bit FCS (CRC-32); call tcp_send_exact()",
                     5, 7.1, 8.6, 1.25, bg='#EBF5FB', border='#2980B9', fontsize=11.5)
    draw_arrow_connector(ax1, 5, 6.45, 5, 5.50)

    draw_rounded_box(ax1, "5. Listen-While-Talk Non-Blocking select() Loop:\nPoll TCP socket for MSG_TYPE_TX_COLLISION alert\nDetects multi-transmitter energy superposition instantaneously",
                     5, 4.8, 8.6, 1.25, bg='#D4EFDF', border='#229954', fontsize=11.0)
    draw_arrow_connector(ax1, 5, 4.15, 5, 3.25)

    draw_rounded_box(ax1, "6. Collision Abort, Jam & BEB Backoff:\nUpon alert: ABORT transmission immediately!\ntcp_send_exact(JAM: 0x55555555)\nDraw R in [0, 2^min(K,10) - 1] -> sleep(R * 2*Tp)",
                     5, 2.4, 8.8, 1.55, bg='#FADBD8', border='#C0392B', fontsize=11.0)

    # (B) Channel Server Coordinator Pipeline (Right Column)
    ax2.set_title('(B) Channel Server Medium Coordinator (channel_server.c)',
                  fontsize=15.5, fontweight='bold', color='#1B4F72', pad=14)

    draw_rounded_box(ax2, "1. Server Master Event Multiplexer:\nTCP listen() on coordinator port\nNon-blocking select() multiplexing up to 64 station clients",
                     5, 14.3, 8.6, 1.25, bg='#EBF5FB', border='#2980B9', fontsize=11.5)
    draw_arrow_connector(ax2, 5, 13.65, 5, 12.80)

    draw_rounded_box(ax2, "2. Handle Client Connection / SENSE RPC:\nProcess incoming MSG_TYPE_SENSE_REQ\nSimulate physical propagation delay window (Tau = Tp)\nReturn perceived IDLE (0.0V) or BUSY (1.0V) state",
                     5, 12.0, 8.8, 1.45, bg='#FEF9E7', border='#F39C12', fontsize=11.0)
    draw_arrow_connector(ax2, 5, 11.25, 5, 10.35)

    draw_rounded_box(ax2, "3. Track Active Transmissions:\nOn MSG_TYPE_TX_START: register station in active table\nIncrement active transmitters counter: g_num_active_txs++",
                     5, 9.6, 8.6, 1.25, bg='#E8F8F5', border='#27AE60', fontsize=11.5)
    draw_arrow_connector(ax2, 5, 8.95, 5, 8.10)

    draw_rounded_box(ax2, "4. Physical Voltage Superposition Meter:\ng_energy_level = g_num_active_txs * 1.0V\n• 0 transmitters: CHAN_STATE_IDLE (0.0V)\n• 1 transmitter:  CHAN_STATE_BUSY (1.0V)\n• >= 2 transmitters: CHAN_STATE_COLLISION (>= 2.0V)",
                     5, 7.0, 8.8, 1.85, bg='#FCF3CF', border='#F1C40F', fontsize=11.0)
    draw_arrow_connector(ax2, 5, 6.05, 5, 5.25)

    draw_rounded_box(ax2, "5. Collision Broadcast Engine:\nIf state == COLLISION: iterate through all active stations\nPush MSG_TYPE_TX_COLLISION alert immediately\ninto each station's dedicated TCP socket stream",
                     5, 4.4, 8.8, 1.45, bg='#FADBD8', border='#C0392B', fontsize=11.0)
    draw_arrow_connector(ax2, 5, 3.65, 5, 2.75)

    draw_rounded_box(ax2, "6. Delivery Sink & CRC-32 Frame Verification:\nFor clean transmissions: verify CRC-32 Frame Check Sequence\nUpdate global delivery statistics & dispatch ACK to sender",
                     5, 2.0, 8.6, 1.25, bg='#D5F5E3', border='#2ECC71', fontsize=11.5)

    plt.tight_layout()
    save_path = CHARTS_DIR / "diagram_code_workflow.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

if __name__ == "__main__":
    print("==================================================================")
    print("  Generating Meticulously Padded 1.75x Flowcharts & Diagrams      ")
    print("==================================================================")
    create_system_architecture_diagram()
    create_csma_flowcharts()
    create_vulnerable_period_and_energy_diagram()
    create_wireless_maca_diagram()
    create_csmacd_detailed_flowchart()
    create_code_workflow_diagram()
    print("\n[+] All 6 publication diagrams generated successfully in results/charts!")
