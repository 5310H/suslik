# go2rtc Doorbell v1 test build

Base: AlexxIT/go2rtc v1.9.14, commit b5948cfb25404cc5cb37b166ecaa2dca20b11d4b.
Source archive SHA256: 78aa79bcedec8f155e4060a379613979b0b3ee48ff62ee5164bafc0ac6532386.

Adapted from https://github.com/AlexxIT/go2rtc/pull/2399 by welovejeff, crediting
jdeath's original fixes in PR #2249. Reviewed PR head:
ac3444ba184c9109d397abbdb829a92eb7e3bc13. Only the three Wyze/TUTK files are
adapted, not the PR branch's unrelated upstream changes.

Changes: retain modern ChaCha PSK negotiation while adding the Doorbell v1 AES
suite; handle 40/48-byte frame trailers; use the doorbell's auto resolution;
and pace RTP timestamps when firmware never advances the device timestamp.
Local additions handle 48-byte trailers on single StartAlt frames, isolate the
resolution command for wire-level tests, and report 1.9.14+wyzedb3.1 in go2rtc.
The runtime retains the upstream MIT license, copied alongside this notice.

Regression tests exercise real local DTLS AES and ChaCha handshakes plus encrypted
payloads, standard/v1 frame layouts including StartAlt, truncated frames,
continuation indexes, timestamp wrap/dead clocks, and v3/doorbell resolution
commands. These do not replace testing on a physical camera.

Firmware 4.25.1.333 was reported working by the PR author. The requested target
4.25.1.368 has not yet been verified. Keep current firmware for the first test.
Wyze v3 and the original Floodlight/v3 use the existing model path; firmware
4.36.17.21 still needs physical acceptance. No separate bridge is added.
