import os
from pyinfra.operations import server, systemd

PI_USER = os.environ.get("PI_USER", "pi")

server.shell(
    name="Install Docker and add user to group",
    commands=[
        "curl -fsSL https://get.docker.com | sh",
        f"usermod -aG docker {PI_USER}",
    ],
)

server.shell(
    name="Install lazydocker",
    commands=[
        "curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash"
    ],
)

systemd.service(
    name="Enable and start Docker",
    service="docker",
    enabled=True,
    running=True,
)
