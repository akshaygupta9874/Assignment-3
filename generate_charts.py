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

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    n_colors = {3: '#0275D8', 5: '#D9534F', 10: '#28A745'}
    n_markers = {3: 'o', 5: 's', 10: '^'}

    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        tps = [r['throughput'] for r in sub]

        ax.plot(ps, tps, marker=n_markers[N], markersize=7,
                linewidth=2.2, color=n_colors[N], label=f'N = {N} Contending Stations')

        # Highlight optimal theoretical peak p* = 1/N
        opt_p = 1.0 / N
        ax.axvline(x=opt_p, color=n_colors[N], linestyle=':', alpha=0.6,
                   label=f'Optimal $p^* = 1/{N} = {opt_p:.2f}$')

    ax.set_title(r'p-Persistent CSMA: Channel Throughput $S$ vs. Persistence Factor $p$',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel(r'Persistence Transmission Probability ($p$)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Throughput $S$ (Fraction of Channel Time)', fontsize=11, fontweight='bold')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0.15, 0.95)
    ax.grid(True)
    ax.legend(frameon=True, framealpha=0.92, fontsize=9, loc='lower right')

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

    # Left: Collisions vs p
    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        colls = [r['collisions'] for r in sub]
        ax1.plot(ps, colls, marker=n_markers[N], markersize=7,
                 linewidth=2.0, color=n_colors[N], label=f'N = {N}')

    ax1.set_title(r'(A) Total Collisions vs. Persistence Factor $p$', fontsize=12, fontweight='bold')
    ax1.set_xlabel(r'Persistence Probability ($p$)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Total Collisions Observed', fontsize=11, fontweight='bold')
    ax1.grid(True)
    ax1.legend(frameon=True, fontsize=9.5)

    # Right: Average Delay vs p
    for N in [3, 5, 10]:
        sub = sorted([r for r in data if int(r['N']) == N], key=lambda x: x['p'])
        ps = [r['p'] for r in sub]
        delays = [r['avg_delay'] for r in sub]
        ax2.plot(ps, delays, marker=n_markers[N], markersize=7,
                 linewidth=2.0, color=n_colors[N], label=f'N = {N}')

    ax2.set_title(r'(B) Average Transmission Delay vs. Persistence Factor $p$', fontsize=12, fontweight='bold')
    ax2.set_xlabel(r'Persistence Probability ($p$)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Mean Packet Delay (Time Slots)', fontsize=11, fontweight='bold')
    ax2.grid(True)
    ax2.legend(frameon=True, fontsize=9.5)

    plt.suptitle('p-Persistent CSMA: Contention Penalties Across Probability Spectrum',
                 fontsize=14, fontweight='bold', y=1.02)

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

    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'csma_ca', 'one_persistent']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        tps = [r['throughput'] for r in sub]
        ax.plot(ns, tps, marker=MARKERS[strat], markersize=8,
                linewidth=2.4, color=COLORS[strat], label=LABELS[strat])

    ax.set_title('Channel Throughput vs. Contending Network Stations (N)',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Saturated Channel Throughput (S)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 36)
    ax.set_ylim(0.2, 0.98)
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

    for strat in ['one_persistent', 'csma_cd', 'non_persistent', 'p_persistent', 'csma_ca']:
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

    plt.suptitle('Collision Scaling Under Intense Network Station Contention',
                 fontsize=14, fontweight='bold', y=1.02)

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

    for strat in ['one_persistent', 'non_persistent', 'p_persistent', 'csma_ca', 'csma_cd']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        delays = [r['avg_delay'] for r in sub]
        ax.plot(ns, delays, marker=MARKERS[strat], markersize=8,
                linewidth=2.2, color=COLORS[strat], label=LABELS[strat])

    ax.set_title('Average Frame Transmission Delay vs. Station Contention (N)',
                 fontsize=13, fontweight='bold', pad=12)
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

    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'csma_ca', 'one_persistent']:
        sub = sorted([r for r in data if r['strategy'] == strat], key=lambda x: x['N'])
        if not sub: continue
        ns = [r['N'] for r in sub]
        effs = [r['efficiency'] * 100.0 for r in sub]
        ax.plot(ns, effs, marker=MARKERS[strat], markersize=8,
                linewidth=2.4, color=COLORS[strat], label=LABELS[strat])

    ax.set_title(r'Channel Access Efficiency ($\eta = T_{useful} / T_{total}$) vs. Contending Stations (N)',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Channel Efficiency $\eta$ (%)', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 36)
    ax.set_ylim(20, 100)
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

    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=300)

    gs = [r['G'] for r in data]
    ax.plot(gs, [r['S_pure_aloha'] for r in data], '--', color='#6C757D', linewidth=2.0, label='Pure ALOHA ($S = G e^{-2G}$, Max 18.4%)')
    ax.plot(gs, [r['S_slotted_aloha'] for r in data], '--', color='#17A2B8', linewidth=2.0, label='Slotted ALOHA ($S = G e^{-G}$, Max 36.8%)')
    ax.plot(gs, [r['S_1_persistent'] for r in data], '-', color=COLORS['one_persistent'], linewidth=2.2, label='1-Persistent CSMA ($a=0.01$)')
    ax.plot(gs, [r['S_non_persistent'] for r in data], '-', color=COLORS['non_persistent'], linewidth=2.2, label='Non-Persistent CSMA ($a=0.01$)')
    ax.plot(gs, [r['S_csma_cd'] for r in data], '-', color=COLORS['csma_cd'], linewidth=2.5, label='CSMA/CD (IEEE 802.3)')

    ax.set_title('Classical MAC Performance: Throughput (S) vs. Offered Channel Traffic (G)',
                 fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Offered Traffic Load (G: packets generated / frame time)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Saturated Channel Throughput (S: successful packets / frame time)', fontsize=11, fontweight='bold')
    ax.set_xscale('log')
    ax.set_xlim(0.08, 12.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, which='both')
    ax.legend(frameon=True, framealpha=0.92, fontsize=9.2, loc='upper left')

    save_path = CHARTS_DIR / "7_classic_throughput_vs_offered_load_g.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
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
            linewidth=2.0, label='Empirical Simulation (N=10 Contending Stations)')

    ax.set_title(r'CSMA/CD Channel Efficiency ($\eta$) vs. Normalized Propagation Delay ($a = T_p / T_t$)',
                 fontsize=13, fontweight='bold', pad=12)
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

# ------------------------------------------------------------------------------
# Chart 9: Backoff Dynamics & Fairness (BEB vs Linear vs MACAW MILD)
# ------------------------------------------------------------------------------
def chart_9_backoff_comparison():
    csv_file = DATA_DIR / "backoff_comparison.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    b_colors = {
        'IEEE 802.3 Truncated BEB': '#28A745',
        'Linear Backoff':           '#D9534F',
        'MACAW MILD (x1.5 / -1)':   '#0275D8'
    }

    schemes = ['IEEE 802.3 Truncated BEB', 'Linear Backoff', 'MACAW MILD (x1.5 / -1)']
    for scheme in schemes:
        sub = sorted([r for r in data if r['scheme'] == scheme], key=lambda x: x['N'])
        ns = [r['N'] for r in sub]
        retries = [r['avg_retries'] for r in sub]
        fair = [r['jains_fairness'] for r in sub]

        ax1.plot(ns, retries, marker='o', linewidth=2.0,
                 color=b_colors.get(scheme, '#333333'), label=scheme)
        ax2.plot(ns, fair, marker='s', linewidth=2.0,
                 color=b_colors.get(scheme, '#333333'), label=scheme)

    ax1.set_title('(A) Average Collision Retries per Packet', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Average Re-transmissions', fontsize=11, fontweight='bold')
    ax1.grid(True)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title('(B) Jain\'s Channel Access Fairness Index', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Number of Contending Stations (N)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Jain\'s Fairness Index (0 to 1)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0.7, 1.02)
    ax2.grid(True)
    ax2.legend(frameon=True, fontsize=9)

    plt.suptitle('Collision Resolution Dynamics: IEEE 802.3 Truncated BEB vs. Alternatives',
                 fontsize=14, fontweight='bold', y=1.02)

    save_path = CHARTS_DIR / "9_backoff_dynamics_and_fairness.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 10: Live C Multi-Process Empirical Socket Validation
# ------------------------------------------------------------------------------
def chart_10_live_c_validation():
    csv_file = DATA_DIR / "live_c_benchmarks.csv"
    if not csv_file.exists(): return
    data = load_csv(csv_file)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    strategies = ['non_persistent', 'one_persistent', 'p_persistent', 'csma_cd']
    x = np.arange(len(strategies))
    width = 0.35

    d2 = {r['strategy']: r for r in data if int(r['stations']) == 2}
    d4 = {r['strategy']: r for r in data if int(r['stations']) == 4}

    eff2 = [d2[s]['efficiency'] * 100.0 if s in d2 else 0 for s in strategies]
    eff4 = [d4[s]['efficiency'] * 100.0 if s in d4 else 0 for s in strategies]

    ax1.bar(x - width/2, eff2, width, label='N = 2 Stations', color='#0275D8', alpha=0.85)
    ax1.bar(x + width/2, eff4, width, label='N = 4 Stations', color='#D9534F', alpha=0.85)
    ax1.set_title('(A) Channel Efficiency (%) in Live Socket Execution', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(['Non-P', '1-P', 'p-P', 'CSMA/CD'], fontsize=10, fontweight='bold')
    ax1.set_ylabel('Efficiency (%)', fontsize=11, fontweight='bold')
    ax1.grid(True, axis='y')
    ax1.legend(frameon=True)

    coll2 = [d2[s]['collisions'] if s in d2 else 0 for s in strategies]
    coll4 = [d4[s]['collisions'] if s in d4 else 0 for s in strategies]

    ax2.bar(x - width/2, coll2, width, label='N = 2 Stations', color='#0275D8', alpha=0.85)
    ax2.bar(x + width/2, coll4, width, label='N = 4 Stations', color='#D9534F', alpha=0.85)
    ax2.set_title('(B) Observed Contention Collisions', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Non-P', '1-P', 'p-P', 'CSMA/CD'], fontsize=10, fontweight='bold')
    ax2.set_ylabel('Collision Count', fontsize=11, fontweight='bold')
    ax2.grid(True, axis='y')
    ax2.legend(frameon=True)

    plt.suptitle('Live Multi-Process C Sockets: Channel Server & Stations Empirical Validation',
                 fontsize=14, fontweight='bold', y=1.02)

    save_path = CHARTS_DIR / "10_live_c_socket_validation.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  [SAVED] {save_path.name}")

# ------------------------------------------------------------------------------
# Chart 11: Master Performance Comparison Dashboard
# ------------------------------------------------------------------------------
def chart_11_master_dashboard():
    csv_stations = DATA_DIR / "stations_contention_sweep.csv"
    csv_p = DATA_DIR / "p_persistent_sweep.csv"
    if not csv_stations.exists() or not csv_p.exists(): return

    data_st = load_csv(csv_stations)
    data_p = load_csv(csv_p)

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), dpi=300)

    # (A) Throughput vs N
    ax = axes[0, 0]
    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'one_persistent']:
        sub = sorted([r for r in data_st if r['strategy'] == strat], key=lambda x: x['N'])
        ax.plot([r['N'] for r in sub], [r['throughput'] for r in sub],
                marker=MARKERS[strat], color=COLORS[strat], linewidth=2.0, label=LABELS[strat])
    ax.set_title('(A) Saturated Throughput vs. Contending Stations (N)', fontweight='bold')
    ax.set_xlabel('Stations (N)', fontweight='bold')
    ax.set_ylabel('Throughput (S)', fontweight='bold')
    ax.grid(True)
    ax.legend(fontsize=8, frameon=True)

    # (B) Collisions vs N
    ax = axes[0, 1]
    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'one_persistent']:
        sub = sorted([r for r in data_st if r['strategy'] == strat], key=lambda x: x['N'])
        ax.plot([r['N'] for r in sub], [r['collisions'] for r in sub],
                marker=MARKERS[strat], color=COLORS[strat], linewidth=2.0, label=LABELS[strat])
    ax.set_title('(B) Collision Frequency vs. Contending Stations (N)', fontweight='bold')
    ax.set_xlabel('Stations (N)', fontweight='bold')
    ax.set_ylabel('Total Collisions', fontweight='bold')
    ax.grid(True)
    ax.legend(fontsize=8, frameon=True)

    # (C) Delay vs N
    ax = axes[1, 0]
    for strat in ['csma_cd', 'p_persistent', 'non_persistent', 'one_persistent']:
        sub = sorted([r for r in data_st if r['strategy'] == strat], key=lambda x: x['N'])
        ax.plot([r['N'] for r in sub], [r['avg_delay'] for r in sub],
                marker=MARKERS[strat], color=COLORS[strat], linewidth=2.0, label=LABELS[strat])
    ax.set_title('(C) Mean Packet Delay vs. Contending Stations (N)', fontweight='bold')
    ax.set_xlabel('Stations (N)', fontweight='bold')
    ax.set_ylabel('Delay (Slots)', fontweight='bold')
    ax.grid(True)
    ax.legend(fontsize=8, frameon=True)

    # (D) p-Persistent Throughput vs p
    ax = axes[1, 1]
    for N in [3, 5, 10]:
        sub = sorted([r for r in data_p if int(r['N']) == N], key=lambda x: x['p'])
        ax.plot([r['p'] for r in sub], [r['throughput'] for r in sub],
                marker='o', linewidth=2.0, label=f'N = {N}')
        ax.axvline(1.0/N, linestyle=':', alpha=0.5)
    ax.set_title(r'(D) p-Persistent Throughput vs. $p$ ($p^* = 1/N$ peak)', fontweight='bold')
    ax.set_xlabel(r'Probability $p$', fontweight='bold')
    ax.set_ylabel('Throughput (S)', fontweight='bold')
    ax.grid(True)
    ax.legend(fontsize=8.5, frameon=True)

    plt.suptitle('CSMA Medium Access Control Master Performance Comparison Dashboard',
                 fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()

    save_path = CHARTS_DIR / "11_master_csma_dashboard.png"
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
    chart_7_throughput_vs_offered_load()
    chart_8_csmacd_efficiency_vs_a()
    chart_9_backoff_comparison()
    chart_10_live_c_validation()
    chart_11_master_dashboard()
    print(f"\n[+] All 11 visual charts successfully rendered in: {CHARTS_DIR}")

if __name__ == "__main__":
    main()
