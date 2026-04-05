# pi-setup

Automated Raspberry Pi provisioning for a self-hosted home media server.
Turns a fresh Raspberry Pi OS install into a fully configured media server with a single command.

## What gets installed

| Layer | Tools |
|---|---|
| System | apt upgrade, curl, git, vim, htop, tmux, exfatprogs, timezone |
| Security | fail2ban, UFW firewall, unattended-upgrades |
| Reliability | log2ram (SD card wear reduction), hardware watchdog |
| Runtime | Docker + Docker Compose |
| Media stack | Jellyfin, Portainer, Netdata, Homer, FileBrowser, Watchtower |
| Backups | restic (daily cron at 03:00, 7-day / 4-week retention) |

## Services

| Service | Port | Purpose |
|---|---|---|
| Jellyfin | 8096 | Media server |
| Portainer | 9000 | Docker management |
| Netdata | 19999 | System monitoring |
| Homer | 3000 | Dashboard |
| FileBrowser | 8234 | File manager |

## Requirements

- macOS (for SD card prep; provisioning works from any OS)
- [just](https://just.systems/) — task runner
- [uv](https://docs.astral.sh/uv/) — Python package manager
- `brew` — for installing `openssl` and `sshpass`

## Quick start

### 1. Clone and configure

```sh
git clone https://github.com/yourusername/pi-setup.git
cd pi-setup
cp .env.example .env
# Edit .env with your Pi hostname, credentials, WiFi, and paths
```

### 2. Install local dependencies

```sh
just setup
```

### 3. Prepare the SD card

Flash Raspberry Pi OS Lite (64-bit) with Raspberry Pi Imager, then mount the boot partition and run:

```sh
just sd-prep
# or specify the mount point: just sd-prep /Volumes/bootfs
```

This writes `userconf.txt` (hashed password), enables SSH, and configures WiFi.

### 4. Boot and wait

Eject the SD card, insert it into the Pi, and power on. Then:

```sh
just wait
```

### 5. Provision

```sh
just deploy
```

Or run individual layers:

```sh
just deploy-system
just deploy-security
just deploy-reliability
just deploy-docker
just deploy-media
just deploy-backup
```

## Operations

```sh
just status        # uptime, disk usage, running containers
just services      # print all service URLs
just ssh           # open SSH session
just logs          # tail jellyfin logs (just logs <container> for others)
just restart       # restart the media stack
just update        # pull latest images and recreate containers
just backup        # run backup immediately
just backup-logs   # tail backup log
just reboot        # reboot the Pi
```

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Default | Description |
|---|---|---|
| `PI_HOST` | `raspberrypi.local` | Pi hostname or IP |
| `PI_USER` | `pi` | SSH username |
| `PI_PASSWORD` | — | SSH password |
| `WIFI_SSID` | — | WiFi network name |
| `WIFI_PASSWORD` | — | WiFi password |
| `WIFI_COUNTRY` | `DE` | WiFi regulatory country (ISO 3166-1 alpha-2) |
| `MEDIA_PATH` | `/mnt/media` | Path on Pi where media drive is mounted |
| `BACKUP_PATH` | `/mnt/backup` | Path on Pi where backup drive is mounted |
| `RESTIC_PASSWORD` | — | Password for restic backup encryption |

## Project structure

```
deploy/
  main.py        # Full deploy (includes all layers in order)
  system.py      # apt update/upgrade, base packages, timezone
  security.py    # fail2ban, UFW, unattended-upgrades
  reliability.py # log2ram, hardware watchdog
  docker.py      # Docker + Docker Compose
  media.py       # Docker Compose stack + Homer dashboard config
  backup.py      # restic install, repo init, backup script, cron job
inventory.py     # Reads PI_HOST/PI_USER/PI_PASSWORD from env
setup-sd.sh      # Writes userconf.txt, ssh flag, wpa_supplicant.conf
justfile         # Task runner commands
```
