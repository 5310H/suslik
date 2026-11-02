# Install and test on Home Assistant OS

This experimental app is a separate Frigate installation. It does not replace
the existing Frigate or standalone Suslik apps.

## Installation

1. Add or refresh `https://github.com/5310H/suslik#feature/haos-addon` in the
   Home Assistant app/add-on store repositories.
2. Install **Frigate + Suslik Test** on amd64 HAOS. Supervisor builds the pinned
   source and UI on the device; the initial download/build is large and can take
   several minutes. Allow several GB of disk and memory headroom.
3. Start it and choose **Open Web UI**. HA Ingress is provided on internal port
   5000. No host ports are published, so it does not conflict with existing
   Frigate ports. The initial config has no cameras, MQTT, recording or face
   inference enabled. The **Visits (Suslik)** page is available in navigation.

All Frigate settings live in its own Settings/configuration UI. The add-on's only
optional Supervisor setting is the existing Frigate `plus_api_key`; it is not
needed for this test. Secrets belong in your private configuration, never an
image, public issue or source repository.

## One-camera USB Coral test

Use a single test camera and a low-resolution detect stream initially. Copy only
that camera's stream settings into this app's Frigate config; do not overwrite
your original Frigate configuration. Frigate's UI can edit and validate the YAML.
The following fragment shows the native settings to combine with that camera:

```yaml
detectors:
  coral:
    type: edgetpu
    device: usb

face_recognition:
  enabled: true
  model_size: small
  suslik:
    enabled: true
    min_samples: 3
    max_attempts: 24
    window_seconds: 3
    min_span_seconds: 0.5
    min_fraction: 0.75
    sample_interval: 0.5
    visit_gap_seconds: 300
```

Enable person detection on the test camera. Keep recording off for the initial
test, and leave MQTT off to avoid mixing this instance's events with production.
Coral accelerates object detection; this USB-only test package passes no GPU
devices and needs a compatible CPU for the face model. It adds no Coral
face-recognition model. The native
implementation shares Frigate's inference rather than running AdaFace again.

**Do not let two running Frigate instances claim the same USB Coral.** Stop the
other instance or disable its Coral detector before starting Coral detection in
this app. Stop the standalone Suslik analyzer while measuring this test to avoid
counting its CPU work. Cameras may also limit simultaneous stream connections.

Enroll faces in this app's Frigate Face Library. Check its logs for a successful
USB EdgeTPU initialization, then observe known and unknown people. Confirm that
Visits preserves unidentified tracks rather than assigning another track's name.
USB product IDs can change during initialization; unplug/replug/restart and
confirm discovery again. Physical USB access is not covered by Docker simulation.

This is a one-camera test package: Supervisor's shared-memory defaults may be
insufficient for many/high-resolution cameras. Recognition model requirements
still apply to older CPUs. No performance or accuracy improvement is guaranteed
until measured on representative recordings.

## Storage, isolation and rollback

Supervisor's private `/data/config` holds Frigate's config, database, model cache
and secrets. `/data/media` holds this app's clips, learned face pictures, exports
and recordings. The image links Frigate's usual `/config` and `/media/frigate`
paths to those directories. It has no shared media, production Frigate config,
Home Assistant config, Docker socket or host-network mount.

All test data survives restart and image recreation. Select this app in HA
backups; cold backup stops it for consistency and includes its private data.
Recordings/model caches make backups larger, which is why recording starts off.
Restore the app and its data to recover it. For upgrades, create a backup first;
database migrations can require restoring the backup when rolling back.

Stop this test app to free the Coral and return to the original installation.
No automatic import, migration or deletion of the original installation occurs.
Uninstalling the test app can remove its own private data, so back it up first.

## Updates and limitations

The Dockerfile pins the tested Frigate fork commit, source-archive checksum,
official Frigate runtime digest and Node build image. Updates require a reviewed
combined release: rebase on upstream Frigate, port relevant upstream Suslik
changes, test, then update the source pin/checksum and app version together.
Upstream Frigate/Suslik releases do not independently update this fork.

This ports confirmation/grouping and a Visits view, not every standalone Suslik
learning, reference or notification page. Existing Frigate screens provide face
enrollment/configuration. Names in retained historical events reflect their
stored labels; time grouping does not identify unknown people across cameras.

Protected mode remains enabled. USB access is needed for the USB Coral; tmpfs
provides temporary segment/cache space. No elevated capabilities or Supervisor/
Home Assistant API token is needed. Use the Log tab for startup failures. A
native Docker health check is inherited from Frigate. Actual HAOS Ingress,
USB passthrough, recognition accuracy, CPU load and HA backup/restore are manual
acceptance gates; local container tests are simulations.
