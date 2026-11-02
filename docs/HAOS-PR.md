Title: Add experimental native Home Assistant OS add-on for Suslik CPU

Base: main
Head: feature/haos-addon

Adds Supervisor packaging for the existing Suslik 0.1.1.048 CPU release, using a
digest-pinned image because model assets needed for source builds are absent from
this checkout. Standalone code, images and configuration remain unchanged.

The amd64 add-on validates Supervisor options and atomically merges them into
Suslik's persistent config store. It includes private /data storage, cold backups,
exec-based shutdown, a native Docker liveness health check and a disabled-by-default UI port.
No host networking, device access, extra capabilities or API tokens are required.

Includes architecture findings, installation/backup/troubleshooting documentation,
six passing configuration tests, metadata invariants and a GitHub workflow for
schema linting, amd64 image build and Docker deployment tests. Local metadata,
Python syntax, whitespace and the HA add-on schema linter pass. The actual amd64
image builds, starts its first-run UI, handles an unavailable Frigate endpoint,
stops cleanly, preserves state across recreation, rejects credential-bearing
URLs without leaking secrets, and starts from a cold filesystem backup restore.
The unmodified standalone image also starts using that restored configuration.

The Dockerfile supplies its immutable base and current image labels directly;
deprecated build.yaml and watchdog metadata are removed. A native Docker
HEALTHCHECK tests HTTP liveness without treating Frigate outages as restart loops.

Keep this PR in draft until the real-HAOS checklist in
docs/HAOS-VALIDATION.md pass. ARM is unsupported by the pinned upstream image.
Ingress is deferred because the UI lacks prefix-aware routing. The optional
published web port requires a trusted LAN or authenticated reverse proxy.
