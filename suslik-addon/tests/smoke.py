"""Actual-image Docker tests; these do not certify Supervisor/HAOS or recognition."""
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

IMAGE = "suslik-addon:test"


def docker(*args, **kwargs):
    return subprocess.run(["docker", *args], check=True, text=True,
                          capture_output=True, timeout=150, **kwargs).stdout.strip()


def volume_python(volume, code, data=None):
    return docker("run", "--rm", "-i", "--network", "none", "--mount",
                  f"type=volume,src={volume},dst=/data", "--entrypoint", "python",
                  IMAGE, "-c", code, input=json.dumps(data))


def write_options(volume, options):
    volume_python(volume, "import sys; from pathlib import Path; "
                  "Path('/data/options.json').write_text(sys.stdin.read())", options)


def start(name, volume, image=IMAGE):
    # Match Supervisor's default init, with no host mounts, published ports or network.
    docker("run", "-d", "--init", "--network", "none", "--name", name, "--mount",
           f"type=volume,src={volume},dst=/data", image)


def wait_http(name, check_health=True):
    probe = ("import json,urllib.request; "
             "r=urllib.request.urlopen('http://127.0.0.1:8199/health',timeout=5); "
             "h=json.load(r); assert isinstance(h['ok'],bool); "
             "r=urllib.request.urlopen('http://127.0.0.1:8199/',timeout=5); "
             "assert r.status == 200")
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        result = subprocess.run(["docker", "exec", name, "python", "-c", probe],
                                capture_output=True, timeout=20)
        if result.returncode == 0:
            if check_health:
                health = json.loads(docker("inspect", name))[0]["Config"]["Healthcheck"]["Test"]
                assert health[0] == "CMD"
                docker("exec", name, *health[1:])
            return
        if docker("inspect", "-f", "{{.State.Running}}", name) != "true":
            break
        time.sleep(2)
    raise AssertionError("Application HTTP interface did not start within 240 seconds")


def stop(name):
    docker("stop", "-t", "120", name)
    assert docker("inspect", "-f", "{{.State.ExitCode}}", name) == "0", "Forced or failed shutdown"
    docker("rm", name)


def check_state(volume):
    volume_python(volume, "import json; from pathlib import Path; "
                  "s=json.loads(Path('/data/config/config.json').read_text()); "
                  "assert s['backend']=='cpu'; assert s['poll_interval']==17; "
                  "assert s['frigate_url']=='http://127.0.0.1:1'; "
                  "assert s['frigate_password']=='test-only-password'; "
                  "assert Path('/data/learn/persistence-test').read_text()=='keep'")


def main():
    name = "suslik-test-" + uuid.uuid4().hex[:10]
    volume, restored = name + "-data", name + "-restored"
    for item in (volume, restored):
        docker("volume", "create", item)
    try:
        write_options(volume, {})
        start(name, volume)
        wait_http(name)
        stop(name)
        print("PASS: first startup without credentials, web UI, health check and graceful stop", flush=True)

        volume_python(volume, "import json; from pathlib import Path; "
                      "p=Path('/data/config/config.json'); s=json.loads(p.read_text()); "
                      "s['frigate_password']='test-only-password'; p.write_text(json.dumps(s)); "
                      "p=Path('/data/learn/persistence-test'); p.parent.mkdir(exist_ok=True); "
                      "p.write_text('keep')")
        write_options(volume, {"frigate_url": "http://127.0.0.1:1", "poll_interval": 17})
        start(name, volume)
        wait_http(name)
        stop(name)
        check_state(volume)
        print("PASS: unavailable Frigate does not prevent UI startup; recreation preserves settings and data", flush=True)

        write_options(volume, {"frigate_url": "http://user:test-only-password@host"})
        start(name, volume)
        assert docker("wait", name) == "1"
        raw = subprocess.run(["docker", "logs", name], capture_output=True, text=True, check=True)
        assert "without credentials" in raw.stderr
        assert "test-only-password" not in raw.stdout + raw.stderr
        docker("rm", name)
        check_state(volume)
        write_options(volume, {})
        print("PASS: invalid configuration fails closed without leaking secrets or replacing data", flush=True)

        # Cold filesystem backup/restore simulation, with no live writers.
        archive = subprocess.run(["docker", "run", "--rm", "--network", "none", "--mount",
                                  f"type=volume,src={volume},dst=/data,readonly", "--entrypoint",
                                  "tar", IMAGE, "-C", "/data", "-cf", "-", "."],
                                 check=True, capture_output=True, timeout=60).stdout
        subprocess.run(["docker", "run", "--rm", "-i", "--network", "none", "--mount",
                        f"type=volume,src={restored},dst=/data", "--entrypoint", "tar", IMAGE,
                        "-C", "/data", "-xf", "-"], input=archive,
                       check=True, capture_output=True, timeout=60)
        start(name, restored)
        wait_http(name)
        stop(name)
        check_state(restored)
        print("PASS: cold archive restore starts and preserves settings, credentials and learning data", flush=True)

        # Check the same persisted store with the unmodified standalone image.
        dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text()
        upstream = re.search(r"^FROM (\S+)$", dockerfile, re.MULTILINE).group(1)
        start(name, restored, upstream)
        wait_http(name, check_health=False)
        stop(name)
        check_state(restored)
        print("PASS: original standalone image starts with the add-on's saved configuration", flush=True)
    except Exception:
        subprocess.run(["docker", "logs", "--tail", "100", name], check=False)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True)
        for item in (volume, restored):
            subprocess.run(["docker", "volume", "rm", item], check=False, capture_output=True)


if __name__ == "__main__":
    main()
