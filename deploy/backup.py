import io
import os
from pyinfra.operations import apt, files, server

BACKUP_PATH = os.environ.get("BACKUP_PATH", "/mnt/backup")
RESTIC_PASSWORD = os.environ.get("RESTIC_PASSWORD", "")

apt.packages(
    name="Install restic",
    packages=["restic"],
)

files.directory(
    name="Create restic config dir",
    path="/etc/restic",
    present=True,
    mode="700",
)

files.directory(
    name="Create backup destination",
    path=f"{BACKUP_PATH}/pi-media",
    present=True,
)

if RESTIC_PASSWORD:
    files.put(
        name="Write restic password file",
        src=io.StringIO(RESTIC_PASSWORD + "\n"),
        dest="/etc/restic/password",
        mode="600",
    )

    server.shell(
        name="Initialize restic repo",
        commands=[
            f"restic -r {BACKUP_PATH}/pi-media --password-file /etc/restic/password cat config >/dev/null 2>&1 "
            f"|| restic -r {BACKUP_PATH}/pi-media --password-file /etc/restic/password init",
        ],
    )

files.put(
    name="Write backup script",
    src=io.StringIO(f"""\
#!/bin/bash
set -euo pipefail
REPO={BACKUP_PATH}/pi-media
restic -r "$REPO" --password-file /etc/restic/password backup /opt/media
restic -r "$REPO" --password-file /etc/restic/password forget \\
    --keep-daily 7 --keep-weekly 4 --prune
"""),
    dest="/usr/local/bin/pi-backup",
    mode="755",
)

files.put(
    name="Schedule daily backup",
    src=io.StringIO(
        "0 3 * * * root /usr/local/bin/pi-backup >> /var/log/pi-backup.log 2>&1\n"
    ),
    dest="/etc/cron.d/pi-backup",
    mode="644",
)
