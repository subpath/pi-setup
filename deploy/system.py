import os
from pyinfra.operations import apt, server

TIMEZONE = os.environ.get("TIMEZONE", "Europe/Berlin")

apt.update(name="Update apt cache")

apt.upgrade(
    name="Upgrade packages",
    auto_remove=True,
)

apt.packages(
    name="Install base packages",
    packages=[
        "curl",
        "git",
        "vim",
        "htop",
        "ca-certificates",
        "tmux",
        "exfatprogs",
        "btop",
        "iperf3",
        "smartmontools",
    ],
)

server.shell(
    name="Set timezone",
    commands=[f"timedatectl set-timezone {TIMEZONE}"],
)
