# Validation and release checklist

## Executed locally

- Six stdlib unit tests passed on Python 3.12 (2026-11-02).
- YAML/JSON parsing and cross-file metadata invariants passed with PyYAML 6.0.3.
- Home Assistant add-on linter v2.21.0 passed (its unmodified Docker image, built
  from upstream commit f995494fd84fae6310d23617e66d0e37de4f14eb).
- The amd64 add-on image built successfully from the immutable CPU release.
- Actual-image Docker tests passed with init enabled, no external network, no
  published ports and private named volumes: first-run UI without credentials,
  HTTP health check, unavailable Frigate, clean exit code 0 on stop, container
  recreation, preserved settings/credentials/learning data, invalid options
  rejected without leaking their secret, and cold tar backup/restore.
- The unmodified pinned standalone image starts with the add-on's restored store
  and preserves the checked settings, credentials and learning data on shutdown.
- Python syntax checks and git diff whitespace checks passed.
- Registry manifest verified: pinned CPU release provides linux/amd64 only.
- Existing application Python, Dockerfiles and standalone configs are unchanged.

## Remaining validation

Docker Desktop was started and the local build/runtime tests above completed.
These tests simulate deployment and filesystem backup; they do not run Supervisor
or Home Assistant OS. No real Frigate, camera recordings, recognition corpus,
MQTT broker or HA installation was available. Future application-version upgrade
migrations are not tested by recreating the same image.

## Before production acceptance

- Confirm the GitHub workflow runs on the repository; local equivalents pass.
- Register `https://github.com/5310H/suslik#feature/haos-addon` before merge (or
  the plain repository URL after merge) and confirm store discovery on amd64 HAOS.
- Install, configure Frigate, complete the wizard, analyze known recordings and
  compare results with the same standalone CPU version.
- Test valid/invalid Frigate credentials and unavailable Frigate/MQTT endpoints;
  confirm actionable logs without publishing secrets. Wrapper validation tests
  do not exercise real Frigate authentication.
- Enable a trusted-network UI port, confirm disabled ports remain inaccessible.
- Stop/restart under Supervisor, confirm no forced kill and no lost learning data.
- Create and restore an HA cold backup containing this add-on; confirm settings,
  references and credentials survive. Repeat with a future upgraded image and
  restore the pre-upgrade backup to verify rollback.
- Measure CPU, memory and storage on target hardware before enabling live watchers.

No real HAOS acceptance or aarch64 compatibility is claimed by this change.
