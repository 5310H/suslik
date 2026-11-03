# Camera protocol follow-up

The 0.19 development preview already includes upstream go2rtc 1.9.14. Camera
protocol work is separate from the upstream/Suslik integration release.

## Wyze

Initial acceptance targets requested by the user: Wyze Cam v3 and the original
Wyze Floodlight using a v3 camera. Verify each model/firmware on real hardware.

[go2rtc Wyze source](https://github.com/AlexxIT/go2rtc/blob/master/internal/wyze/README.md)
provides native local P2P in 1.9.14 for compatible DTLS-enabled firmware. Account
camera discovery requires Wyze authentication and API ID/key; streaming is then
local. The existing built-in restreamer should be reused, with a Frigate camera
setup path that discovers/selects a camera, validates its stream and configures
local detect/record/live inputs. Do not add a second decoder or Wyze bridge when
the included native source supports the camera. Keep credentials in private
storage and out of source, URLs displayed to users, and logs. The user completes
account authentication. Thingino cameras should retain their working RTSP path.

The 0.19.0-dev-suslik.2-2 test package adds the proposed Doorbell v1 fixes
from go2rtc PR #2399 on a checksummed v1.9.14 base, plus protocol regression
tests and a private interactive setup helper. See the add-on DOCS.md and
go2rtc/README.md for setup and patch provenance. Target WYZEDB3 firmware is
4.25.1.368; the PR author tested 4.25.1.333. Neither the requested doorbell
firmware nor Floodlight/v3 4.36.17.21 has passed our physical acceptance yet.
No new graphical onboarding UI or live Wyze account test has been completed.
A successful RTSP test does not verify stock Wyze P2P compatibility.

## Reolink Baichuan

The requested product is [Reostream](https://github.com/VoltTech21/reostream), not
a generic restreaming service. Its Baichuan receiver exposes RTSP and HTTP MPEG-TS
for Frigate/go2rtc. An optional supervised process inside the combined package can
feed its local RTSP output into the existing go2rtc instance and Frigate inputs.
Keep its private config separate, use loopback/internal ports, and preserve normal
RTSP cameras. Pin a reviewed source/runtime and retain its license/attribution.
Its documented license is AGPL v3; source changes must remain available as required.

No Reostream binary, service, onboarding UI or real Reolink acceptance test is
included in the current upstream integration release. A camera model is still
needed before setting hardware acceptance criteria.
