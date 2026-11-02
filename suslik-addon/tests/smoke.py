"""Actual-image Docker simulation. No real HAOS, credentials or recognition data."""
import json
from pathlib import Path
import subprocess
import tempfile
import time
import uuid


def docker(*args, **kwargs):
    return subprocess.run(["docker", *args], check=True, text=True,
                          capture_output=True, **kwargs).stdout.strip()


def wait_http(name):
    probe = ("import urllib.request; "
             "r=urllib.request.urlopen('http://127.0.0.1:8199/health',timeout=5); "
             "assert r.status == 200")
    for _ in range(90):
        result = subprocess.run(["docker", "exec", name, "python", "-c", probe],
                                capture_output=True)
        if result.returncode == 0:
            return
        if docker("inspect", "-f", "{{.State.Running}}", name) != "true":
            break
        time.sleep(2)
    raise AssertionError("Application did not become healthy within 180 seconds")


name = "suslik-test-" + uuid.uuid4().hex[:10]
with tempfile.TemporaryDirectory() as tmp:
    data = Path(tmp)
    (data / "options.json").write_text(json.dumps({"frigate_url": "http://127.0.0.1:1"}))
    try:
        docker("run", "-d", "--name", name, "--mount",
               f"type=bind,src={data},dst=/data", "suslik-addon:test")
        wait_http(name)
        docker("exec", name, "python", "-c",
               "from pathlib import Path; Path('/data/upgrade-marker').write_text('keep')")
        docker("stop", "-t", "120", name)
        assert docker("inspect", "-f", "{{.State.ExitCode}}", name) == "0"
        docker("rm", name)
        docker("run", "-d", "--name", name, "--mount",
               f"type=bind,src={data},dst=/data", "suslik-addon:test")
        wait_http(name)
        assert (data / "upgrade-marker").read_text() == "keep"
        store = json.loads((data / "config/config.json").read_text())
        assert store["frigate_url"] == "http://127.0.0.1:1"
        assert store["backend"] == "cpu"
        docker("stop", "-t", "120", name)
        assert docker("inspect", "-f", "{{.State.ExitCode}}", name) == "0"
    finally:
        subprocess.run(["docker", "logs", name], check=False)
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True)
print("Docker startup, unavailable dependency, recreation, persistence and shutdown passed")
