# RADIUS EAP-TLS Synthetic Health Check 

A lightweight, containerized synthetic monitoring dashboard and HTTP health-check endpoint for **RADIUS EAP-TLS** authentication. It uses `eapol_test` to perform real certificate-based 802.1X authentication transactions against a RADIUS server, caches results to prevent flooding, and exposes both a web UI and standard HTTP status codes (`200`, `503`, `500`) for uptime monitoring tools (e.g., Uptime Kuma, Prometheus Blackbox Exporter, PRTG, Loadbalancers, or Zabbix etc).

---

## Features

- **Real EAP-TLS Transactions:** Executes end-to-end certificate authentication via `eapol_test`.
- **Built-in Rate Limiting & Locking:** Uses `flock` and a configurable cooldown cache (`COOLDOWN`) to prevent concurrent executions or accidental RADIUS flooding.
- **Monitoring-Friendly HTTP Codes:**
  - `200 OK` — Authentication succeeded (`SUCCESS`)
  - `503 Service Unavailable` — Authentication rejected or timed out (`FAILURE`)
  - `500 Internal Server Error` — Configuration, lock, or execution error (`ERROR`)
- **Hardened Container Architecture:**
  - Runs as a non-root user (`UID/GID 10001`)
  - Read-only root filesystem with an isolated `tmpfs` mount for lock/state files
  - All Linux capabilities dropped (`cap_drop: ALL`) and `no-new-privileges` enabled
  - Private keys and RADIUS shared secrets mounted via Docker `secrets` with `0400` permissions

---

## Repository Structure

```text
.
├── app.py                # Flask web dashboard and HTTP health check wrapper
├── check_radius.sh       # Hardened bash runner with flock locking & cooldown cache
├── Dockerfile            # Multi-step slim Python image with eapol_test & Gunicorn
├── docker-compose.yml    # Hardened container configuration with secrets & configs
├── eapol_conf            # wpa_supplicant / eapol_test EAP-TLS configuration
└── certs/                # (Git-ignored) Local directory for CA, client cert, key, & secret
```

---

## Prerequisites

- Docker Engine & Docker Compose v2+
- A valid **CA certificate** (`ca.pem`), **client/machine certificate** (`computer.pem`), and **private key** (`computer.key`) trusted by your RADIUS server
- Network access from the Docker host to your RADIUS server on UDP port `1812` (or custom port)
- A matching RADIUS client entry configured on your RADIUS server with a shared secret

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/thatacebreaker-beep/radiusmon-python.git
cd /radiusmon-python
```

### 2. Prepare Certificates and Secrets
Create a restricted `certs/` directory and place your certificates, private key, and RADIUS shared secret inside:

```bash
mkdir -p certs
chmod 700 certs

# Add your PEM files and shared secret
cp /path/to/ca.pem certs/ca.pem
cp /path/to/computer.pem certs/computer.pem
cp /path/to/computer.key certs/computer.key
printf '%s' 'your-radius-shared-secret' > certs/radius_secret.txt

# Lock down sensitive files
chmod 644 certs/ca.pem certs/computer.pem
chmod 600 certs/computer.key certs/radius_secret.txt
```

> **Note:** Ensure `certs/` is listed in your `.gitignore` so private keys and secrets are never committed to version control.

### 3. Configure `eapol_conf`
Edit `eapol_conf` to match the Subject Alternative Name (SAN) or Common Name (CN) of your client certificate:

```ini
ap_scan=0
network={
    key_mgmt=IEEE8021X
    eapol_flags=0
    eap=TLS
    identity="host/pc01.domain.local"
    ca_cert="/etc/eapol_test/ca.pem"
    client_cert="/etc/eapol_test/computer.pem"
    private_key="/etc/eapol_test/computer.key"
}
```
https://manpages.debian.org/testing/eapoltest/eapol_test.8.en.html

### 4. Configure Environment Variables
Update the `environment` and `ports` sections in `docker-compose.yml` to match your environment:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RADIUS_IP` | `192.168.0.1` | Target RADIUS server IP address or host (requires working DNS) |
| `RADIUS_PORT` | `1812` | Target RADIUS authentication port (UDP) |
| `RADIUS_SECRET_FILE` | `/run/secrets/radius_secret` | Path to the mounted RADIUS shared secret |
| `TIMEOUT` | `6` | Maximum timeout (in seconds) for `eapol_test` |
| `COOLDOWN` | `15` | Minimum interval (in seconds) between live RADIUS checks |
| `SCRIPT_PATH` | `/usr/local/bin/check_radius.sh` | Path to the health-check runner script |

### 5. Build and Start
```bash
docker compose up -d --build
```

Access the dashboard at `http://<host-ip>:8082/`.

---

## Security Recommendations

- **Reverse Proxy & TLS:** Place Nginx, Caddy, or Traefik in front of port `8082` to enforce HTTPS and restrict access via IP allowlisting or authentication (OIDC/Basic Auth), as `eapol_test` output contains diagnostic session details.
- **Secret Management:** Never pass `RADIUS_SECRET` as a plaintext environment variable in production; always use `RADIUS_SECRET_FILE` backed by Docker secrets.

---

## Recommended `.gitignore`

```gitignore
certs/
*.pem
*.key
*.crt
*secret*
__pycache__/
*.py[cod]
.env
```

---

## License

JJB - raccoon-cloud.nl — see...  `Nah its free for all` no further details.
