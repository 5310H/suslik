# Changelog

## 0.1.1.048-2

- Move the immutable base reference into Dockerfile and remove deprecated build.yaml.
- Use current Home Assistant image labels and enforce version consistency in validation.
- Replace the obsolete watchdog URL with a native Docker liveness health check.
- Remove redundant Supervisor defaults flagged by the Home Assistant add-on linter.

## 0.1.1.048-1

- Initial experimental amd64 Home Assistant add-on around Suslik 0.1.1.048 CPU.
- Validated Supervisor options, preserved application config and private data.
- Disabled-by-default web port, cold backups, health watchdog and clean exec startup.
- Added Docker simulation CI and documented HAOS acceptance checks.
