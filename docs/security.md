# Security Posture

ICLIM treated security as part of each phase rather than a separate hardening stage at the end. For every new component, four questions were asked: what are the risks, what must be done now, what can wait, and how would the choice be explained?

This page records what is in place and what is not.

---

## In place

| Area | Control |
|---|---|
| **Secrets** | Groq API key only in `/etc/iclim-ai-worker.env` (root-owned, mode 600, loaded by systemd). Azure and SSH credentials only in GitHub repository secrets. `.gitignore` excludes `*.tfvars`, state files, private keys and env files |
| **Least privilege (services)** | Node Exporter, Prometheus and Grafana run as dedicated non-login system users. Prometheus binaries and config are root-owned; its service user can only write its data directory |
| **AI safety** | The AI layer has no ability to execute commands, restart services or change configuration. It reads evidence and writes JSON. A human acts |
| **Untrusted input** | Log content is treated as untrusted. Logs are parsed and summarised in code before reaching the LLM, and are never executed |
| **Runtime VM firewall** | firewalld active; Grafana (3000) allowed only from `192.168.1.0/24` via a rich rule |
| **Azure VM access** | SSH key authentication only; password authentication disabled |
| **Azure exposure window** | Infrastructure exists only for the duration of a pipeline run, then `terraform destroy` always runs |
| **Terraform state** | Stored in Azure Storage, not on a laptop or in Git |
| **CI credentials** | A dedicated service principal, not a personal account |

---

## Known gaps

| # | Gap | Risk | Planned fix |
|---|---|---|---|
| 1 | **NSG allows SSH (22) from any source** (`source_address_prefix = "*"` in `terraform/main.tf`) | The ephemeral VM is exposed to internet-wide SSH scanning while it exists | Restrict to the GitHub runner's IP for that run, or use Azure Bastion / just-in-time access |
| 2 | **Container runs as root** (no `USER` in the `Dockerfile`) | A container escape or app compromise starts with root inside the container | Add a non-root user in the image and set ownership on `/app/logs` and `/app/models` |
| 3 | **ICLIM services run as a personal login user** (`akashp`), not a dedicated service account | The services can access everything that user can | Create an `iclim` system user and move the project to `/opt/iclim` |
| 4 | **Ports 8000, 8001, 9090 and 9100 bind to all interfaces with no authentication or TLS.** firewalld blocks them from the network, except 9090: the default `cockpit` service rule opens 9090/tcp, and on this VM 9090 is Prometheus | Prometheus (UI and API) is reachable unauthenticated from the home network | Remove the `cockpit` firewalld service; bind local-only services to `127.0.0.1` as defence in depth |
| 5 | **Pipeline C disables SSH host key checking** (`StrictHostKeyChecking=no`) | A man-in-the-middle at first connection would not be detected | Read the host key from the VM through Azure (`az vm run-command`) and pin it in `known_hosts` |
| 6 | **Service principal secret instead of OIDC federation** | A long-lived secret exists that could leak | Switch `azure/login` to OpenID Connect with a federated credential (no stored secret) |
| 7 | **Service principal role scope** | Contributor at subscription scope (as set up in [deployment.md](deployment.md)) is broader than the pipeline needs | Scope it to the ICLIM resource groups |
| 8 | **Actions pinned to major versions** (`@v4`), not commit SHAs | A compromised upstream tag could change what runs | Pin third-party actions to full commit SHAs |
| 9 | **Prompt injection** | Log lines reach the LLM prompt. Today they are written only by ICLIM itself and contain numbers, so the risk is low, but this would change if system logs were added | Keep summarising in code; never let model output trigger actions (already true) |

None of these gaps are hidden. Items 1 and 2 are the ones most visible from the repo, so they come first.
