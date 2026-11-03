# Changelog

## 0.19.0-dev-suslik.2-5

- Enable host networking for direct local Wyze P2P connections without Docker
  bridge NAT. This does not establish the cause of camera handshake timeouts.
- Retain ingress and private storage; document shared listening ports, direct
  service access, and update/restart verification.

## 0.19.0-dev-suslik.2-3

- Add Connect a Wyze camera to the Add Camera UI: private account discovery,
  camera selection, current IP, validated saving and an explicit restart button.
- Keep device keys on the server, expire discovery sessions after ten minutes,
  restrict discovery/saving to admins, and preserve existing cameras/Coral settings.
- Fix the Terminal helper's Frigate import path when launched directly from /ha.
- Hardware compatibility remains experimental; successful discovery does not
  establish working live video on the requested firmware.

## 0.19.0-dev-suslik.2-2

- Bundle a pinned go2rtc build with the proposed Doorbell v1 AES/DTLS,
  frame-layout, resolution and timestamp fixes, retaining the v3 path.
- Add private interactive Wyze discovery and validated configuration saving
  with rollback copies; no separate bridge or additional exposed ports.
- Test protocol negotiation, frames, resolution commands and configuration
  preservation. Doorbell firmware 4.25.1.368 and Floodlight/v3 firmware
  4.36.17.21 still require physical camera acceptance.

## 0.19.0-dev-suslik.2-1

- Integrate upstream Frigate dev commit 2b4397bc (2026-11-02), preserving
  native Suslik confirmation, grouping, and Visits UI/API.
- Pin the matching official upstream runtime and a Node 22 web build image.
- Retain root service execution in the HAOS adapter for its read-only device
  mount and existing private storage; native Docker keeps upstream defaults.
- Development preview: create a full app backup before upgrading. Restore that
  backup to downgrade after upstream database/config migrations.

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
