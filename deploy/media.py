import io
import os
from pyinfra.operations import files, server

MEDIA_PATH = os.environ.get("MEDIA_PATH", "/mnt/media")
PI_HOST = os.environ.get("PI_HOST", "raspberrypi.local")
FB_PASSWORD = os.environ.get("FB_PASSWORD", "admin")

COMPOSE = f"""\
services:

  # ── Media server ──────────────────────────────────────────────────────────
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    network_mode: host   # required for DLNA multicast discovery
    volumes:
      - /opt/media/jellyfin/config:/config
      - /opt/media/jellyfin/cache:/cache
      - {MEDIA_PATH}:/media:ro
    restart: unless-stopped
    environment:
      - JELLYFIN_PublishedServerUrl=http://{PI_HOST}:8096

  # ── Docker management ─────────────────────────────────────────────────────
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt/media/portainer/data:/data


  # ── System monitoring ─────────────────────────────────────────────────────
  netdata:
    image: netdata/netdata:latest
    container_name: netdata
    restart: unless-stopped
    pid: host
    ports:
      - "19999:19999"
    cap_add:
      - SYS_PTRACE
      - SYS_ADMIN
    security_opt:
      - apparmor:unconfined
    volumes:
      - /etc/passwd:/host/etc/passwd:ro
      - /etc/group:/host/etc/group:ro
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /etc/os-release:/host/etc/os-release:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - netdata-config:/etc/netdata
      - netdata-lib:/var/lib/netdata
      - netdata-cache:/var/cache/netdata


  # ── Homelab dashboard ─────────────────────────────────────────────────────
  homer:
    image: b4bz/homer:latest
    container_name: homer
    restart: unless-stopped
    ports:
      - "3000:8080"
    volumes:
      - /opt/media/homer/assets:/www/assets
    user: "1000:1000"


  # ── File manager ─────────────────────────────────────────────────────────
  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    restart: unless-stopped
    ports:
      - "8234:80"
    volumes:
      - /home/pi:/srv/home
      - {MEDIA_PATH}:/srv/media:ro
      - /opt/media/filebrowser/config/settings.json:/config/settings.json
      - /opt/media/filebrowser/database/filebrowser.db:/database/filebrowser.db
    user: "1000:1000"


  # ── Auto-updater ──────────────────────────────────────────────────────────
  watchtower:
    image: containrrr/watchtower:latest
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_SCHEDULE=0 0 4 * * *   # daily at 4am

  # ── Tidal Connect ─────────────────────────────────────────────────────────
  # Uncomment when ready. Appears as a UPnP renderer on your network.
  # tidal-connect:
  #   image: ghcr.io/tidal-connect/tidal-connect:latest
  #   container_name: tidal-connect
  #   network_mode: host
  #   restart: unless-stopped
  #   environment:
  #     - TIDAL_CONNECT_DEVICE_NAME=Pi-HiFi
  #     - TIDAL_CONNECT_DEVICE_TYPE=1   # 1=speaker, 3=AVR

volumes:
  netdata-config:
  netdata-lib:
  netdata-cache:
"""

HOMER_CONFIG = f"""\
title: "Pi Dashboard"
subtitle: "Home Media Server"
logo: "logo.png"

header: true
footer: false

services:
  - name: "Media"
    icon: "fas fa-photo-video"
    items:
      - name: "Jellyfin"
        logo: "https://jellyfin.org/images/favicon.ico"
        subtitle: "Media server"
        url: "http://{PI_HOST}:8096"

  - name: "Management"
    icon: "fas fa-cogs"
    items:
      - name: "Portainer"
        logo: "https://www.portainer.io/hubfs/portainer-logo-black.svg"
        subtitle: "Docker management"
        url: "http://{PI_HOST}:9000"
      - name: "Netdata"
        logo: "https://www.netdata.cloud/img/netdata.svg"
        subtitle: "System monitoring"
        url: "http://{PI_HOST}:19999"
      - name: "FileBrowser"
        logo: "https://filebrowser.org/img/logo.svg"
        subtitle: "File manager"
        url: "http://{PI_HOST}:8234"
"""

for path in [
    "/opt/media/jellyfin/config",
    "/opt/media/jellyfin/cache",
    "/opt/media/portainer/data",
    "/opt/media/homer/assets",
    "/opt/media/filebrowser/config",
    "/opt/media/filebrowser/database",
    MEDIA_PATH,
]:
    files.directory(
        name=f"Create directory {path}",
        path=path,
        present=True,
    )

files.put(
    name="Write FileBrowser settings.json",
    src=io.StringIO(
        '{"port": 80, "baseURL": "", "address": "", "log": "stdout", "database": "/database/filebrowser.db", "root": "/srv"}'
    ),
    dest="/opt/media/filebrowser/config/settings.json",
    user="1000",
    group="1000",
    mode="644",
)

files.put(
    name="Write docker-compose.yml",
    src=io.StringIO(COMPOSE),
    dest="/opt/media/docker-compose.yml",
    user="root",
    group="root",
    mode="644",
)

files.put(
    name="Write Homer config.yml",
    src=io.StringIO(HOMER_CONFIG),
    dest="/opt/media/homer/assets/config.yml",
    user="1000",
    group="1000",
    mode="644",
)

server.shell(
    name="Configure FileBrowser admin credentials",
    commands=[
        "rm -f /opt/media/filebrowser/database/filebrowser.db",
        "chown 1000:1000 /opt/media/filebrowser/database /opt/media/filebrowser/config",
        "docker run --rm "
        "-v /opt/media/filebrowser/database:/database "
        "-v /opt/media/filebrowser/config/settings.json:/config/settings.json "
        "filebrowser/filebrowser config init",
        f"docker run --rm "
        f"-v /opt/media/filebrowser/database:/database "
        f"-v /opt/media/filebrowser/config/settings.json:/config/settings.json "
        f"filebrowser/filebrowser users add admin '{FB_PASSWORD}' --perm.admin",
        "chown 1000:1000 /opt/media/filebrowser/database/filebrowser.db",
    ],
)

server.shell(
    name="Start media stack",
    commands=["docker compose -f /opt/media/docker-compose.yml up -d --remove-orphans"],
)
