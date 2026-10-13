# ICLIM Components and Operations

This is a reference for every service running on the CentOS Stream 9 runtime VM. Each section covers what the service does, how systemd manages it, where it logs, and how to check it is healthy.

Unit files are in [`deploy/systemd/`](../deploy/systemd/). For how the components fit together, see [architecture.md](architecture.md).

## At a glance

| Unit | Type | Runs as | Schedule / restart | Port |
|---|---|---|---|---|
| `iclim.service` | long-running | `akashp` | `Restart=always`, 5s delay | 8000 |
| `iclim-model-refresh.service` | oneshot | `akashp` | `iclim-model-refresh.timer` daily 03:00 | none |
| `iclim-ai-worker.service` | oneshot | `akashp` | `iclim-ai-worker.timer` every 5 min | none |
| `iclim-ai-result-api.service` | long-running | `akashp` | `Restart=always`, 5s delay | 8001 |
| `node_exporter.service` | long-running | `node_exporter` | none (no auto-restart) | 9100 |
| `prometheus.service` | long-running | `prometheus` | `Restart=on-failure` | 9090 |
| `grafana-server.service` | long-running (packaged) | `grafana` | `Restart=on-failure`, start timeout 5 min | 3000 |

**Why systemd timers instead of cron:** timers are managed the same way as services. Their runs appear in `journalctl -u`, `systemctl list-timers` shows the last and next run, and `Persistent=true` catches up on runs missed while the VM was off.

**Quick health check for the whole stack:**

```bash
systemctl is-active iclim iclim-ai-result-api node_exporter prometheus grafana-server
systemctl list-timers 'iclim-*'
curl -s localhost:9090/api/v1/targets | python3 -m json.tool | grep -E '"job"|"health"'
curl -fsS localhost:8001/ai/latest | head -c 300; echo
```

---

## 1. Realtime anomaly agent: `iclim.service`

**What it does:** this is the core of ICLIM. Every ~6 seconds it samples CPU, memory and root-disk usage, scores the sample with the Isolation Forest model, classifies severity for anomalies, writes history, events and logs, and serves application metrics on `:8000/metrics`.

| | |
|---|---|
| Code | `agents/realtime_anomaly_agent.py`, `agents/metrics_exporter.py` |
| Config | `config/config.yaml` (env overrides: `INTERVAL`, `HOSTNAME`, `LOG_LEVEL`) |
| Writes | `logs/snapshot_history.jsonl`, `logs/anomaly_events.jsonl`, `logs/iclim.log` |
| Reads | `models/anomaly_model.pkl`, `logs/ai_incidents.jsonl` (for AI gauges) |
| First start | If history or model is missing, bootstraps 30 samples and trains a model before monitoring |
| Model reload | Detects a changed model file (mtime) and reloads it without a restart |

**Metrics exposed on :8000**

| Metric | Type | Meaning |
|---|---|---|
| `iclim_agent_status` | gauge | Set to 1 when the agent starts |
| `iclim_bootstrap_completed` | gauge | 1 once history and model are ready |
| `iclim_model_loaded` | gauge | 1 if a model is loaded; 0 if a load failed |
| `iclim_monitoring_cycles_total` | counter | Monitoring cycles completed |
| `iclim_anomaly_total{severity}` | counter | Anomalies by `unusual` / `warning` / `critical` |
| `iclim_ai_result_available` | gauge | 1 if an AI result exists |
| `iclim_ai_incident_severity{severity}` | gauge | Severity of the latest AI-analysed incident |
| `iclim_ai_investigation_priority{priority}` | gauge | `HIGH` / `MEDIUM` / `LOW` from the Operational Assistant |

**Check it**

```bash
systemctl status iclim --no-pager
journalctl -u iclim -n 20 --no-pager           # live log lines
tail -f ~/projects/ICLIM/logs/iclim.log
curl -s localhost:8000/metrics | grep ^iclim_
```

**Failure behaviour:** systemd restarts it 5 seconds after any exit. If the initial model load fails, the agent sets `iclim_model_loaded 0` and exits, and systemd keeps restarting it.

---

## 2. Model refresh: `iclim-model-refresh.service` + `.timer`

**What it does:** retrains the Isolation Forest on the full snapshot history, validates it, and swaps it in atomically.

| | |
|---|---|
| Code | `analysis/anomaly_training.py` |
| Schedule | `OnCalendar=*-*-* 03:00:00`, `Persistent=true` |
| Model settings | `n_estimators=200`, `contamination=0.05`, `random_state=42`, features `[cpu, mem, disk]` |
| Validation gate | At least 20 samples; anomaly rate on training data within 4–6% |
| Swap | Writes `anomaly_model.pkl.candidate`, then `os.replace()` (atomic on the same filesystem) |

The `.service` is **not enabled** on its own (`is-enabled` shows `disabled`). That's expected: only the timer is enabled, and the timer starts the service.

**Check it / run it now**

```bash
systemctl list-timers iclim-model-refresh.timer
sudo systemctl start iclim-model-refresh.service    # manual retrain
journalctl -u iclim-model-refresh -n 20 --no-pager
ls -l ~/projects/ICLIM/models/
```

**Failure behaviour:** if validation fails, the script raises an error and the unit ends in `failed` state. The current model stays in place.

---

## 3. AI worker: `iclim-ai-worker.service` + `.timer`

**What it does:** takes the most recent anomaly event, builds an evidence package, and calls the LLM twice: once for the Incident Explainer ("what happened?") and once for the Operational Assistant ("what should I check next?"). It stores the combined result.

| | |
|---|---|
| Code | `ai/ai_worker.py`, `ai/context_builder.py`, `ai/incident_explainer.py`, `ai/operational_assistant.py`, `ai/providers/`, `ai/result_store.py` |
| Schedule | `OnBootSec=2min`, `OnUnitActiveSec=5min` |
| Secrets | `EnvironmentFile=/etc/iclim-ai-worker.env` → `GROQ_API_KEY` (template: `deploy/systemd/iclim-ai-worker.env.example`) |
| Provider | Groq, model `openai/gpt-oss-20b` by default (`GROQ_MODEL` overrides) |
| Evidence | Prometheus `query_range` for CPU / memory / disk over the 5 minutes before the incident (60s step); `logs/iclim.log` lines in the same window, summarised |
| Writes | `logs/ai_incidents.jsonl` (history), `logs/latest_ai.json` (latest) |
| De-duplication | Skips the LLM call if the latest event's timestamp has already been processed |

**Check it / run it now**

```bash
systemctl list-timers iclim-ai-worker.timer
sudo systemctl start iclim-ai-worker.service
journalctl -u iclim-ai-worker -n 40 --no-pager
```

**Failure behaviour:** this is a oneshot job, so a failure (Groq unreachable, invalid JSON, missing key) only fails that one run. The next timer run tries again. Monitoring is unaffected.

---

## 4. AI Result API: `iclim-ai-result-api.service`

**What it does:** a minimal Python `http.server` that returns `logs/latest_ai.json` at `GET /ai/latest`. Grafana's Infinity data source reads it to render the explanation and recommendation tables.

| | |
|---|---|
| Code | `ai/result_api.py` |
| Bind | `0.0.0.0:8001` |
| Responses | `200` JSON; `404` if no result yet or wrong path; `500` if the file is not valid JSON |

**Check it**

```bash
curl -fsS localhost:8001/ai/latest | python3 -m json.tool | head -30
```

---

## 5. Node Exporter: `node_exporter.service`

**What it does:** exposes Linux host metrics (CPU time, memory, filesystems and more) for Prometheus. It is the independent cross-check against the ICLIM agent's own readings.

| | |
|---|---|
| Binary | `/usr/local/bin/node_exporter` (v1.12.1) |
| User | dedicated system user `node_exporter` (non-root, no login) |
| Endpoint | `:9100/metrics` |

```bash
curl -s localhost:9100/metrics | grep -m3 node_cpu_seconds_total
```

---

## 6. Prometheus: `prometheus.service`

**What it does:** scrapes `iclim` (:8000), `node_exporter` (:9100) and itself (:9090) every 15 seconds, and stores the results in its local TSDB.

| | |
|---|---|
| Binary + config | `/opt/prometheus/` (root-owned); config `/opt/prometheus/prometheus.yml` (repo copy: `deploy/prometheus/prometheus.yml`) |
| Data | `/var/lib/prometheus` (owned by `prometheus`) |
| Retention | 15 days (default) |
| Version | 3.13.3 |

```bash
curl -s localhost:9090/-/ready
curl -s 'localhost:9090/api/v1/query?query=up' | python3 -m json.tool
```

**Note:** the scrape interval (15s) and the agent's monitoring interval (~6s) are independent, so Prometheus only sees every second or third agent cycle. Counters still capture every cycle, because a counter's value accumulates between scrapes.

---

## 7. Grafana: `grafana-server.service`

**What it does:** displays the "ICLIM - Linux & Anomaly Monitoring" dashboard.

| | |
|---|---|
| Version | 13.2.2 (RPM package; unit file shipped with the package) |
| Override | `/etc/systemd/system/grafana-server.service.d/timeout.conf` → `TimeoutStartSec=5min` (repo: `deploy/systemd/grafana-server.service.d/`) |
| Data sources | Prometheus (`uid dfzwzcawaxnnkc`), Infinity plugin (`uid fg0lpomgtadj4d`); provisioning file in `deploy/grafana/provisioning/` |
| Dashboard | `deploy/grafana/dashboards/iclim-dashboard.json` |

**About the timeout override:** on the 1-vCPU VM, Grafana's plugin initialisation took longer than systemd's default start timeout, so the service was marked failed. Raising the timeout lets it start. It does not make plugin startup faster.

```bash
curl -s localhost:3000/api/health
```

---

## Log locations

| What | Where |
|---|---|
| ICLIM agent and training | `~/projects/ICLIM/logs/iclim.log` (rotated daily, 7 kept; JSONL files rotated at 10 MB, 5 kept; configs in `deploy/logrotate/`) and `journalctl -u iclim` |
| AI worker output | `journalctl -u iclim-ai-worker` |
| Prometheus / Node Exporter | `journalctl -u prometheus`, `journalctl -u node_exporter` |
| Grafana | `/var/log/grafana/` and `journalctl -u grafana-server` |

> The journal on the reference VM is **volatile** (no `/var/log/journal`), so `journalctl` history is lost on reboot. See [deployment.md](deployment.md#a10-keep-service-logs-across-reboots) to make it persistent.
