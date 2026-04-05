import io

from pyinfra.operations import apt, files, server

files.download(
    name="Add azlux apt key",
    src="https://azlux.fr/repo.gpg",
    dest="/usr/share/keyrings/azlux-archive-keyring.gpg",
)

files.put(
    name="Add azlux apt repo",
    src=io.StringIO(
        "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] "
        "http://packages.azlux.fr/debian/ bookworm main\n"
    ),
    dest="/etc/apt/sources.list.d/azlux.list",
    mode="644",
)

apt.update(name="Update apt after adding azlux repo")
apt.packages(name="Install log2ram", packages=["log2ram"])

files.replace(
    name="Set log2ram size to 128M",
    path="/etc/log2ram.conf",
    match=r"^SIZE=.*",
    replace="SIZE=128M",
)

files.line(
    name="Enable watchdog in boot config",
    path="/boot/firmware/config.txt",
    line="dtparam=watchdog=on",
    present=True,
)

files.replace(
    name="Configure systemd hardware watchdog",
    path="/etc/systemd/system.conf",
    match=r"^#?RuntimeWatchdogSec=.*",
    replace="RuntimeWatchdogSec=15",
)

server.shell(
    name="Reload systemd after watchdog config",
    commands=["systemctl daemon-reexec"],
)
