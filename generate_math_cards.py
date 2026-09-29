#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
generate_math_cards.py
Renders publication-grade mathematical formula cards using Matplotlib's
mathtext engine, producing clean 300-DPI images for embedding into ReportLab PDF.
==============================================================================
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHARTS_DIR = BASE_DIR / "results" / "charts"
MATH_DIR = CHARTS_DIR / "math"
MATH_DIR.mkdir(parents=True, exist_ok=True)

def render_math_card(filename, title, formula, subtext="", height=1.35):
    fig, ax = plt.subplots(figsize=(8.2, height), dpi=300)
    ax.set_xlim(0, 8.2)
    ax.set_ylim(0, height)
    ax.axis('off')

    # Card background box
    box = patches.FancyBboxPatch((0.08, 0.08), 8.04, height - 0.16,
                                 boxstyle="round,pad=0.15",
                                 facecolor='#F4F9FD', edgecolor='#2980B9', lw=1.5)
    ax.add_patch(box)

    # Title
    ax.text(4.1, height - 0.26, title.upper(), ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='#1B4F72')

    # Formula (rendered with Mathtext)
    ax.text(4.1, (height / 2.0) - 0.04, formula, ha='center', va='center',
            fontsize=12, fontweight='bold', color='#0E6251')

    # Subtext / Explanation
    if subtext:
        ax.text(4.1, 0.22, subtext, ha='center', va='center',
                fontsize=8.0, style='italic', color='#555555')

    plt.tight_layout()
    out_path = MATH_DIR / filename
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [MATH CARD] {filename}")

def main():
    print("==================================================================")
    print("  Rendering High-Resolution LaTeX Mathematical Formula Cards      ")
    print("==================================================================")

    # 1. Minimum Frame Size
    render_math_card(
        "formula_min_frame_size.png",
        "IEEE 802.3 Minimum Frame Size Constraint & Propagation Bound",
        r"$T_{fr} \geq 2 \cdot T_p \quad \Rightarrow \quad L_{\min} = 2 \cdot T_p \cdot \mathrm{Bandwidth}$",
        r"Standard Ethernet: B = 10 Mbps, Tp = 25.6 us  ===>  L_min = 10 Mbps * 51.2 us = 512 bits = 64 Bytes",
        height=1.4
    )

    # 2. Non-Persistent CSMA Throughput
    render_math_card(
        "formula_non_persistent.png",
        "Non-Persistent CSMA Throughput Formulation (Kleinrock & Tobagi, 1975)",
        r"$S_{\mathrm{non-p}} = \frac{G \cdot e^{-a \cdot G}}{G \cdot (1 + 2a) + e^{-a \cdot G}} \quad \mathrm{where} \quad a = \frac{T_p}{T_t}$",
        r"Vulnerable window is limited to normalized delay a. Prevents synchronous herd collapse under heavy load.",
        height=1.45
    )

    # 3. 1-Persistent CSMA Throughput
    render_math_card(
        "formula_one_persistent.png",
        "1-Persistent CSMA Throughput Formulation (Renewal Process Model)",
        r"$S_{\mathrm{1-p}} = \frac{G \cdot [1 + G + a G (1 + G + a G / 2)] \cdot e^{-G(1 + 2a)}}{G (1 + 2a) - (1 - e^{-a G}) + (1 + a G) e^{-G(1+a)}}$",
        r"High efficiency under light load, but exhibits steep throughput collapse for G > 1 due to herd collisions.",
        height=1.55
    )

    # 4. CSMA/CD Efficiency Formula
    render_math_card(
        "formula_csmacd_efficiency.png",
        "IEEE 802.3 CSMA/CD Channel Access Efficiency & Contention Ratio",
        r"$\mathrm{Efficiency} \ \eta = \frac{T_t}{T_t + 6.44 \cdot T_p} = \frac{1}{1 + 6.44 \cdot a} \quad \left(a = \frac{T_p}{T_t}\right)$",
        r"Contention period averages e * 2 Tp = 5.44 Tp before successful transmission + Tp propagation.",
        height=1.45
    )

    # 5. Optimal Persistence Factor
    render_math_card(
        "formula_p_optimal.png",
        "Optimal Persistence Factor Derivation in p-Persistent CSMA",
        r"$P(\mathrm{Success}) = N \cdot p \cdot (1 - p)^{N - 1} \quad \Rightarrow \quad \frac{d P}{dp} = 0 \quad \Rightarrow \quad p^* = \frac{1}{N}$",
        r"For N=3: p* = 0.33; for N=5: p* = 0.20; for N=10: p* = 0.10. Maximizes success probability to 1/e = 36.8%.",
        height=1.45
    )

    # 6. Binary Exponential Backoff
    render_math_card(
        "formula_beb_backoff.png",
        "IEEE 802.3 Truncated Binary Exponential Backoff (BEB) Mechanics",
        r"$R \in [0, \, 2^{\min(K, 10)} - 1], \quad T_B = R \times \mathrm{SlotTime}, \quad K_{\max} = 15$",
        r"Collision count K increments per attempt; aborts after 16 failed collisions with channel error.",
        height=1.45
    )

    # 7. MACAW MILD Backoff
    render_math_card(
        "formula_mild_backoff.png",
        "MACAW Multiplicative Increase Linear Decrease (MILD) Backoff",
        r"$\mathrm{Collision:} \ CW \leftarrow \min(1.5 \times CW, \, CW_{\max}) \quad | \quad \mathrm{Success:} \ CW \leftarrow \max(CW - 1, \, CW_{\min})$",
        r"Eliminates flow starvation and channel capture caused by pure BEB, maintaining high Jain's fairness index.",
        height=1.45
    )

    # 8. Wireless SINR & Dynamic Range
    render_math_card(
        "formula_wireless_sinr.png",
        "Wireless RF Dynamic Range Bound & Signal-to-Interference-plus-Noise Ratio",
        r"$\mathrm{SINR}_B^A = \frac{P_t^A / d_{AB}^\alpha}{N_0 + P_t^C / d_{CB}^\alpha} \quad \mathrm{and} \quad \frac{P_{\mathrm{local\_tx}}}{P_{\mathrm{remote\_rx}}} \approx 10^8 \quad (80 \ \mathrm{dB})$",
        r"Transmitter power overwhelms incoming collision signals by 80 dB, making CSMA/CD physically impossible in RF media.",
        height=1.5
    )

    print(f"[+] All mathematical formula cards saved in: {MATH_DIR}")

if __name__ == "__main__":
    main()
