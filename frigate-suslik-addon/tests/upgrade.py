"""Exercise a real 0.18.2 database/config upgrade in isolated private storage."""

import json
import subprocess
import time
import uuid

from smoke import IMAGE, docker, start, stop, wait_ready

PREVIOUS_IMAGE = (
    "ghcr.io/blakeblackshear/frigate:0.18.2@sha256:"
    "fd60f99ffd4eb6c42360ed4e14953e270586f239309ab3983e55b2e97ffac09a"
)


def main():
    name = "frigate-upgrade-test-" + uuid.uuid4().hex[:10]
    volume = name + "-data"
    docker("volume", "create", volume)
    try:
        config = {
            "mqtt": {"enabled": False},
            "cameras": {},
            "record": {"enabled": False},
            "face_recognition": {"enabled": False},
        }
        docker(
            "run",
            "--rm",
            "-i",
            "--network",
            "none",
            "--mount",
            f"type=volume,src={volume},dst=/data",
            "--entrypoint",
            "python3",
            PREVIOUS_IMAGE,
            "-c",
            "import json,sys,yaml; from pathlib import Path; "
            "Path('/data/config').mkdir(); Path('/data/media').mkdir(); "
            "Path('/data/options.json').write_text('{}'); "
            "Path('/data/config/config.yml').write_text(yaml.safe_dump(json.load(sys.stdin)))",
            input=json.dumps(config),
        )
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "none",
            "--mount",
            f"type=volume,src={volume},dst=/data",
            "--entrypoint",
            "sh",
            PREVIOUS_IMAGE,
            "-c",
            "mkdir -p /media && "
            "ln -s /data/config /config && ln -s /data/media /media/frigate && exec /init",
        )
        for _ in range(90):
            ready = subprocess.run(
                [
                    "docker",
                    "exec",
                    name,
                    "python3",
                    "-c",
                    (
                        "import urllib.request; assert '0.18.2' in "
                        "urllib.request.urlopen('http://127.0.0.1:5000/api/version',timeout=3).read().decode()"
                    ),
                ],
                check=False,
                capture_output=True,
                timeout=10,
            )
            if ready.returncode == 0:
                break
            if docker("inspect", "-f", "{{.State.Running}}", name) != "true":
                raise AssertionError("Previous Frigate runtime exited during startup")
            time.sleep(2)
        else:
            raise AssertionError("Previous Frigate runtime did not start")
        docker("stop", "-t", "120", name)
        docker("rm", name)
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
            "import sqlite3,yaml; from pathlib import Path; "
            "db=sqlite3.connect('/data/config/frigate.db'); "
            "db.execute('CREATE TABLE suslik_upgrade_marker (value TEXT)'); "
            "db.execute(\"INSERT INTO suslik_upgrade_marker VALUES ('preserved')\"); "
            "db.commit(); db.close(); "
            "p=Path('/data/config/config.yml'); c=yaml.safe_load(p.read_text()); "
            "c['face_recognition']={'enabled':False,'suslik':{'enabled':True,'min_samples':4}}; "
            "p.write_text(yaml.safe_dump(c)); Path('/data/media/keep').write_text('preserved')",
        )
        start(name, volume)
        wait_ready(name)
        docker(
            "exec",
            name,
            "python3",
            "-c",
            "import sqlite3,yaml; from pathlib import Path; "
            "db=sqlite3.connect('/data/config/frigate.db'); "
            "assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; "
            "assert db.execute('SELECT value FROM suslik_upgrade_marker').fetchone()[0]=='preserved'; "
            "assert yaml.safe_load(Path('/data/config/config.yml').read_text())"
            "['face_recognition']['suslik']['min_samples']==4; "
            "assert Path('/data/media/keep').read_text()=='preserved'",
        )
        stop(name)
        print(
            "PASS: 0.18.2 database upgrades with integrity, Suslik settings and private media preserved"
        )
    except Exception:
        subprocess.run(["docker", "logs", "--tail", "80", name], check=False)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True)
        subprocess.run(
            ["docker", "volume", "rm", volume], check=False, capture_output=True
        )


if __name__ == "__main__":
    main()
