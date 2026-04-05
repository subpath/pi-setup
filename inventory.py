import os

PI_HOST = os.environ.get("PI_HOST", "raspberrypi.local")
PI_USER = os.environ.get("PI_USER", "pi")
PI_PASSWORD = os.environ.get("PI_PASSWORD", "")

hosts = [(PI_HOST, {"ssh_user": PI_USER, "ssh_password": PI_PASSWORD})]
