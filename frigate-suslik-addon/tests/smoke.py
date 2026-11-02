"""Docker simulation of private Supervisor data, Ingress headers and cold restore.

No HAOS, real camera, Coral access or face inference is exercised here.
"""

import json
import subprocess
import time
import uuid

IMAGE = "frigate-suslik-addon:test"


def docker(*args, **kwargs):
    return subprocess.run(
        ["docker", *args],
        check=True,
        text=True,
        capture_output=True,
        timeout=150,
        **kwargs,
    ).stdout.strip()


def start(name, volume):
    docker(
        "run",
        "-d",
        "--name",
        name,
        "--network",
        "none",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=volume,src={volume},dst=/data",
        IMAGE,
    )


def wait_ready(name):
    probe = (
        "import json,urllib.request; from pathlib import Path; "
        "u='http://127.0.0.1:5000'; "
        "v=urllib.request.urlopen(u+'/api/version',timeout=5).read().decode(); "
        "assert '0.18.2-suslik.1' in v; "
        "r=json.load(urllib.request.urlopen(u+'/api/events/suslik/visits',timeout=5)); "
        "assert r['visits']==[]; "
        "req=urllib.request.Request(u+'/visits',headers={'X-Ingress-Path':'/api/hassio_ingress/test-token'}); "
        "html=urllib.request.urlopen(req,timeout=5).read().decode(); "
        "assert '/api/hassio_ingress/test-token/' in html; "
        "assert Path('/config').resolve()==Path('/data/config'); "
        "assert Path('/media/frigate').resolve()==Path('/data/media'); "
        "assert list(Path('/opt/frigate/web/assets').glob('SuslikVisits-*.js'))"
    )
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", name, "python3", "-c", probe],
            capture_output=True,
            timeout=25,
        )
        if result.returncode == 0:
            return
        if docker("inspect", "-f", "{{.State.Running}}", name) != "true":
            break
        time.sleep(2)
    raise AssertionError("HAOS test image did not initialize its UI/API/private data")


def stop(name):
    docker("stop", "-t", "120", name)
    state = json.loads(docker("inspect", name))[0]["State"]
    assert state["ExitCode"] in (0, 143) and not state["OOMKilled"]
    logs = subprocess.run(
        ["docker", "logs", name], check=True, text=True, capture_output=True
    )
    assert "Service Frigate exited with code 0" in logs.stdout + logs.stderr
    docker("rm", name)


def main():
    name = "frigate-addon-test-" + uuid.uuid4().hex[:10]
    volume, restored = name + "-data", name + "-restored"
    for item in (volume, restored):
        docker("volume", "create", item)
    try:
        docker(
            "run",
            "--rm",
            "--network",
            "none",
            "--mount",
            f"type=volume,src={volume},dst=/data",
            "--entrypoint",
            "python3",
            IMAGE,
            "-c",
            "from pathlib import Path; Path('/data/options.json').write_text('{}')",
        )
        start(name, volume)
        wait_ready(name)
        docker(
            "exec",
            name,
            "python3",
            "-c",
            "from pathlib import Path; Path('/data/media/keep').write_text('preserve')",
        )
        stop(name)
        print(
            "PASS: private data initialization, native API/UI assets, Ingress prefix and graceful shutdown",
            flush=True,
        )

        start(name, volume)
        wait_ready(name)
        docker(
            "exec",
            name,
            "python3",
            "-c",
            "from pathlib import Path; assert Path('/data/media/keep').read_text()=='preserve'; "
            "assert Path('/data/config/frigate.db').exists()",
        )
        stop(name)
        print("PASS: settings/database/media survive container recreation", flush=True)

        archive = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--mount",
                f"type=volume,src={volume},dst=/data,readonly",
                "--entrypoint",
                "tar",
                IMAGE,
                "-C",
                "/data",
                "-cf",
                "-",
                ".",
            ],
            check=True,
            capture_output=True,
            timeout=60,
        ).stdout
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--network",
                "none",
                "--mount",
                f"type=volume,src={restored},dst=/data",
                "--entrypoint",
                "tar",
                IMAGE,
                "-C",
                "/data",
                "-xf",
                "-",
            ],
            input=archive,
            check=True,
            capture_output=True,
            timeout=60,
        )
        start(name, restored)
        wait_ready(name)
        docker(
            "exec",
            name,
            "python3",
            "-c",
            "from pathlib import Path; assert Path('/data/media/keep').read_text()=='preserve'; "
            "assert Path('/data/config/frigate.db').exists()",
        )
        stop(name)
        print(
            "PASS: cold filesystem restore starts with preserved database/media",
            flush=True,
        )
    except Exception:
        subprocess.run(["docker", "logs", "--tail", "100", name], check=False)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True)
        for item in (volume, restored):
            subprocess.run(
                ["docker", "volume", "rm", item], check=False, capture_output=True
            )


if __name__ == "__main__":
    main()
