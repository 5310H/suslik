# Home Assistant OS architecture

## Repository investigation

Suslik is a Python companion to Frigate: polling or MQTT triggers recorded-clip
analysis, AdaFace/buffalo_l face recognition, cross-camera scenarios, learning,
and optional notifications/write-back. `verifyd.py --config /app/verifyd.yaml`
starts a threaded HTTP server on 8199 and manages analysis subprocesses
(`worker_dienst.py`, CPU/OpenVINO/CUDA/MIGraphX engines). `core/`, `routes/`, and
`webui/` contain shared logic and the UI. See architecture.md and configuration.md.

The existing CPU Dockerfile uses Python 3.13, ffmpeg, OpenCV, NumPy, InsightFace,
scikit-learn, PyYAML, paho-mqtt and pinned OpenVINO runtimes. Source builds refer
to absent `models/`, `modelle/`, `docker/buffalo_l/`, and person-learning staging
directories. The documented build script is also absent. No test suite or release
workflow exists in this checkout; VERSION is 0.1.1.048. Releases are distributed
as CPU, Intel, Intel legacy, CUDA and ROCm images on upstream GHCR.

On 2026-11-02 the registry manifest for
`ghcr.io/bennobaer-dev/suslik:0.1.1.048-cpu` contained linux/amd64 only (plus an
attestation). Its immutable index digest is
`sha256:0a73af4efad3a595d7104881015d7eca51f4d318d820c40f018c9f093c0df636`.
ARM is therefore unsupported initially; substituting an inference runtime would
need accuracy and performance acceptance, not merely a successful pip install.

## Packaging decision

Build a thin add-on from that immutable CPU image. This reuses the existing
application, models and pinned runtime without duplicating its incomplete source
build. No application source is modified. The upstream release, rather than local
application edits, is what the add-on runs. Updating it requires changing the
digest, release reference and add-on version together. No new pip/apt dependencies
are installed. An official Alpine HA base would be incompatible with these glibc
ML wheels; Supervisor's default init is used with the existing Debian image.

The entrypoint reads /data/options.json, validates types/ranges and URLs, and
atomically merges supported options into the existing /data/config/config.json.
Other UI settings and secrets survive. Empty frigate_url leaves wizard/UI
configuration intact. Provided options are authoritative on each restart; CPU
backend is enforced because no devices/drivers are passed through. The existing
/app/verifyd.yaml remains the standalone-format default configuration.

All runtime state remains in Supervisor's private /data: config, refquelle,
faces, learn, state, personlern, live, events, clips, logs and archives. Backups
include this directory and options. Stop before backup for a consistent snapshot.
The wrapper never deletes data or logs option values. Application diagnostics
remain upstream behavior; treat downloaded diagnostics as sensitive.

## Network, security and integration

Outbound connectivity is required to Frigate's configured HTTP(S) API and, for
live cameras, configured RTSP sources. Optional MQTT, Pushover, Telegram/HA and
vision endpoints need their own outbound access. Existing source supports
frigate_user/password and TLS verification in its config store, despite older
installation documentation saying authenticated Frigate is unsupported.
Configure credentials in Suslik's UI; no secrets are baked into this wrapper.

No host networking, devices, capabilities, Docker socket, host directory mounts,
Supervisor API or automatic HA token is needed. Protection mode stays enabled.
The upstream image runs as root inside the isolated container, as its model
search path uses /root/.insightface. No additional privileges are granted.

Ingress is disabled: generated HTML and JavaScript contain root-relative links,
fetches and redirects, with no established proxy-prefix support. Rewriting just
HTML would not reliably cover uploads, streaming and generated URLs. Port 8199
is disabled by default. Enable only on a trusted LAN, or use an authenticated
reverse proxy serving Suslik at its own URL root. The UI has no add-on-provided
authentication. Do not publish it directly to the internet.

Existing MQTT and configured HA/Telegram calls remain available; there is no new
entity integration, discovery or invented webhook. /health supplies the optional
Supervisor HTTP liveness watchdog. It returns HTTP 200 even when its JSON `ok`
flag is false; inspect that flag and logs for application/dependency health.
exec preserves signal delivery; verifyd registers SIGTERM
and SIGINT handlers and worker cleanup. Supervisor allows 120 seconds to stop.

## Validation boundary

Unit tests exercise real wrapper parsing, atomic merge, restart/upgrade state
preservation, invalid credentials-in-URL rejection, and fail-closed behavior.
CI checks metadata with the HA builder/linter ecosystem and builds amd64, then
runs the actual image for first startup, restart, health and graceful termination
against an unreachable Frigate endpoint. These are Docker simulations, not HAOS
certification. Real HAOS store registration, wizard completion, Frigate login,
recognition accuracy, resource sizing and backup/restore remain release gates.
Local Docker availability and executed test results are recorded at delivery.

References: https://contributors.home-assistant.io/apps/reference/configuration/
and https://contributors.home-assistant.io/apps/guides/dockerfile/.
