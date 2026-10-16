# Engineering Decisions

These are the decisions that shaped ICLIM and the reason for each. They are condensed from the per-phase decision logs kept during development. The final section records known limitations, the things this design does not handle yet, with the improvement each would need.

---

## Overall approach

| Decision | Why |
|---|---|
| Build in stages, each extending the last (monitoring → bootstrap → Docker → Terraform → CI/CD → observability → AI) | Each stage can be validated and explained on its own; nothing earlier gets rewritten |
| Develop on Windows, validate on real Linux (CentOS Stream 9) before merging | Production Linux behaviour (systemd, permissions, SELinux, paths) only shows up on Linux |
| Branch flow `feature/*` → `dev` → `main` | `dev` is the integration point where CI runs; `main` only receives validated work |
| Prefer the simplest design that can be explained and tested | Avoid adding a technology just because it is popular |

## Detection and severity

| Decision | Why |
|---|---|
| Isolation Forest on `[cpu, mem, disk]` | Unsupervised, so no labelled incident data is needed. Fast, and works on a small feature set |
| `contamination = 0.05` | Treat roughly the most unusual 5% of history as anomalous |
| **Severity is separate from detection** | The model only says "unusual"; it cannot say how much it matters. A deterministic rule (persistence + resource impact) gives severity that is explainable and testable |
| Persistence threshold of 30 s before WARNING/CRITICAL | A single spike is noise; something that persists is an incident |
| ICLIM severity names (UNUSUAL / WARNING / CRITICAL) are separate from Python log levels | A log line at level `WARNING` can carry ICLIM severity `UNUSUAL`; mixing them up misleads both humans and the AI |

## Model lifecycle

| Decision | Why |
|---|---|
| Retrain daily from history (systemd timer, 03:00) | A stale model flagged **34.66%** of 11,110+ observations as anomalous against an expected 5%. The model had been trained on the first ~7,640 samples, and the system's normal behaviour had moved since. Retraining fixed the cause; tweaking thresholds would only have hidden it |
| Validate a candidate model, then swap it atomically (`.candidate` → `os.replace`) | A bad or half-written model file must never become the live model |
| Hot reload on file change (mtime) | Retraining takes effect without restarting the monitoring service |
| Bootstrap on first start (30 live samples → initial model) | A fresh deployment starts without manual preparation. Live samples are more representative than synthetic data |

## Runtime and operations

| Decision | Why |
|---|---|
| systemd for every long-running service, systemd timers for scheduled jobs (no cron) | One way to manage, log (`journalctl`), restart and inspect everything; `Persistent=true` catches up on missed runs |
| Prometheus binaries/config root-owned in `/opt/prometheus`, data owned by the `prometheus` user in `/var/lib/prometheus` | Separates application files from runtime data; the service account cannot modify its own binaries or config |
| Node Exporter and Prometheus run as dedicated non-login system users | Least privilege |
| Configuration in YAML; only operational settings (`INTERVAL`, `HOSTNAME`, `LOG_LEVEL`) overridable via environment | Paths stay identical everywhere; deployments can tune behaviour without rebuilding |
| Grafana start timeout raised to 5 min via a drop-in override | Plugin start-up exceeded the default timeout on the 1-vCPU VM. This is recorded as a workaround, not a fix |

## Observability

| Decision | Why |
|---|---|
| Node Exporter for host metrics and a custom exporter for application metrics | Clear ownership: Node Exporter describes the machine, ICLIM describes itself. Each also cross-checks the other |
| Counters for events (`iclim_anomaly_total`, `iclim_monitoring_cycles_total`), gauges for state | Counters survive scrape gaps; dashboards use `increase(...[5m])` for recent activity |
| Dashboard limited to the agreed scope (host health → app health → anomalies → AI) | Every panel answers an operational question; no decorative panels |

## AI layer

| Decision | Why |
|---|---|
| AI explains and recommends; it never detects or remediates | The detection pipeline is deterministic and testable. Keeping the LLM out of the control path limits the blast radius of a wrong answer |
| Separate worker process on a timer, not inside the agent | LLM latency, outages or bad output cannot affect real-time monitoring |
| Evidence package = anomaly event + 5-minute Prometheus window + summarised agent logs | The LLM gets focused, real evidence, not the whole system |
| Prompts require Evidence / Interpretation / Unknowns separation and ban causal claims without evidence | An honest "unknown" is more useful in an incident than a confident wrong root cause |
| Structured JSON output, validated in code | Free text can't be reliably displayed, stored or tested |
| Provider abstraction (`AIProvider`) with Groq as the current implementation | The model or provider can be swapped without touching the explainer or assistant logic |
| Bounded AI state → Prometheus gauges; free text → REST API → Grafana Infinity | Free text as Prometheus labels would create unbounded cardinality |

## Infrastructure and CI/CD

| Decision | Why |
|---|---|
| Terraform for Azure (RG, VNet, subnet, NSG, public IP, NIC, VM) | Repeatable, version-controlled infrastructure instead of portal clicks |
| Remote state in Azure Storage | The GitHub runner and the laptop share one state; no state file to lose locally |
| Three pipelines: A (CI on every push to `dev`), B (Terraform validate/plan, manual), C (apply → deploy → verify → destroy, manual) | Each pipeline has one responsibility. Cloud-touching pipelines are manual to control cost |
| Cleanup as a **separate job** with `if: always()` | When cleanup was the last step of the deploy job, any earlier failure skipped it and left billable resources running |
| Ephemeral Azure infrastructure | The proof costs minutes of compute instead of a VM running permanently |
| Service principal + GitHub secrets for authentication | Non-interactive credentials, kept out of source control |

---

## Known limitations

These are documented deliberately. Each one has a clear next step.

| # | Limitation | Effect | Next step |
|---|---|---|---|
| 1 | **The model validation gate is weak.** The 4–6% anomaly-rate check runs on the training data itself, and Isolation Forest's `contamination` setting forces roughly 5% there by design | The gate catches degenerate models (too few samples, heavily duplicated data) but not a model that performs badly on new data | Validate on a held-out recent window, or compare candidate and current model on the last N hours before swapping |
| 2 | **The training window is set by log rotation, not by design.** Retraining reads the current `snapshot_history.jsonl`, which logrotate truncates at 10 MB. The window also includes past anomalies | Right after a rotation, the next retrain sees only the samples collected since, which may be a thin baseline. Repeated incidents gradually become "normal" | Train on an explicit rolling window (e.g. the last 7 days, read across rotated files) and exclude samples already flagged as anomalous |
| 3 | **Resource impact uses the highest of CPU / memory / disk** | With root disk at ≥80% (as on the reference VM), every persistent anomaly becomes at least WARNING, even if disk is not what changed | Score impact on the metric(s) that are actually anomalous |
| 4 | **Duration is an estimate.** It is calculated as consecutive cycles × 5 s, but a real cycle takes ~6 s (1 s CPU sample + 5 s sleep) | Reported durations run about 15–20% low | Measure elapsed time between the first and the current anomalous timestamp |
| 5 | **ICLIM and Prometheus CPU values differ.** ICLIM uses a 1-second `psutil` sample; the dashboard and AI evidence use `rate(...[1m])` averages | In the end-to-end test, ICLIM recorded 100% while Prometheus showed ~84%. Both are correct for their window | Documented; the AI was correctly instructed to report it as an unexplained discrepancy rather than guess |
| 6 | **`iclim_agent_status` is only ever set to 1** | If the agent dies, the series goes stale instead of showing 0 | Use `up{job="iclim"}` as the liveness signal |
| 7 | **The AI worker explains one incident per run.** Fixed on 16 Oct: events are grouped into incidents and the most severe one is explained (previously the last reading, so a CRITICAL incident ending in a short blip was shown as UNUSUAL); UNUSUAL-only incidents are skipped (they had used up Groq's 200k tokens/day) | Two separate incidents within one 5-minute timer gap → only the newer one is explained | Process every unprocessed incident, not just the latest |
| 8 | **No alerting.** There are no Prometheus alert rules and no Alertmanager | Detection is visible in Grafana and logs, but nobody is notified | Add alert rules for `iclim_anomaly_total{severity="critical"}` and `up == 0`, routed via Alertmanager |
| 9 | **CI checks start-up only.** Pipeline A asserts one log line; there are no unit tests | Logic regressions (severity rules, parsing) are not caught automatically | Add `pytest` tests for `classify_anomaly`, the context builder and AI output validation |
| 10 | **The Docker image predates the AI layer** | The containerised path runs monitoring only | Either add `ai/` to the image or keep containers scoped to the agent and say so (current choice) |
| 11 | **Inside a container, "what is monitored" is mixed.** `psutil` reads host-wide CPU and memory from `/proc`, but `disk_usage("/")` measures the container's overlay filesystem. Port 8000 is not published, so Prometheus cannot scrape it | The containerised agent is a deployment proof, not an equivalent to the systemd runtime | Publish 8000, mount the host root read-only and measure that path, or keep the container explicitly scoped to deployment validation |
| 12 | **Single node, local TSDB, no HA** | A VM failure loses the monitoring | Out of scope for this project |
