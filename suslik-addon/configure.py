"""Supervisor adapter; deliberately independent of inference dependencies."""
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    pass


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ConfigurationError(f"Cannot read valid JSON from {path.name}") from None
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path.name} must contain a JSON object")
    return value


def validate(options):
    if set(options) - {"frigate_url", "poll_interval", "cpu_threads"}:
        raise ConfigurationError("Unknown add-on option; check the documentation")
    result = {"backend": "cpu"}
    url = options.get("frigate_url", "")
    if not isinstance(url, str):
        raise ConfigurationError("frigate_url must be a string")
    if url:
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme in {"http", "https"} and parsed.hostname
                     and not parsed.username and not parsed.password
                     and not parsed.query and not parsed.fragment
                     and not any(c.isspace() or ord(c) < 32 for c in url))
            parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ConfigurationError("frigate_url must be HTTP(S) without credentials, query or fragment")
        result["frigate_url"] = url.rstrip("/")
    for key, low, high in (("poll_interval", 5, 300), ("cpu_threads", 0, 64)):
        if key in options:
            value = options[key]
            if type(value) is not int or not low <= value <= high:
                raise ConfigurationError(f"{key} must be an integer between {low} and {high}")
            result[key] = value
    return result


def configure(data=Path("/data")):
    updates = validate(read_object(data / "options.json"))
    directory = data / "config"
    path = directory / "config.json"
    store = read_object(path) if path.exists() else {}
    store.update(updates)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            json.dump(store, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        configure()
    except (ConfigurationError, OSError) as error:
        # Never print supplied values, JSON parser excerpts, or OS exception paths.
        message = str(error) if isinstance(error, ConfigurationError) else "Cannot write persistent configuration; check storage permissions and free space"
        print(f"[suslik add-on] {message}", file=sys.stderr)
        sys.exit(1)
    print("[suslik add-on] Configuration validated; starting CPU service", flush=True)
