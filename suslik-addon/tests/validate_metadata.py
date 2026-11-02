"""Cross-file invariants, in addition to the Home Assistant schema linter."""
import json
from pathlib import Path
import re
import yaml

root = Path(__file__).resolve().parents[2]
addon = root / "suslik-addon"
config = yaml.safe_load((addon / "config.yaml").read_text())
repo = json.loads((root / "repository.json").read_text())
workflow = yaml.safe_load((root / ".github/workflows/haos-addon.yml").read_text())
assert repo["url"] == "https://github.com/5310H/suslik"
assert config["arch"] == ["amd64"]
assert not (addon / "build.yaml").exists(), "Use Dockerfile defaults, not deprecated build.yaml"
assert config["ports"] == {"8199/tcp": None}
assert config["backup"] == "cold"
assert config["timeout"] >= 120
assert config.get("init", True) is True
assert "watchdog" not in config
assert not any(config.get(key) for key in (
    "host_network", "privileged", "devices", "docker_api", "hassio_api", "homeassistant_api", "map"))
dockerfile = (addon / "Dockerfile").read_text()
image = re.search(r"^FROM (\S+)$", dockerfile, re.MULTILINE).group(1)
assert re.fullmatch(r"ghcr.io/bennobaer-dev/suslik:0\.1\.1\.048-cpu@sha256:[a-f0-9]{64}", image)
assert config["version"].startswith((root / "VERSION").read_text().strip() + "-")
assert f'ARG BUILD_VERSION={config["version"]}' in dockerfile
assert 'io.hass.type="app"' in dockerfile
assert "HEALTHCHECK " in dockerfile
assert workflow["permissions"] == {"contents": "read"}
assert set(config["options"]) <= set(config["schema"])
print("Metadata, workflow YAML and cross-file invariants passed")
