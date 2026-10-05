#!/usr/bin/env bash
# ==============================================================================
# interactive_menu.sh
# Concurrent Multi-Threaded CSMA & CSMA/CD Simulation Launcher
# CSE/PC/B/S/314: Computer Networks Laboratory
# Department of Computer Science & Engineering, Jadavpur University
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Ensure binary is built
echo "[*] Compiling Multi-Threaded C binary (csma_sim)..."
make all > /dev/null 2>&1

cleanup() {
    pkill -f "./bin/csma_sim" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

while true; do
    echo "=========================================================================="
    echo "  CSE/PC/B/S/314: MULTI-THREADED CSMA & CSMA/CD SIMULATION SUITE LAUNCHER"
    echo "=========================================================================="
    echo "1) Launch Interactive C Simulation Menu (bin/csma_sim)"
    echo "2) Run All 4 Protocols Batch Simulation (N=10, 5 Frames/Station)"
    echo "3) View Simulation Logs (Select Log to View)"
    echo "4) Run High-Scale Simulation & Rebuild All Matplotlib Charts"
    echo "5) Recompile Master Technical PDF Lab Report (generate_report.py)"
    echo "6) Exit"
    read -p "Select option [1-6, Default: 1]: " OPTION
    OPTION=${OPTION:-1}

    case "$OPTION" in
        1)
            ./bin/csma_sim
            ;;
        2)
            echo ""
            echo ">>> Executing All 4 Strategies (N=10 Stations, 5 Frames/Station)..."
            printf "2\n10\n5\n0.10\n5\n" | ./bin/csma_sim
            ;;
        3)
            echo ""
            echo "=========================================================================="
            echo "                       SELECT LOG FILE TO VIEW                            "
            echo "=========================================================================="
            echo "1) Latest Simulation Run (logs/csma_simulation.log)"
            echo "2) CSMA/CD IEEE 802.3 Log (logs/csma_sim_csma_cd.log)"
            echo "3) 1-Persistent CSMA Log (logs/csma_sim_1_persistent.log)"
            echo "4) Non-Persistent CSMA Log (logs/csma_sim_non_persistent.log)"
            echo "5) p-Persistent CSMA Log (logs/csma_sim_p_persistent.log)"
            read -p "Select log [1-5, Default: 1]: " LOG_SEL
            LOG_SEL=${LOG_SEL:-1}
            case "$LOG_SEL" in
                2) TARGET_LOG="logs/csma_sim_csma_cd.log" ;;
                3) TARGET_LOG="logs/csma_sim_1_persistent.log" ;;
                4) TARGET_LOG="logs/csma_sim_non_persistent.log" ;;
                5) TARGET_LOG="logs/csma_sim_p_persistent.log" ;;
                *) TARGET_LOG="logs/csma_simulation.log" ;;
            esac
            if [ -f "$TARGET_LOG" ]; then
                echo ""
                echo "=========================================================================="
                echo "                 DISPLAYING: $TARGET_LOG                                  "
                echo "=========================================================================="
                cat "$TARGET_LOG"
                echo "=========================================================================="
            else
                echo "[!] Log file $TARGET_LOG not found yet!"
            fi
            ;;
        4)
            echo ""
            echo ">>> Running High-Scale Parametric Sweeps & Chart Rebuilder..."
            python3 run_high_scale_simulation.py
            ;;
        5)
            echo ""
            echo ">>> Rebuilding Master Technical PDF Lab Report..."
            python3 generate_report.py
            ;;
        6)
            echo "Exiting simulation menu. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid selection. Please choose an option between 1 and 6."
            ;;
    esac
done
