# Combined native Frigate/Suslik HAOS test package

This is a second add-on, separate from `suslik-addon/`. The standalone add-on
continues to run Suslik's original AdaFace pipeline and full application. The
combined test add-on runs a Frigate fork with adapted temporal confirmation,
cross-camera time grouping, a Visits API and an integrated Visits page. It
shares Frigate's inference; it does not port every standalone Suslik feature.

## Reproducible source and storage

`frigate-suslik-addon/Dockerfile` fetches public fork commit
`c8b5768d42204982d30f63af6ecdc419a9c1adcc` from 5310H/frigate and checks the
source tarball SHA-256 before extraction. Its Node build image and official
Frigate development runtime at upstream commit `2b4397bc` are digest-pinned. The native fork's runtime and compiled
UI are built together; no credentials or installation-specific camera settings
are part of that source archive or image.

The Python entrypoint validates Supervisor options, creates a no-camera config
only for an empty install, preserves existing .yml/.yaml files, and execs the
upstream s6 init. The private Supervisor data volume contains `/data/config`
(Frigate YAML, database, model cache/secrets) and `/data/media` (clips, faces,
exports, recordings). Frigate's standard paths are symlinks into that volume.
No production Frigate or Home Assistant config/media path is mounted. Cold
backups stop the app and include the private volume. Recording starts disabled.

This `0.19.0-dev-suslik.2-1` package is a development preview. Back up all app
data before updating from 0.18.2; downgrade by restoring that backup after
migrations. The prior 0.18.2 source pin remains in Git history.

## Permissions and network

Supervisor USB passthrough is requested for a USB Coral. No PCIe devices, GPU
devices, elevated capabilities, host networking, Docker API or shared host
directories are requested. Protection remains at its default enabled setting.
The app needs no Supervisor/Core API permission; optional inherited Supervisor
tokens are removed before starting s6, avoiding optional go2rtc address discovery.
tmpfs provides temporary cache space. No host ports are published.

The HAOS adapter sets `FRIGATE_RUN_AS_ROOT=true` to retain the previous service
identity: Supervisor mounts `/dev` read-only, so upstream non-root initialization
cannot apply its device ACLs. It does not request additional host capabilities or
modify device permissions. The native standalone image retains upstream defaults.

HA Ingress uses Frigate's existing prefix-aware Nginx/frontend on internal port
5000. Frigate's native Docker health check is retained. The no-camera bootstrap
does not claim the Coral or download face models. Configure the camera, detector
and face recognition in Frigate's own UI after installation. Coral handles
object detection; this USB-only package provides no GPU passthrough and relies
on a compatible CPU for face recognition.

## Upstream development validation (2026-11-02)

- Matching upstream runtime, TypeScript/Vite build and integration-file ESLint pass.
- 26 native tests and 153 upstream configuration/event/camera-access regressions pass.
- OpenAPI and config translations regenerated; API spec freshness check passes.
- Native no-camera s6 startup, Visits API/UI assets and clean shutdown pass.
- The checksummed HA package builds and passes all 26 native tests.
- Package startup, Ingress prefix, restart persistence and cold filesystem restore pass.
- A real 0.18.2 database/config upgrades with SQLite integrity, custom Suslik
  settings and private media preserved. This is a Docker simulation, not a live HAOS upgrade.

## Original 0.18.2 validation (2026-11-02)

- HA add-on linter v2.21.0 and metadata/source-pin/isolation invariants pass.
- Seven bootstrap tests pass: first install, restart preservation, yaml extension,
  invalid options, failed atomic writes, keeping secrets out of seeded YAML,
  and preparing the temporary cache before parallel s6 services start.
- The actual amd64 add-on image builds successfully from the checksummed archive.
- All 26 native logic/config/processor/API tests pass inside that add-on image.
  Processor classifiers are stubbed; these are not recognition-accuracy tests.
- Its real entrypoint/s6 startup serves the native Visits API and compiled UI
  assets. Frigate's Ingress header prefix is reflected in the served UI.
- Private config/database/media survive container recreation and a cold tar
  restore into a new volume. Frigate exits cleanly; s6 may return SIGTERM 143.
- The corresponding native source build additionally passes 114 existing Frigate
  config/event/camera-access regressions, changed-file Ruff/ESLint checks, the
  TypeScript/Vite build and no-camera container startup/shutdown checks.

Physical USB/firmware re-enumeration, real HAOS Ingress/authentication, HA backup
restore, recognition accuracy and CPU load on the target host remain manual
acceptance gates. The older host's face-model/instruction-set compatibility must
be checked before treating it as supported. Local tests do not install on HAOS.

## Updates

Use one reviewed combined app release. To update Frigate, rebase the native
source on the target upstream release and change its source/runtime versions
together. Review and port relevant Suslik changes into the isolated native
module. After tests, update this package's source commit/checksum and app version
together. Upstream releases and Frigate's upstream-update banner do not install
the fork's native changes automatically. Back up before upgrades; migrations
may require a full backup restore for rollback.

Installation and test steps: [add-on guide](../frigate-suslik-addon/DOCS.md).
