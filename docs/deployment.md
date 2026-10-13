# Deploying ICLIM

There are two deployment paths, and they serve different purposes (see [architecture.md](architecture.md#2-two-environments-two-purposes)):

- **Part A — Full runtime on a Linux VM.** The complete stack: agent, model refresh, AI worker, AI API, Node Exporter, Prometheus and Grafana. Tested on CentOS Stream 9.
- **Part B — Automated Azure deployment proof.** Terraform and GitHub Actions provision an Ubuntu VM, deploy the containerised agent, verify it, then destroy everything.

Commands assume a user called `akashp` and a project path of `/home/akashp/projects/ICLIM`, which match the unit files in `deploy/systemd/`. If your user or path differs, edit `User=`, `WorkingDirectory=` and `ExecStart=` in those files first.

---

## Part A — Full runtime on CentOS Stream 9 / RHEL 9

### A0. Prerequisites

- A CentOS Stream 9 (or RHEL 9 compatible) VM. At least 2 GB RAM is recommended; the reference VM runs with 1 vCPU and 1.6 GB, which is tight once Grafana is running.
- `sudo` access and outbound internet.
- A Groq API key for the AI layer (free tier is enough for testing).

### A1. System packages and code

```bash
sudo dnf install -y git python3.12 python3.12-pip tar curl
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/akashpagar1865/ICLIM.git
cd ICLIM
```

### A2. Python environment

```bash
python3.12 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/python -m compileall -q agents analysis ai utils && echo "syntax OK"
```

### A3. Smoke test in the foreground (optional but recommended)

```bash
venv/bin/python -m agents.realtime_anomaly_agent
```

On a fresh clone you should see bootstrap progress (`1/30 … 30/30`), model training, then `First snapshot collected` and `System Normal` lines every ~6 seconds. Press `Ctrl+C` to stop.

### A4. Install the ICLIM services

```bash
sudo cp deploy/systemd/iclim.service \
        deploy/systemd/iclim-model-refresh.service deploy/systemd/iclim-model-refresh.timer \
        deploy/systemd/iclim-ai-worker.service deploy/systemd/iclim-ai-worker.timer \
        deploy/systemd/iclim-ai-result-api.service \
        /etc/systemd/system/

# Secret for the AI worker: root-owned and readable only by root
sudo cp deploy/systemd/iclim-ai-worker.env.example /etc/iclim-ai-worker.env
sudo vi /etc/iclim-ai-worker.env                        # paste your real GROQ_API_KEY
sudo chown root:root /etc/iclim-ai-worker.env
sudo chmod 600 /etc/iclim-ai-worker.env

sudo systemctl daemon-reload
sudo systemctl enable --now iclim.service iclim-ai-result-api.service
sudo systemctl enable --now iclim-model-refresh.timer iclim-ai-worker.timer
```

Enable the **timers**, not the oneshot services; each timer starts its service on schedule.

**Verify:**

```bash
systemctl is-active iclim iclim-ai-result-api
systemctl list-timers 'iclim-*'
curl -s localhost:8000/metrics | grep ^iclim_agent_status
```

### A5. Node Exporter

```bash
NE_VER=1.12.1
cd /tmp
curl -LO https://github.com/prometheus/node_exporter/releases/download/v${NE_VER}/node_exporter-${NE_VER}.linux-amd64.tar.gz
tar xzf node_exporter-${NE_VER}.linux-amd64.tar.gz
sudo cp node_exporter-${NE_VER}.linux-amd64/node_exporter /usr/local/bin/
sudo useradd --system --no-create-home --shell /sbin/nologin node_exporter

cd ~/projects/ICLIM
sudo cp deploy/systemd/node_exporter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
curl -s localhost:9100/metrics | head -3
```

### A6. Prometheus

```bash
PROM_VER=3.13.3
cd /tmp
curl -LO https://github.com/prometheus/prometheus/releases/download/v${PROM_VER}/prometheus-${PROM_VER}.linux-amd64.tar.gz
tar xzf prometheus-${PROM_VER}.linux-amd64.tar.gz
sudo mkdir -p /opt/prometheus /var/lib/prometheus
sudo cp prometheus-${PROM_VER}.linux-amd64/{prometheus,promtool} /opt/prometheus/
sudo useradd --system --no-create-home --shell /sbin/nologin prometheus

cd ~/projects/ICLIM
sudo cp deploy/prometheus/prometheus.yml /opt/prometheus/prometheus.yml
/opt/prometheus/promtool check config /opt/prometheus/prometheus.yml

# Binaries and config stay root-owned; only the data directory belongs to the service user
sudo chown -R root:root /opt/prometheus
sudo chown -R prometheus:prometheus /var/lib/prometheus

sudo cp deploy/systemd/prometheus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now prometheus
```

**Verify:** all three targets should report `up`:

```bash
curl -s localhost:9090/api/v1/targets | python3 -m json.tool | grep -E '"job"|"health"'
```

### A7. Grafana and the dashboard

```bash
sudo tee /etc/yum.repos.d/grafana.repo > /dev/null <<'EOF'
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
sudo dnf install -y grafana

# Start-timeout override (plugin start-up is slow on small VMs)
sudo mkdir -p /etc/systemd/system/grafana-server.service.d
sudo cp deploy/systemd/grafana-server.service.d/timeout.conf /etc/systemd/system/grafana-server.service.d/

# Infinity plugin (used by the AI narrative tables)
sudo grafana cli plugins install yesoreyeram-infinity-datasource

# Data sources with fixed UIDs that the dashboard JSON expects
sudo cp deploy/grafana/provisioning/datasources/iclim-datasources.yaml /etc/grafana/provisioning/datasources/
sudo chown root:grafana /etc/grafana/provisioning/datasources/iclim-datasources.yaml

sudo systemctl daemon-reload
sudo systemctl enable --now grafana-server
curl -s localhost:3000/api/health
```

**Import the dashboard:** open `http://<vm-ip>:3000` (default login `admin` / `admin`, then change it). Go to **Dashboards → New → Import**, upload `deploy/grafana/dashboards/iclim-dashboard.json`, and save.

> The dashboard was exported from Grafana 13.2.2 in the v2 dashboard schema. It needs a Grafana version that supports that schema. The data source UIDs in the provisioning file must match the UIDs in the JSON, otherwise panels show "data source not found".

### A8. Log rotation

```bash
sudo cp deploy/logrotate/iclim-app deploy/logrotate/iclim-data /etc/logrotate.d/
sudo logrotate -d /etc/logrotate.d/iclim-app      # dry run, shows what would happen
```

### A9. Firewall: Grafana reachable from the local network only

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="3000" protocol="tcp" accept'
sudo firewall-cmd --permanent --remove-service=cockpit    # cockpit's rule opens 9090, which is Prometheus here
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

Only Grafana (3000) should be reachable from other machines, and only from the home subnet. Ports 8000, 8001, 9090 and 9100 have no authentication and are for local use. See [security.md](security.md).

### A10. Keep service logs across reboots

By default the journal on this VM is volatile, so `journalctl` history is lost at every reboot. To make it persistent:

```bash
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
journalctl --list-boots
```

### A11. End-to-end check (also the demo)

```bash
# 1. Generate 40 seconds of CPU load
timeout 40s python3 -c "while True: pass" &

# 2. Watch severity escalate: UNUSUAL (<30s) → CRITICAL (≥30s with CPU ≥ 90%)
journalctl -u iclim -f            # Ctrl+C when done

# 3. Run the AI worker now instead of waiting for the timer
sudo systemctl start iclim-ai-worker.service
curl -fsS localhost:8001/ai/latest | python3 -m json.tool | head -40
```

Then check the Grafana **ICLIM Agent Metrics** and **AI Analysis** rows.

### Troubleshooting

| Symptom | Check |
|---|---|
| `iclim` keeps restarting | `journalctl -u iclim -n 50`. Usually a missing package in the venv or a bad path in the unit file |
| Unit fails with `Permission denied` on `venv/bin/python` | SELinux on RHEL-family systems can block systemd from running binaries in home directories. `sudo ausearch -m avc -ts recent`, then fix the label or the path |
| AI worker: `GROQ_API_KEY environment variable is not configured` | `/etc/iclim-ai-worker.env` is missing or malformed. Check with `sudo cat /etc/iclim-ai-worker.env` |
| AI worker: `Anomaly file not found` | No anomaly has happened yet. Run the load test in A11 |
| Grafana fails to start (timeout) | Confirm the `timeout.conf` override is installed, then run `systemctl daemon-reload` |
| Prometheus target `iclim` is `down` | Is `iclim.service` running? `curl localhost:8000/metrics` |

---

## Part B — Automated Azure deployment proof

### What it does

Pipeline C (`.github/workflows/pipeline-c-full-validation.yml`):

1. Runs `terraform apply` to create a resource group, VNet, subnet, NSG, public IP, NIC and Ubuntu 24.04 VM (`Standard_D2ls_v6`, Sweden Central).
2. Waits for SSH and copies the application tarball to the VM.
3. Installs Docker, builds the image, runs the container, and verifies it from logs.
4. Runs `terraform destroy` in a separate cleanup job that **always** runs, even if deployment failed.

### One-time setup

**1. Remote state storage.** Terraform state is kept in Azure Storage (see `terraform/backend.tf`) so the GitHub runner and your laptop share one state. Create it once:

```bash
az group create -n iclim-tfstate-rg -l swedencentral
az storage account create -n iclimtfstate1865 -g iclim-tfstate-rg -l swedencentral --sku Standard_LRS
az storage container create -n tfstate --account-name iclimtfstate1865
```

**2. Service principal** that GitHub Actions uses to log in to Azure:

```bash
az ad sp create-for-rbac --name iclim-github \
  --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID> \
  --json-auth
```

**3. GitHub repository secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `AZURE_CREDENTIALS` | The JSON output of the command above |
| `SSH_PRIVATE_KEY` | The private key matching `terraform/keys/iclim_ed25519.pub` |

### Run it

GitHub → **Actions** → **Full Validation** → **Run workflow**. Pipeline B (**Terraform Infrastructure Validation**) runs `init`, `fmt`, `validate` and `plan` without creating anything.

### Run Terraform from your own machine (optional)

```bash
az login
cd terraform
terraform init
terraform plan
terraform apply      # creates billable resources
terraform destroy    # always clean up afterwards
```
