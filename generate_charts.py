#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
generate_charts.py
CSE/PC/B/S/314 Computer Networks Lab - Assignment 3
Publication-Grade Matplotlib Visualization Suite for CSMA MAC Protocols
Uses standard csv and numpy to be fully dependency-free (no pandas required).
==============================================================================
"""

import os
import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = RESULTS_DIR / "data"
CHARTS_DIR = RESULTS_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Styling parameters
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#222222'
plt.rcParams['axes.linewidth'] = 1.0
plt.rcParams['grid.color'] = '#dddddd'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.75
plt.rcParams['xtick.direction'] = 'out'
plt.rcParams['ytick.direction'] = 'out'

COLORS = {
    'non_persistent': '#D9534F',      # Crimson Red
    'one_persistent': '#F0AD4E',      # Amber Orange
    'p_persistent':   '#0275D8',      # Deep Blue
    'csma_cd':        '#28A745',      # Emerald Green
    'csma_ca':        '#6F42C1',      # Purple
    'pure_aloha':     '#6C757D',      # Slate Gray
    'slotted_aloha':  '#17A2B8'       # Teal
}

LABELS = {
    'non_persistent': 'Non-Persistent CSMA',
    'one_persistent': '1-Persistent CSMA',
    'p_persistent':   'p-Persistent CSMA (Best p=1/N)',
    'csma_cd':        'CSMA/CD (IEEE 802.3)',
    'csma_ca':        'CSMA/CA (IEEE 802.11 CW)'
}

MARKERS = {
    'non_persistent': 'o',
    'one_persistent': 's',
    'p_persistent':   '^',
    'csma_cd':        'D',
    'csma_ca':        'v'
}

def load_csv(path):
    rows = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            parsed = {}
            for k, v in r.items():
                try:
                    parsed[k] = float(v)
                except ValueError:
                    parsed[k] = v
            rows.append(parsed)
    return rows

# ------------------------------------------------------------------------------
# Chart 1: p-Persistent CSMA Throughput vs p (Requirement i)
# ------------------------------------------------------------------------------
def chart_1_p_persistent_throughput():
    csv_file = DATA_DIR / "p_persistent_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=300)

    n_colors = {3: '#0275D8', 5: '#D9534F', 10: '#28A745'}
    n_markers = {3: 'o', 5: 's', 10: '^'}

    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        tps = [r['throughput'] for r in sub]

        # Plot empirical curve
        ax.plot(ps, tps, marker=n_markers[N], markersize=7,
                linewidth=2.4, color=n_colors[N], label=f'N = {N} Empirical Curve')

        # Highlight optimal theoretical peak p* = 1/N
        opt_p = 1.0 / N
        ax.axvline(x=opt_p, color=n_colors[N], linestyle='--', alpha=0.75, linewidth=1.8,
                   label=f'Optimal $p^* = 1/{N} = {opt_p:.2f}$')

        # Find peak empirical point and annotate
        peak_idx = max(range(len(tps)), key=lambda i: tps[i])
        peak_p = ps[peak_idx]
        peak_tp = tps[peak_idx]
        ax.plot([peak_p], [peak_tp], marker='*', markersize=14, color=n_colors[N],
                markeredgecolor='black', markeredgewidth=1.2, zorder=5)

    ax.set_title(r'p-Persistent CSMA: Channel Throughput $S$ vs. Persistence Factor $p$ ($N \in \{3, 5, 10\}$, 500 Frames/Station)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel(r'Persistence Transmission Probability ($p$)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Throughput $S$ (Fraction of Channel Time)', fontsize=11, fontweight='bold')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.03, 1.00)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(frameon=True, framealpha=0.92, fontsize=8.5, loc='lower left', ncol=2)

    save_path = CHARTS_DIR / "1_p_persistent_throughput_vs_p.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 2: p-Persistent Collisions & Delay vs p (Requirement i)
# ------------------------------------------------------------------------------
def chart_2_p_persistent_collisions_and_delay():
    csv_file = DATA_DIR / "p_persistent_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    n_colors = {3: '#0275D8', 5: '#D9534F', 10: '#28A745'}
    n_markers = {3: 'o', 5: 's', 10: '^'}

    # Left: Collisions vs p (Log Scale to reveal monotonic escalation clearly)
    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        colls = [max(1.0, r['collisions']) for r in sub]
        ax1.plot(ps, colls, marker=n_markers[N], markersize=6.5,
                 linewidth=2.0, color=n_colors[N], label=f'N = {N}')

    ax1.set_yscale('log')
    ax1.set_title(r'(A) Total Collisions vs. Persistence Factor $p$', fontsize=12, fontweight='bold')
    ax1.set_xlabel(r'Persistence Probability ($p$)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Total Collisions Observed (Log Scale)', fontsize=11, fontweight='bold')
    ax1.grid(True, which="both", linestyle='--', alpha=0.4)
    ax1.legend(frameon=True, fontsize=9.5)

    # Right: Average Delay vs p (Convex U-Curve with minimum at p* = 1/N)
    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N and r['throughput'] > 0.0], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        delays = [r['avg_delay'] for r in sub]
        ax2.plot(ps, delays, marker=n_markers[N], markersize=6.5,
                 linewidth=2.0, color=n_colors[N], label=f'N = {N}')

        # Mark delay minimum
        min_idx = min(range(len(delays)), key=lambda i: delays[i])
        ax2.plot([ps[min_idx]], [delays[min_idx]], marker='*', markersize=13,
                 color=n_colors[N], markeredgecolor='black', markeredgewidth=1.0, zorder=5)

    ax2.set_yscale('log')
    ax2.set_title(r'(B) Average Packet Latency vs. Persistence Factor $p$', fontsize=12, fontweight='bold')
    ax2.set_xlabel(r'Persistence Probability ($p$)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Mean Packet Delay in Slots (Log Scale)', fontsize=11, fontweight='bold')
    ax2.grid(True, which="both", linestyle='--', alpha=0.4)
    ax2.legend(frameon=True, fontsize=9.5)

    plt.suptitle('p-Persistent CSMA: Contention Penalties Across Probability Spectrum (N in {3, 5, 10}, 500 Frames/Station)',
                 fontsize=13.5, fontweight='bold', y=1.02)

    save_path = CHARTS_DIR / "2_p_persistent_collisions_and_delay.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 3: Contending Stations N vs Throughput (Requirement ii)
# ------------------------------------------------------------------------------
def chart_3_stations_vs_throughput():
    csv_file = DATA_DIR / "stations_contention_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'one_persistent']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        tps = [r['throughput'] for r in sub]
        ax.plot(ns, tps, marker=MARKERS[strat], markersize=8,
                linewidth=2.4, color=COLORS[strat], label=LABELS[strat])

    ax.set_title('Channel Throughput vs. Contending Network Stations (N = 1 to 35, 400 Frames/Station Saturated Load)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Saturated Channel Throughput (S)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 36)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True)
    ax.legend(frameon=True, framealpha=0.92, fontsize=9.5, loc='upper right')

    save_path = CHARTS_DIR / "3_stations_vs_throughput.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 4: Contending Stations N vs Collisions (Requirement ii)
# ------------------------------------------------------------------------------
def chart_4_stations_vs_collisions():
    csv_file = DATA_DIR / "stations_contention_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    for strat in ['one_persistent', 'csma_cd', 'non_persistent', 'p_persistent']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        colls = [r['collisions'] for r in sub]
        crates = [r['collision_rate'] * 100.0 for r in sub]

        ax1.plot(ns, colls, marker=MARKERS[strat], markersize=7,
                 linewidth=2.0, color=COLORS[strat], label=LABELS[strat])
        ax2.plot(ns, crates, marker=MARKERS[strat], markersize=7,
                 linewidth=2.0, color=COLORS[strat], label=LABELS[strat])

    ax1.set_title('(A) Total Contention Collisions vs. N', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Number of Stations (N)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Total Collisions Observed', fontsize=11, fontweight='bold')
    ax1.grid(True)
    ax1.legend(frameon=True, fontsize=8.5)

    ax2.set_title('(B) Collision Probability (%) vs. N', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Number of Stations (N)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Collision Rate (%)', fontsize=11, fontweight='bold')
    ax2.grid(True)
    ax2.legend(frameon=True, fontsize=8.5)

    plt.suptitle('Collision Scaling Under Intense Contention (N = 1 to 35 Stations, 400 Frames/Station)',
                 fontsize=13.5, fontweight='bold', y=1.02)

    save_path = CHARTS_DIR / "4_stations_vs_collisions.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 5: Contending Stations N vs Transmission Delay (Requirement ii)
# ------------------------------------------------------------------------------
def chart_5_stations_vs_delay():
    csv_file = DATA_DIR / "stations_contention_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    for strat in ['one_persistent', 'non_persistent', 'p_persistent', 'csma_cd']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        delays = [r['avg_delay'] for r in sub]
        ax.plot(ns, delays, marker=MARKERS[strat], markersize=8,
                linewidth=2.2, color=COLORS[strat], label=LABELS[strat])

    ax.set_title('Average Frame Transmission Delay vs. Station Contention (N = 1 to 35 Stations, 400 Frames/Station)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Mean Transmission Latency (Time Slots)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 36)
    ax.grid(True)
    ax.legend(frameon=True, framealpha=0.92, fontsize=9.5, loc='upper left')

    save_path = CHARTS_DIR / "5_stations_vs_delay.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 6: Protocol Channel Efficiency Comparison (Requirement ii)
# ------------------------------------------------------------------------------
def chart_6_stations_vs_efficiency():
    csv_file = DATA_DIR / "stations_contention_sweep.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'one_persistent']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        effs = [r['efficiency'] * 100.0 for r in sub]
        ax.plot(ns, effs, marker=MARKERS[strat], markersize=8,
                linewidth=2.4, color=COLORS[strat], label=LABELS[strat])

    ax.set_title(r'Channel Access Efficiency ($\eta = T_{useful} / T_{total}$) vs. Contending Stations (N = 1 to 35, 400 Frames/Station)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Efficiency $\eta$ (%)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 36)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.grid(True)
    ax.legend(frameon=True, framealpha=0.92, fontsize=9.5, loc='upper right')

    save_path = CHARTS_DIR / "6_stations_vs_channel_efficiency.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 7: Classic S vs Offered Load G (Kleinrock & Tobagi Renewal Model)
# ------------------------------------------------------------------------------
def chart_7_throughput_vs_offered_load():
    csv_file = DATA_DIR / "throughput_vs_offered_load.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.4), dpi=300)

    gs = [r['G'] for r in data]
    ax.plot(gs, [r['S_pure_aloha'] for r in data], '--', color='#6C757D', linewidth=2.0, label='Pure ALOHA ($S = G e^{-2G}$, Max 18.4%)')
    ax.plot(gs, [r['S_slotted_aloha'] for r in data], '--', color='#17A2B8', linewidth=2.0, label='Slotted ALOHA ($S = G e^{-G}$, Max 36.8%)')
    ax.plot(gs, [r['S_1_persistent'] for r in data], '-', color=COLORS['one_persistent'], linewidth=2.2, label='1-Persistent CSMA ($a=0.01$)')
    ax.plot(gs, [r['S_non_persistent'] for r in data], '-', color=COLORS['non_persistent'], linewidth=2.2, label='Non-Persistent CSMA ($a=0.01$)')
    ax.plot(gs, [r['S_csma_cd'] for r in data], '-', color=COLORS['csma_cd'], linewidth=2.5, label='CSMA/CD (IEEE 802.3)')

    ax.set_title('Classical MAC Performance: Throughput (S) vs. Offered Load (G) (Renewal Model, Poisson Frame Arrivals)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel('Offered Traffic Load (G: packets generated / frame time)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Throughput $S$ (Fraction of Capacity)', fontsize=11, fontweight='bold')
    ax.set_xscale('log')
    ax.set_xlim(0.08, 12.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, which='both', linestyle='--', alpha=0.6)
    ax.legend(frameon=True, framealpha=0.92, fontsize=9.2, loc='upper left')

    save_path = CHARTS_DIR / "7_classic_throughput_vs_offered_load_g.png"
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.15)
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 8: CSMA/CD Efficiency vs Propagation Delay Ratio a
# ------------------------------------------------------------------------------
def chart_8_csmacd_efficiency_vs_a():
    csv_file = DATA_DIR / "csmacd_efficiency_vs_a.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    a_vals = [r['a'] for r in data]
    theory = [r['theoretical_efficiency'] * 100.0 for r in data]
    emp = [r['empirical_efficiency'] * 100.0 for r in data]

    ax.plot(a_vals, theory, '--', color='#111111', linewidth=2.2,
            label=r'Theoretical: $\eta = \frac{1}{1 + 6.44a}$')
    ax.plot(a_vals, emp, 'o-', color=COLORS['csma_cd'], markersize=6,
            linewidth=2.0, label='Empirical Simulation (N=10 Contending Stations, 400 Frames/Station)')

    ax.set_title(r'CSMA/CD Channel Efficiency ($\eta$) vs. Normalized Delay Ratio ($a = T_p / T_t$) (N = 10 Stations, 400 Frames/Station)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel(r'Normalized Propagation Delay Ratio $a = T_p / T_t$', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Efficiency $\eta$ (%)', fontsize=11, fontweight='bold')
    ax.set_xscale('log')
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.grid(True, which='both')
    ax.legend(frameon=True, framealpha=0.92, fontsize=10, loc='lower left')

    save_path = CHARTS_DIR / "8_csmacd_efficiency_vs_propagation_delay_a.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

def main():
    print("==================================================================")
    print("  Generating Publication-Grade CSMA Charts for Report             ")
    print("==================================================================")
    chart_1_p_persistent_throughput()
    chart_2_p_persistent_collisions_and_delay()
    chart_3_stations_vs_throughput()
    chart_4_stations_vs_collisions()
    chart_5_stations_vs_delay()
    chart_6_stations_vs_efficiency()
    # chart_7_throughput_vs_offered_load() [Removed per user specification]
    chart_8_csmacd_efficiency_vs_a()
    print(f"\n[+] Active visual charts successfully rendered in: {CHARTS_DIR}")

if __name__ == "__main__":
    main()
