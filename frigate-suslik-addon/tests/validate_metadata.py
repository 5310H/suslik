import json
from pathlib import Path
import re

import yaml

addon = Path(__file__).resolve().parents[1]
config = yaml.safe_load((addon / "config.yaml").read_text())
dockerfile = (addon / "Dockerfile").read_text()
assert config["arch"] == ["amd64"]
assert config["init"] is False
assert config["usb"] is True
assert config["host_network"] is True
assert config["environment"] == {"FRIGATE_RUN_AS_ROOT": "true"}
assert config["ingress"] is True and config["ingress_port"] == 5000
assert config["boot"] == "manual" and config["backup"] == "cold"
assert not any(
    config.get(key)
    for key in (
        "ports",
        "map",
        "privileged",
        "full_access",
        "docker_api",
        "hassio_api",
        "homeassistant_api",
    )
)
assert "watchdog" not in config and "webui" not in config
assert f"ARG BUILD_VERSION={config['version']}" in dockerfile
assert re.search(r"ARG SOURCE_COMMIT=[a-f0-9]{40}\b", dockerfile)
assert re.search(r"ADD --checksum=sha256:[a-f0-9]{64} ", dockerfile)
assert dockerfile.count("@sha256:") == 3
assert "ln -s /data/config /config" in dockerfile
assert "ln -s /data/media /media/frigate" in dockerfile
assert (
    json.loads((addon.parent / "repository.json").read_text())["url"]
    == "https://github.com/5310H/suslik"
)
print("Combined Frigate/Suslik HAOS metadata, host networking, storage isolation and source pins passed")
