#!/usr/bin/env bash
# ==============================================================================
# quick_demo.sh
# End-to-end multi-process verification script for CSMA protocols
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "  CSE/PC/B/S/314: CSMA MAC Protocols Live Verification    "
echo "=========================================================="

PORT=9199
FRAMES_PER_STATION=5

cleanup() {
    echo "Cleaning up background processes..."
    kill $(jobs -p) 2>/dev/null || true
    pkill -f "./bin/channel_server $PORT" 2>/dev/null || true
    pkill -f "./bin/station" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

run_scenario() {
    local STRATEGY=$1
    local NUM_STATIONS=$2
    local P_VAL=${3:-0.25}
    local DESC=$4

    PORT=$((PORT + 1))

    echo ""
    echo "----------------------------------------------------------"
    echo ">>> Running Test Scenario: $DESC"
    echo "    Strategy: $STRATEGY | Stations: $NUM_STATIONS | Frames/Station: $FRAMES_PER_STATION (Port: $PORT)"
    echo "----------------------------------------------------------"

    # Start channel server in background
    ./bin/channel_server $PORT 1.0 2.0 > logs/test_${STRATEGY}_server.log 2>&1 &
    SERVER_PID=$!
    sleep 0.3

    # Launch station processes concurrently
    STATION_PIDS=()
    for ((i=1; i<=NUM_STATIONS; i++)); do
        ./bin/station $i $STRATEGY 127.0.0.1 $PORT $FRAMES_PER_STATION $P_VAL > logs/test_${STRATEGY}_st${i}.log 2>&1 &
        STATION_PIDS+=($!)
    done

    # Wait for all stations to complete
    for pid in "${STATION_PIDS[@]}"; do
        wait $pid
    done

    echo "[+] All stations completed."
    sleep 0.5
    kill -TERM $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true

    # Display server summary
    echo "--- Server Summary Output ---"
    grep -E "Total Transmission Attempts|Total Successful Deliveries|Total Collisions|Total Jam Signals|Channel Efficiency" logs/test_${STRATEGY}_server.log || true
}

mkdir -p logs

echo "[1/4] Testing Non-Persistent CSMA with 3 contending stations..."
run_scenario "non_persistent" 3 0.25 "Non-Persistent CSMA Contention"

echo "[2/4] Testing 1-Persistent CSMA with 3 contending stations..."
run_scenario "one_persistent" 3 0.25 "1-Persistent CSMA High Collision Contention"

echo "[3/4] Testing p-Persistent CSMA (p=0.33) with 3 contending stations..."
run_scenario "p_persistent" 3 0.33 "p-Persistent CSMA (p = 1/N Optimal)"

echo "[4/4] Testing CSMA/CD with 3 contending stations (Detection + Jam + BEB)..."
run_scenario "csma_cd" 3 0.25 "CSMA/CD with Collision Detection & BEB"

echo ""
echo "=========================================================="
echo "  All Live Multi-Process Scenarios Verified Successfully! "
echo "=========================================================="
