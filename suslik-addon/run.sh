#!/bin/sh
set -eu
umask 077
python /app/ha_configure.py
cd /app
exec python -u verifyd.py --config /app/verifyd.yaml
