import io
from pyinfra.operations import apt, files, server, systemd

apt.packages(
    name="Install security packages",
    packages=["fail2ban", "ufw", "unattended-upgrades"],
)

files.put(
    name="Configure fail2ban SSH jail",
    src=io.StringIO("[sshd]\nenabled = true\nport = ssh\nmaxretry = 5\nbantime = 1h\n"),
    dest="/etc/fail2ban/jail.local",
    mode="644",
)

systemd.service(
    name="Enable fail2ban",
    service="fail2ban",
    enabled=True,
    running=True,
)

# Docker bypasses UFW for container port mappings (known upstream issue).
# UFW here protects the host — SSH and host-mode services (Jellyfin DLNA).
server.shell(
    name="Configure UFW",
    commands=[
        "ufw default deny incoming",
        "ufw default allow outgoing",
        "ufw allow ssh",
        "ufw allow 8096/tcp",  # Jellyfin
        "ufw allow 9000/tcp",  # Portainer
        "ufw allow 19999/tcp",  # Netdata
        "ufw allow 3000/tcp",  # Homer
        "ufw --force enable",
    ],
)

systemd.service(
    name="Enable unattended-upgrades",
    service="unattended-upgrades",
    enabled=True,
    running=True,
)
