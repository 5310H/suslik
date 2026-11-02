# Validation and release checklist

## Executed locally

- Six stdlib unit tests passed on Python 3.12 (2026-11-02).
- YAML/JSON parsing and cross-file metadata invariants passed with PyYAML 6.0.3.
- Python syntax checks and git diff whitespace checks passed.
- Registry manifest verified: pinned CPU release provides linux/amd64 only.
- Existing application Python, Dockerfiles and standalone configs are unchanged.

## Not executed locally

Docker Desktop has no running Linux daemon. Image build, actual application
startup, recognition, process shutdown and container recreation tests could not
run locally. The GitHub workflow contains an amd64 build and actual-image Docker
smoke test; adding a workflow is not evidence that it has passed.

## Before production acceptance

- Run the workflow, including the Home Assistant add-on schema linter.
- Register this repository after merge and confirm store discovery on amd64 HAOS.
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
