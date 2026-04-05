from pyinfra import local

local.include("deploy/system.py")
local.include("deploy/security.py")
local.include("deploy/reliability.py")
local.include("deploy/docker.py")
local.include("deploy/media.py")
local.include("deploy/backup.py")
