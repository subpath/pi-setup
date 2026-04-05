set dotenv-load := true

PI_HOST       := env_var_or_default("PI_HOST", "raspberrypi.local")
PI_USER       := env_var_or_default("PI_USER", "pi")
PI_PASSWORD   := env_var_or_default("PI_PASSWORD", "")
COMPOSE_FILE  := "/opt/media/docker-compose.yml"

export SSHPASS := PI_PASSWORD
SSH            := "sshpass -e ssh -o StrictHostKeyChecking=no"
PYINFRA := "uv run pyinfra inventory.py --sudo"

# List available commands
default:
    @just --list

# Install all local dependencies (run once after cloning)
setup:
    brew install openssl sshpass
    uv sync --group dev
    uv run pre-commit install

# Run pre-commit on all files
lint:
    uv run pre-commit run --all-files

# ── SD card prep ──────────────────────────────────────────────────────────────

# Write user, SSH, and WiFi config to mounted SD card
# Usage: just sd-prep  OR  just sd-prep /Volumes/boot
sd-prep mount="/Volumes/bootfs":
    @./setup-sd.sh "{{mount}}"

# ── Connection ────────────────────────────────────────────────────────────────

# Wait for Pi to come online (polls every 5s)
wait:
    @echo "Waiting for {{PI_HOST}}..."
    @until {{SSH}} -o ConnectTimeout=2 {{PI_USER}}@{{PI_HOST}} true 2>/dev/null; do \
        printf '.'; sleep 5; \
    done
    @echo "\nPi is up!"

# Open SSH session
ssh:
    {{SSH}} {{PI_USER}}@{{PI_HOST}}

# ── Provisioning ──────────────────────────────────────────────────────────────

# Full provisioning (system → security → reliability → docker → media → backup)
deploy:
    {{PYINFRA}} deploy/main.py

# Base system only (apt, timezone)
deploy-system:
    {{PYINFRA}} deploy/system.py

# Docker only
deploy-docker:
    {{PYINFRA}} deploy/docker.py

# Security (fail2ban, UFW, unattended-upgrades)
deploy-security:
    {{PYINFRA}} deploy/security.py

# Reliability (log2ram, hardware watchdog)
deploy-reliability:
    {{PYINFRA}} deploy/reliability.py

# Media stack only (Jellyfin, Portainer, Netdata, Homer, FileBrowser, Watchtower)
deploy-media:
    {{PYINFRA}} deploy/media.py

# Backup config (restic + cron)
deploy-backup:
    {{PYINFRA}} deploy/backup.py

# ── Operations ────────────────────────────────────────────────────────────────

# Open lazydocker TUI on the Pi
lazydocker:
    {{SSH}} -t {{PI_USER}}@{{PI_HOST}} lazydocker

# Show Pi status (uptime, disk, running containers)
status:
    {{SSH}} {{PI_USER}}@{{PI_HOST}} \
        "uptime && echo '---' && df -h && echo '---' && docker ps"

# Print URLs for all services
services:
    @echo "Jellyfin     http://{{PI_HOST}}:8096"
    @echo "Portainer    http://{{PI_HOST}}:9000"
    @echo "Netdata      http://{{PI_HOST}}:19999"
    @echo "Homer        http://{{PI_HOST}}:3000"
    @echo "FileBrowser  http://{{PI_HOST}}:8234"

# Stream logs for a container (default: jellyfin)
logs container="jellyfin":
    {{SSH}} {{PI_USER}}@{{PI_HOST}} "docker logs -f {{container}}"

# Restart a container or the whole stack (e.g. just restart filebrowser)
restart container="":
    {{SSH}} {{PI_USER}}@{{PI_HOST}} "docker compose -f {{COMPOSE_FILE}} restart {{container}}"

# Pull latest images and recreate containers
update:
    {{SSH}} {{PI_USER}}@{{PI_HOST}} \
        "docker compose -f {{COMPOSE_FILE}} pull && docker compose -f {{COMPOSE_FILE}} up -d"

# Run backup now (don't wait for cron)
backup:
    {{SSH}} {{PI_USER}}@{{PI_HOST}} "sudo /usr/local/bin/pi-backup"

# Tail backup log
backup-logs:
    {{SSH}} {{PI_USER}}@{{PI_HOST}} "tail -f /var/log/pi-backup.log"

# Reboot the Pi
reboot:
    {{SSH}} {{PI_USER}}@{{PI_HOST}} sudo reboot
