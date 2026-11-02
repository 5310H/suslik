"""Bootstrap only this test add-on's private storage, then enter Frigate's s6 init."""

import json
import os
from pathlib import Path
import sys
import tempfile

import yaml


def bootstrap(data=Path("/data")):
    try:
        options = json.loads((data / "options.json").read_text())
    except (ValueError, OSError):
        raise ValueError("Cannot read Supervisor options.json") from None
    if not isinstance(options, dict) or set(options) - {"plus_api_key"}:
        raise ValueError(
            "Unexpected add-on options; configure Frigate through its own UI"
        )
    if "plus_api_key" in options and not isinstance(options["plus_api_key"], str):
        raise ValueError("plus_api_key must be a string")
    config = data / "config"
    media = data / "media"
    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    media.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (config / "config.yml").exists() or (config / "config.yaml").exists():
        return
    # Start without cameras, model downloads or claiming the Coral. The user
    # enables their test camera and USB detector in Frigate's configuration UI.
    initial = {
        "mqtt": {"enabled": False},
        "cameras": {},
        "record": {"enabled": False},
        "face_recognition": {"enabled": False, "suslik": {"enabled": True}},
    }
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=config, delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            yaml.safe_dump(initial, stream, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, config / "config.yml")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        bootstrap()
    except (ValueError, OSError):
        print(
            "[Frigate + Suslik] Cannot initialize private data or options; check configuration, permissions and free space",
            file=sys.stderr,
        )
        sys.exit(1)
    # No Supervisor API capability is needed. Avoid upstream go2rtc attempting
    # optional API-based WebRTC address discovery in this ingress-only test app.
    os.environ.pop("SUPERVISOR_TOKEN", None)
    os.environ.pop("HASSIO_TOKEN", None)
    print(
        "[Frigate + Suslik] Starting experimental native build with private config/media",
        flush=True,
    )
    os.execv("/init", ["/init"])
