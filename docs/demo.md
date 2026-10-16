# ICLIM Demo Guide

A 5–7 minute live demo of ICLIM for interviews and recordings: what to set up, what to run, what to say, and what to do if something goes wrong.

The demo creates a **controlled CPU incident** and shows the full chain:

**load → ICLIM detects it → severity escalates to CRITICAL → the AI explains it → the result appears in Grafana**

---

## 1. Before the demo (10 minutes earlier)

1. **Start the VM** and SSH in. Then:
   ```bash
   cd ~/projects/ICLIM && git pull
   bash scripts/run_demo.sh --check
   ```
   Every line should say `active` / `ready`.
2. **Open three things side by side:**
   - Terminal: SSH session in `~/projects/ICLIM`
   - Browser tab 1: Grafana dashboard *ICLIM - Linux & Anomaly Monitoring*, time range **Last 15 minutes**, auto-refresh **10s**
   - Browser tab 2: the GitHub repo README (architecture diagram)
3. **Don't run test incidents on demo day.** Each AI explanation uses Groq's free daily quota (200k tokens/day). Two or three runs are fine; twenty are not.
4. **Let the system be quiet for 5 minutes** before starting, so the incident stands out on the graphs.

---

## 2. Run it

```bash
bash scripts/run_demo.sh
```

The script runs six steps by itself and prints a heading for each:

| Step | What happens | Takes |
|---|---|---|
| 1 | Checks every service is running | 2 s |
| 2 | Starts one busy loop per CPU for 75 s (stops on its own) | – |
| 3 | Shows ICLIM's log live: UNUSUAL lines, then CRITICAL | ~80 s |
| 4 | Summarises what ICLIM recorded (highest severity, duration, CPU) | 1 s |
| 5 | Runs the AI worker immediately instead of waiting for the 5-min timer (asks for your sudo password) | ~10 s |
| 6 | Prints the AI's answer: severity, priority, explanation, unknowns, suggested checks | 1 s |

If it ends with *"Did not reach WARNING/CRITICAL"*, run a longer load:
```bash
DEMO_SECONDS=90 bash scripts/run_demo.sh
```

---

## 3. What to say (talk track)

**0:00–0:45 · The pitch**
> "ICLIM is a Linux monitoring platform I built. It watches CPU, memory and disk, uses machine learning to spot unusual behaviour, decides how serious it is with simple rules, shows everything in Prometheus and Grafana, and uses an AI model to explain incidents in plain English. The AI only explains and suggests; a human decides."

**0:45–1:45 · The architecture** (README diagram)
> "The agent runs as a systemd service and checks the machine every ~6 seconds. An Isolation Forest model says normal or unusual. Separate rules decide severity. Prometheus scrapes the agent and Node Exporter; Grafana shows it. Every 5 minutes an AI worker picks up the latest serious incident, gathers evidence and asks the LLM for an explanation."

**1:45–4:00 · Live incident** (start the script, switch between terminal and Grafana)
> "I'm loading both CPUs to 100% for 75 seconds."
> *(UNUSUAL lines appear)* "It's unusual but short, under 30 seconds, so it's UNUSUAL, not an alert."
> *(CRITICAL appears)* "Now it has lasted 30 seconds and CPU is above 90%, so it's CRITICAL. Severity comes from duration plus impact, not from the model guessing."
> *(Grafana)* "Top row: the host from Node Exporter. Middle row: ICLIM's own health and anomaly counts. Both agree."

**4:00–5:30 · The AI explanation** (step 6 output, then Grafana AI row)
> "The AI got real evidence: the incident, 5 minutes of Prometheus data and the agent's log lines. It says what happened, how strong the evidence is, what's still unknown, and what to check next."
> "Notice it doesn't invent a root cause. When ICLIM said 100% and Prometheus said 97%, it called that a difference it couldn't explain. The real reason is that ICLIM takes a 1-second sample and Prometheus averages over 1 minute. I'd rather it say 'unknown' than guess."

**5:30–6:30 · The engineering behind it** (pick two)
- Model retrains nightly through a systemd timer, and is swapped in safely without a restart.
- Terraform plus GitHub Actions build an Azure VM, deploy the agent in Docker, check it, and **always** destroy it, so the cloud cost stays near zero.
- Real bugs I found and fixed: CI caught a bootstrap bug that only shows on fresh machines; the AI was explaining the last blip instead of the whole incident; noisy alerts burned the AI quota, so only WARNING/CRITICAL now go to the AI.

**6:30–7:00 · Close**
> "It's a single-node project, with no alert routing or high availability. Those limits are documented in the repo, along with how I'd add them."

---

## 4. If something goes wrong

| Problem | What to do and say |
|---|---|
| Pre-flight says a service is not active | `sudo systemctl start <name>`, rerun `--check`. If it won't start, use the backup video. |
| Stays UNUSUAL, never CRITICAL | `DEMO_SECONDS=90 bash scripts/run_demo.sh`. Explain: "CRITICAL needs 30 s of persistence; under full load the agent's own cycle slows down." |
| AI step fails with **429 rate limit** | Show the last saved result: `curl -s localhost:8001/ai/latest \| python3 -m json.tool \| head -30`. Say: "This is the free-tier quota. It's actually why I added the severity filter." |
| Grafana slow or blank | Use the terminal output and the API; show the README screenshots. |
| VM won't boot / no network | Play the **backup recording** (below) and walk through the README. |

---

## 5. Record a backup video

Record one clean run so you always have something to show.

- **Windows:** press `Win + G` (Xbox Game Bar) → Capture → Record, or use OBS Studio.
- Record the terminal running `bash scripts/run_demo.sh`, then 30 seconds of the Grafana dashboard.
- Keep it under 4 minutes. Store it outside the repo (video files are large).

---

## 6. Questions to expect after the demo

1. Why Isolation Forest, and why separate severity rules from the model?
2. What happens if the model goes stale? *(34.66% anomaly story → nightly retrain)*
3. Why does ICLIM say 100% when Prometheus says 97%?
4. What happens if Groq is down? *(the worker is separate; monitoring keeps running)*
5. How would you add alerting? *(Prometheus alert rules + Alertmanager)*
6. Why is Azure destroyed after every run?
7. What would you change to run this on 50 servers?
