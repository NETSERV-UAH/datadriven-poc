#!/bin/bash

TXT_LOG="vagrant_provision_30x.log"
CSV_LOG="vagrant_provision_30x.csv"

> "$TXT_LOG"
echo "iteration,stage,duration_seconds" > "$CSV_LOG"

measure_command() {
    local iteration=$1
    local stage=$2
    local command="$3"

    echo "Iteration $iteration - Starting: $stage"
    echo "== Iteration $iteration - $stage ==" >> "$TXT_LOG"

    local start_time=$(date +%s.%N)
    echo "Start: $(date -d @${start_time%%.*})" >> "$TXT_LOG"

    if ! eval "$command" 2>&1 | tee -a "$TXT_LOG"; then
        echo "Stage $stage failed." | tee -a "$TXT_LOG"
    fi

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    local formatted_duration=$(printf "%.3f" "$duration")

    echo "End: $(date -d @${end_time%%.*})" >> "$TXT_LOG"
    echo "Duration: ${formatted_duration} seconds" >> "$TXT_LOG"
    echo >> "$TXT_LOG"

    echo "$iteration,$stage,$formatted_duration" >> "$CSV_LOG"
}

run_stage() {
    local iteration=$1
    local node=$2
    local provision=$3
    measure_command "$iteration" "$provision" "vagrant provision $node --provision-with=$provision"
}

for i in $(seq 1 20); do
    echo "=============================="
    echo "Iteration $i - Starting full cycle"
    echo "=============================="

    measure_command "$i" "up" "vagrant up"

    run_stage "$i" "node-1" "master"
    run_stage "$i" "node-2" "worker-1"
    run_stage "$i" "node-3" "worker-2"
    run_stage "$i" "node-1" "dashboard"
    run_stage "$i" "node-1" "metrics-server"
    run_stage "$i" "node-1" "kubevirt"
    run_stage "$i" "node-1" "pre-process"
    run_stage "$i" "node-1" "project"

    measure_command "$i" "destroy" "vagrant destroy --force"

    echo
done

echo "30 iterations complete. Logs saved in:"
echo "- $TXT_LOG"
echo "- $CSV_LOG"

