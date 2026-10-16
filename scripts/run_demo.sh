#!/usr/bin/env bash
# =====================================================================
# run_demo.sh — ICLIM live demo
#
# Creates a controlled CPU incident and shows the whole chain:
#   load → ICLIM detects it → severity escalates to CRITICAL
#   → AI explains it → result on the API and in Grafana.
#
# Run on the runtime VM, from the project folder:
#   bash scripts/run_demo.sh            # full demo
#   bash scripts/run_demo.sh --check    # pre-flight checks only
#   DEMO_SECONDS=180 bash scripts/run_demo.sh  # longer load if CRITICAL isn't reached
#
# Safe: the load stops by itself. Nothing is changed or installed.
# The load runs at the lowest priority (nice 19), so the CPU still shows
# ~100% but ICLIM is never starved and keeps checking every ~6 seconds.
# =====================================================================

set -u
cd "$(dirname "$0")/.." || exit 1

DURATION="${DEMO_SECONDS:-120}"
EVENTS="logs/anomaly_events.jsonl"
LOG="logs/iclim.log"
API="http://localhost:8001/ai/latest"
VM_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

step() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }
fail() { printf '\033[1;31m%s\033[0m\n' "$1"; exit 1; }

# ---------------------------------------------------------------------
step "1. Pre-flight: is everything running?"
all_ok=1
for svc in iclim iclim-ai-result-api prometheus node_exporter grafana-server; do
    state="$(systemctl is-active "$svc")"
    printf '  %-22s %s\n' "$svc" "$state"
    [ "$state" = "active" ] || all_ok=0
done
printf '  %-22s %s\n' "iclim-ai-worker.timer" "$(systemctl is-active iclim-ai-worker.timer)"
curl -fsS localhost:9090/-/ready >/dev/null 2>&1 && echo "  Prometheus API         ready" || all_ok=0
curl -fsS localhost:8000/metrics >/dev/null 2>&1 && echo "  ICLIM /metrics         ready" || all_ok=0
[ "$all_ok" = 1 ] || fail "Something is not running. Fix it before the demo (sudo systemctl start <name>)."
echo "  Grafana: http://${VM_IP}:3000"

[ "${1:-}" = "--check" ] && { echo; echo "Pre-flight OK."; exit 0; }

before=$(wc -l < "$EVENTS" 2>/dev/null || echo 0)
shown=$(wc -l < "$LOG" 2>/dev/null || echo 0)
PATTERN="\| (UNUSUAL|WARNING|CRITICAL) \|"

# Print log lines added since the last call that match PATTERN
show_new_log_lines() {
    local total
    total=$(wc -l < "$LOG")
    if [ "$total" -gt "$shown" ]; then
        sed -n "$((shown + 1)),${total}p" "$LOG" | grep -E "$PATTERN" | sed 's/^/  /'
        shown=$total
    fi
}

# ---------------------------------------------------------------------
step "2. Create the incident: $(nproc) busy loop(s) for ${DURATION}s"
echo "  One loop per CPU, so the whole machine is at ~100%. Each loop stops itself."
echo "  The loops run at the lowest priority, so ICLIM still gets its turn."
pids=()
for _ in $(seq "$(nproc)"); do
    # The loop ends itself after DURATION seconds (no 'timeout' needed).
    nice -n 19 python3 -c "import time
end = time.time() + ${DURATION}
while time.time() < end:
    pass" < /dev/null > /dev/null 2>&1 &
    pids+=("$!")
done
trap 'kill "${pids[@]}" 2>/dev/null' INT TERM

sleep 2
running=0
for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null && running=$((running + 1)); done
[ "$running" -gt 0 ] || fail "The load did not start. Check that python3 works: python3 --version"
echo "  Load running: ${running} loop(s) busy."

# ---------------------------------------------------------------------
step "3. Watch ICLIM detect and rate it (live log)"
echo "  UNUSUAL = unusual but short (<30 s) · CRITICAL = lasting ≥30 s and a value ≥90%"
while kill -0 "${pids[0]}" 2>/dev/null; do
    sleep 3
    show_new_log_lines
done
sleep 7          # one more agent cycle after the load ends
show_new_log_lines
wait 2>/dev/null

# ---------------------------------------------------------------------
step "4. What did ICLIM record?"
top_severity=$(tail -n +"$((before + 1))" "$EVENTS" 2>/dev/null | python3 -c '
import json, sys
rank = {"unusual": 1, "warning": 2, "critical": 3}
events = [json.loads(l) for l in sys.stdin if l.strip()]
if not events:
    print("none"); sys.exit()
top = max(events, key=lambda e: (rank.get(e["severity"], 0), e["duration_seconds"]))
print(top["severity"])
sys.stderr.write("  Anomalous readings: %d\n" % len(events))
sys.stderr.write("  Highest severity:   %s (lasted %s s, CPU %s%%)\n"
                 % (top["severity"].upper(), top["duration_seconds"], top["cpu"]))
')
if [ "$top_severity" != "critical" ] && [ "$top_severity" != "warning" ]; then
    fail "Did not reach WARNING/CRITICAL. Run again with a longer load: DEMO_SECONDS=180 bash scripts/run_demo.sh"
fi

# ---------------------------------------------------------------------
step "5. Ask the AI to explain it (normally the 5-minute timer does this)"
if ! sudo systemctl start iclim-ai-worker.service; then
    echo
    journalctl -u iclim-ai-worker -n 5 --no-pager | tail -3
    fail "AI worker failed. If you see '429 rate limit', Groq's daily quota is used up: show the last saved result instead (curl $API)."
fi

# ---------------------------------------------------------------------
step "6. The AI's answer (from $API)"
curl -fsS "$API" | python3 -c '
import json, sys
r = json.load(sys.stdin)
e, a = r["incident_explanation"], r["operational_assistant"]
print("  Incident:   %s on %s" % (r["timestamp"], r["server"]))
print("  Severity:   %s   Priority: %s   Evidence: %s"
      % (r["severity"], a["investigation_priority"], e["evidence_strength"]["level"]))
print("\n  What happened:\n    " + e["explanation"])
print("\n  Still unknown:")
for u in e["unknowns"][:3]:
    print("    - " + u)
print("\n  Suggested checks (a human decides and acts):")
for c in a["recommended_checks"]:
    print("    - " + c)
'

step "Done"
echo "  Now show Grafana (http://${VM_IP}:3000): Linux row → ICLIM row → AI Analysis row."
