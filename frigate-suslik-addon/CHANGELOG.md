# Changelog

## 0.18.2-suslik.1-2

- Create the temporary cache before starting s6, preventing go2rtc's first-start
  HomeKit setup from racing Frigate's cache-directory creation.
- Verify cache preparation on new and existing configurations and check startup
  logs for the missing-directory regression.

## 0.18.2-suslik.1-1

- Initial isolated HAOS test package for the native Frigate/Suslik prototype.
- Shared Frigate inference, temporal confirmation and native Visits UI/API.
- Private config/database/media under /data; cold backups and HA Ingress.
- USB Coral access, no host networking or published ports, manual start by default.
