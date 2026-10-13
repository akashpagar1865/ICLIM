#!/usr/bin/env bash
# =====================================================================
# vm_inventory.sh
# Read-only snapshot of everything ICLIM-related running on the VM:
# systemd units, timers, cron, ports, Prometheus, Grafana, Docker,
# running processes and code/log/model locations.
#
# It CHANGES NOTHING. Secret-looking values are masked automatically,
# but always read the output yourself before sharing it.
#
# Usage (on the VM):
#   sudo bash vm_inventory.sh > system_inventory.txt 2>&1
# =====================================================================

set -u

# Anything matching this is treated as ICLIM-related
PATTERN='iclim|prometheus|grafana|node_exporter|node-exporter|exporter|ollama|groq|anomaly|ai_worker|result_api'

section() { printf '\n\n==================== %s ====================\n' "$1"; }
run()     { printf '\n$ %s\n' "$*"; eval "$@" 2>&1 || true; }

# Mask API keys, tokens, passwords, secrets
redact() {
  sed -E \
    -e 's/(gsk_)[A-Za-z0-9]+/\1REDACTED/g' \
    -e 's/((api[_-]?key|token|secret|password|passwd|credential)[A-Za-z0-9_]*[[:space:]]*[=:][[:space:]]*)[^[:space:]]+/\1REDACTED/Ig' \
    -e 's/(Bearer[[:space:]]+)[^[:space:]]+/\1REDACTED/g'
}

main() {
  section "1. HOST"
  run "date -u"
  run "hostnamectl"
  run "uptime"
  run "nproc; free -h"
  run "df -hT -x tmpfs -x devtmpfs -x squashfs -x overlay"

  section "2. ICLIM CODE ON THE VM"
  ICLIM_DIRS=$(find /home /opt /srv /root -maxdepth 5 -type f -name 'realtime_anomaly_agent.py' 2>/dev/null \
               | xargs -r -n1 dirname | xargs -r -n1 dirname | sort -u)
  echo "Detected ICLIM checkouts: ${ICLIM_DIRS:-none found}"
  for d in $ICLIM_DIRS; do
    run "(cd '$d' && git remote -v && git log --oneline -5 && echo '-- uncommitted changes:' && git status --short | head -40)"
    run "find '$d' -maxdepth 3 \\( -name venv -o -name .venv -o -name .git -o -name __pycache__ \\) -prune -o -print | sort | head -300"
    run "ls -la '$d'/.env '$d'/*.env 2>/dev/null"
  done

  section "3. SYSTEMD — CUSTOM UNITS AND TIMERS"
  run "ls -la /etc/systemd/system/*.service /etc/systemd/system/*.timer 2>/dev/null"
  run "systemctl list-units --type=service --all --no-pager | grep -Ei '$PATTERN'"
  run "systemctl list-timers --all --no-pager"

  UNITS=$( { ls /etc/systemd/system/*.service /etc/systemd/system/*.timer 2>/dev/null | xargs -r -n1 basename;
             systemctl list-unit-files --type=service,timer --no-legend --no-pager 2>/dev/null \
               | awk '{print $1}' | grep -Ei "$PATTERN"; } | sort -u )

  for u in $UNITS; do
    section "UNIT: $u"
    run "systemctl cat '$u' --no-pager"
    run "echo enabled=\$(systemctl is-enabled '$u') active=\$(systemctl is-active '$u')"
    # Show variable NAMES from EnvironmentFile(s), never their values
    for f in $(systemctl show -p EnvironmentFiles --value "$u" 2>/dev/null | awk '{print $1}' | sed 's/^-//'); do
      echo
      echo "EnvironmentFile $f -> variable names only:"
      [ -f "$f" ] && grep -Ev '^\s*(#|$)' "$f" | sed -E 's/=.*$/=<hidden>/'
    done
    run "journalctl -u '$u' --no-pager -n 15 -o short-iso"
  done

  section "4. CRON"
  run "crontab -l -u root"
  for u in $(ls /home); do run "crontab -l -u '$u'"; done
  run "ls -la /etc/cron.d"
  run "grep -HEv '^\s*(#|$)' /etc/cron.d/* 2>/dev/null | grep -Ei '$PATTERN|python'"

  section "5. NETWORK — LISTENING PORTS AND FIREWALL"
  run "ss -tulpn"
  run "ufw status verbose"

  section "6. RUNNING PROCESSES (ICLIM-related)"
  run "ps -eo user,pid,etime,args --sort=args | grep -Ei '$PATTERN|python' | grep -v grep"

  section "7. PROMETHEUS"
  for f in /etc/prometheus/prometheus.yml /opt/prometheus/prometheus.yml /usr/local/etc/prometheus/prometheus.yml; do
    [ -f "$f" ] && run "cat '$f'"
  done
  run "ls -la /etc/prometheus /etc/prometheus/rules 2>/dev/null"
  run "for f in /etc/prometheus/*rule*.y*ml /etc/prometheus/rules/*.y*ml; do [ -f \"\$f\" ] && echo \"--- \$f\" && cat \"\$f\"; done"
  run "curl -s --max-time 5 'http://localhost:9090/api/v1/targets?state=active' | python3 -c 'import sys,json; [print(t[\"labels\"].get(\"job\"), t[\"scrapeUrl\"], t[\"health\"]) for t in json.load(sys.stdin)[\"data\"][\"activeTargets\"]]'"

  section "8. GRAFANA"
  run "ls -la /etc/grafana /etc/grafana/provisioning/* 2>/dev/null"
  run "grep -Ev '^\s*(;|#|$)' /etc/grafana/grafana.ini"
  run "cat /etc/grafana/provisioning/datasources/*.y*ml 2>/dev/null"
  run "cat /etc/grafana/provisioning/dashboards/*.y*ml 2>/dev/null"
  run "curl -s --max-time 5 http://localhost:3000/api/health"

  section "9. DOCKER"
  run "docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'"
  run "docker images"
  run "docker volume ls"

  section "10. RUNTIME VERSIONS"
  run "python3 --version"
  run "prometheus --version 2>&1 | head -1"
  run "grafana-server -v 2>/dev/null || grafana server -v 2>/dev/null"
  run "node_exporter --version 2>&1 | head -1"
  run "docker --version"

  section "11. LOG AND MODEL LOCATIONS"
  run "ls -la /var/log | grep -Ei '$PATTERN'"
  for d in $ICLIM_DIRS; do
    run "du -sh '$d'/logs '$d'/models 2>/dev/null"
    run "ls -la '$d'/models 2>/dev/null"
  done

  section "12. OTHER"
  run "which nginx ollama 2>/dev/null"
  run "ls /etc/nginx/sites-enabled 2>/dev/null"

  section "END OF INVENTORY"
}

main 2>&1 | redact
