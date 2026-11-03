"""Interactive, private Doorbell v1 discovery using the bundled go2rtc instance."""

import argparse
import copy
import getpass
import io
import ipaddress
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


def discover(email, password, api_id, api_key):
    """Ask local go2rtc to authenticate; never print account or stream secrets."""
    body = urlencode(
        {"email": email, "password": password, "api_id": api_id, "api_key": api_key}
    ).encode()
    request = Request("http://127.0.0.1:1984/api/wyze", data=body)
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def select_doorbell(result, address):
    """Select only the requested Doorbell v1, keeping discovery keys private."""
    address = str(ipaddress.IPv4Address(address))
    candidates = []
    for source in result.get("sources", []):
        parts = urlsplit(source.get("url", ""))
        query = parse_qs(parts.query)
        if parts.scheme == "wyze" and query.get("model") == ["WYZEDB3"]:
            if not all(query.get(key, [""])[0] for key in ("uid", "enr", "mac")):
                raise ValueError(
                    "Doorbell discovery did not supply the connection keys"
                )
            if query.get("dtls") != ["true"]:
                raise ValueError("Doorbell discovery did not report DTLS support")
            candidates.append(parts)
    matching = [parts for parts in candidates if parts.hostname == address]
    if len(matching) == 1:
        selected = matching[0]
    elif len(candidates) == 1:
        selected = candidates[0]
    else:
        raise ValueError(
            "No unique Doorbell v1 found; verify its account and IP address"
        )
    # The cloud can have a stale DHCP address. The user supplies the current IP.
    return urlunsplit(("wyze", address, selected.path, selected.query, ""))


def add_camera(config, name, source):
    """Add a dedicated stream and detect-only camera without replacing others."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,49}", name):
        raise ValueError(
            "Use a camera name starting with a letter, then lowercase letters, digits or underscores"
        )
    config = copy.deepcopy(config)
    for key in ("go2rtc", "cameras"):
        if config.get(key) is None:
            config[key] = {}
        if not isinstance(config[key], dict):
            raise TypeError("Existing camera/stream configuration is not a mapping")
    streams = config["go2rtc"].setdefault("streams", {})
    if not isinstance(streams, dict):
        raise TypeError("Existing stream configuration is not a mapping")
    if name in config["cameras"] or name in streams:
        raise ValueError("That camera/stream name already exists; choose another name")
    streams[name] = [source]
    config["cameras"][name] = {
        "ffmpeg": {
            "inputs": [
                {
                    "path": f"rtsp://127.0.0.1:8554/{name}",
                    "input_args": "preset-rtsp-restream",
                    "roles": ["detect"],
                }
            ],
        },
        "detect": {"enabled": True, "fps": 5},
        "objects": {"track": ["person"]},
        "record": {"enabled": False},
        "audio": {"enabled": False},
    }
    return config


def save_config(path, config, original):
    """Atomically save with a private rollback copy and detect concurrent edits."""
    from ruamel.yaml import YAML

    yaml = YAML()
    stream = io.StringIO()
    yaml.dump(config, stream)
    rendered = stream.getvalue()
    # Validate using the actual Frigate schema before touching the user's YAML.
    from frigate.config import FrigateConfig

    try:
        FrigateConfig.model_validate(yaml.load(rendered))
    except ValueError:
        raise ValueError(
            "Frigate rejected the proposed configuration; original YAML is unchanged"
        ) from None
    if path.read_bytes() != original:
        raise ValueError("Configuration changed during discovery; run setup again")
    backup_fd, backup_path = tempfile.mkstemp(
        prefix=path.name + ".before-wyze-", dir=path.parent
    )
    with os.fdopen(backup_fd, "wb") as stream:
        stream.write(original)
        stream.flush()
        os.fsync(stream.fileno())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        # Check again after staging so an edit cannot be silently overwritten.
        if path.read_bytes() != original:
            raise ValueError("Configuration changed during setup; run setup again")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return Path(backup_path)


def main():
    from ruamel.yaml import YAML

    parser = argparse.ArgumentParser(
        description="Add a Wyze Doorbell v1 without a separate bridge"
    )
    parser.add_argument("--ip", help="Current doorbell IPv4 address")
    args = parser.parse_args()
    paths = [Path("/config/config.yml"), Path("/config/config.yaml")]
    path = next((item for item in paths if item.exists()), None)
    if path is None:
        raise ValueError("Start Frigate once to create its configuration")
    original = path.read_bytes()
    yaml = YAML()
    config = yaml.load(original.decode())
    address = args.ip or input("Doorbell IP address: ").strip()
    address = str(ipaddress.IPv4Address(address))
    name = input("New camera name [wyze_doorbell]: ").strip() or "wyze_doorbell"
    print("Enter Wyze credentials locally. Password and API fields are hidden.")
    email = input("Wyze email: ").strip()
    password = getpass.getpass("Wyze password: ")
    api_id = getpass.getpass("Wyze API ID: ")
    api_key = getpass.getpass("Wyze API key: ")
    result = discover(email, password, api_id, api_key)
    source = select_doorbell(result, address)
    updated = add_camera(config, name, source)
    print(
        f"Found Doorbell v1. Add {name} at {address} for person detection, with recording off?"
    )
    if input("Save configuration? [y/N]: ").strip().lower() != "y":
        print("Frigate configuration unchanged")
        return
    backup = save_config(path, updated, original)
    print(f"Saved. Private rollback copy: {backup.name}")
    print("Restart Frigate + Suslik Test from Home Assistant, then check live video.")
    print(
        "Wyze account credentials are not copied into Frigate YAML; the private stream contains device keys."
    )


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("Setup cancelled; Frigate configuration was not saved")
    except (ValueError, TypeError) as error:
        print(f"Setup could not finish: {error}")
        raise SystemExit(1) from None
    except Exception:  # noqa: BLE001 -- CLI boundary must suppress secret HTTP diagnostics.
        # Authentication/HTTP errors can contain account or camera keys.
        print(
            "Setup failed. Check the Wyze credentials/API key, account verification and local go2rtc status. No secret diagnostics were printed."
        )
        raise SystemExit(1) from None
