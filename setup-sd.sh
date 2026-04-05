#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
set -a && source "$SCRIPT_DIR/.env" && set +a

BOOT="${1:-/Volumes/bootfs}"

[[ -d "$BOOT" ]] || { echo "Boot partition not found: $BOOT"; exit 1; }

# ── User ──────────────────────────────────────────────────────────────────────
HASH=$($(brew --prefix openssl)/bin/openssl passwd -6 "$PI_PASSWORD")
echo "${PI_USER}:${HASH}" > "$BOOT/userconf.txt"

# ── SSH ───────────────────────────────────────────────────────────────────────
touch "$BOOT/ssh"

# ── WiFi ──────────────────────────────────────────────────────────────────────
cat > "$BOOT/wpa_supplicant.conf" << EOF
country=${WIFI_COUNTRY}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="${WIFI_SSID}"
    psk="${WIFI_PASSWORD}"
}
EOF

sync
echo "Done. Eject the SD card and boot your Pi."
