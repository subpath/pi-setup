# pi-setup

Raspberry Pi home media server provisioning tool using [pyinfra](https://pyinfra.com/).

## What this project does

Automates the full lifecycle of a Raspberry Pi home server:
1. **SD card prep** — writes user credentials, SSH, and WiFi config to a freshly flashed card
2. **Provisioning** — configures the Pi over SSH using pyinfra deploy scripts
3. **Operations** — day-to-day management (SSH, logs, restart, backup, etc.)

The media stack runs entirely in Docker and includes: Jellyfin, Portainer, Netdata, Homer, FileBrowser, Watchtower.

## Project layout

```
inventory.py          # pyinfra inventory: reads PI_HOST/PI_USER/PI_PASSWORD from env
justfile              # all commands — run `just` to list them
setup-sd.sh           # writes userconf.txt, ssh, wpa_supplicant.conf to SD boot partition
deploy/
  main.py             # full provisioning: includes all modules in order
  system.py           # apt update/upgrade, base packages, timezone
  security.py         # fail2ban, UFW, unattended-upgrades
  reliability.py      # log2ram (128M), hardware watchdog
  docker.py           # Docker CE install, user group, lazydocker
  media.py            # docker-compose.yml, Homer config, FileBrowser init, stack up
  backup.py           # restic install, backup script, daily cron at 03:00
```

## Environment

Copy `.env.example` to `.env` — `just` loads it automatically via `set dotenv-load := true`.

| Variable | Default | Purpose |
|---|---|---|
| `PI_HOST` | `raspberrypi.local` | Pi hostname or IP |
| `PI_USER` | `pi` | SSH user |
| `PI_PASSWORD` | — | SSH + SD card password |
| `WIFI_SSID` / `WIFI_PASSWORD` / `WIFI_COUNTRY` | — | SD card WiFi setup |
| `MEDIA_PATH` | `/mnt/media` | Mount point for media drive on Pi |
| `FB_PASSWORD` | `changeme12345` | FileBrowser admin password |
| `BACKUP_PATH` | `/mnt/backup` | Mount point for backup drive on Pi |
| `RESTIC_PASSWORD` | — | Restic repo encryption key |
| `TIMEZONE` | `Europe/Berlin` | Pi system timezone |

## Common commands

```bash
just setup          # install local deps (brew + uv + pre-commit) — run once
just sd-prep        # write SD card config (mounts at /Volumes/bootfs by default)
just wait           # poll until Pi is reachable
just deploy         # full provisioning run
just deploy-media   # re-deploy media stack only
just status         # show uptime, disk, running containers
just services       # print service URLs
just logs           # tail jellyfin logs (just logs <container> for others)
just restart        # restart whole stack (just restart <container> for one)
just update         # pull latest images and recreate containers
just backup         # run restic backup immediately
just ssh            # open interactive SSH session
```

## Development

```bash
just setup   # first-time setup
just lint    # run pre-commit (ruff + ty)
```

- Python 3.12, managed by `uv`
- Linting: `ruff` (format + lint), `ty` (type checking)
- Pre-commit runs on every commit

## Architecture notes

- **pyinfra runs on your local machine** and SSHes into the Pi — there is no agent on the Pi
- `inventory.py` is the pyinfra inventory file; pass it explicitly: `pyinfra inventory.py <deploy>`
- `deploy/main.py` uses `local.include()` to chain all modules — order matters (system → security → reliability → docker → media → backup)
- **UFW + Docker**: Docker bypasses UFW for bridge-networked container ports. UFW here protects host-mode services (Jellyfin DLNA on port 8096) and SSH. Portainer/Netdata/Homer/FileBrowser ports are explicitly opened too
- **FileBrowser** password is set by running the filebrowser container itself during provisioning (database is recreated each deploy)
- **Watchtower** auto-updates containers daily at 04:00
- **log2ram** reduces SD card wear by keeping `/var/log` in RAM (128M)
- **Restic backup** runs daily at 03:00, backs up `/opt/media`, retains 7 daily + 4 weekly snapshots

## Service ports

| Service | Port |
|---|---|
| Jellyfin | 8096 |
| Portainer | 9000 |
| Netdata | 19999 |
| Homer | 3000 |
| FileBrowser | 8234 |
