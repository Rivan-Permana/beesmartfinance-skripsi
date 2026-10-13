"""Create private deployment configuration on the VPS without printing secrets."""

import argparse
import ipaddress
import os
from pathlib import Path
import re
import secrets

parser = argparse.ArgumentParser()
parser.add_argument("api_host", help="DNS hostname pointing to the VPS, without https://")
args = parser.parse_args()
host = args.api_host.lower()
if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host) or "." not in host:
    parser.error("Use a DNS hostname without a scheme, path, or port.")
try:
    ipaddress.ip_address(host)
except ValueError:
    pass
else:
    parser.error("Use a DNS hostname for the HTTPS certificate.")

destination = Path(__file__).resolve().parent.parent / ".env.vps"
content = (
    f"API_HOST={host}\n"
    f"POSTGRES_PASSWORD={secrets.token_urlsafe(48)}\n"
    f"DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n"
)
try:
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    parser.error(".env.vps already exists; existing database and Django secrets were preserved.")
with os.fdopen(descriptor, "w") as file:
    file.write(content)
print(f"Created private configuration: {destination}")
