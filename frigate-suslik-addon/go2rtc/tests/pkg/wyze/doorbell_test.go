package wyze

import (
	"encoding/binary"
	"testing"
)

func TestDoorbellResolutionAndV3Regression(t *testing.T) {
	for _, tc := range []struct {
		model   string
		quality byte
		command uint16
		frame   byte
		bitrate uint16
	}{
		{"WYZEDB3", 0, KCmdSetResolutionDB, 4, 0xB4},
		{"WYZEDB3", FrameSize360P, KCmdSetResolutionDB, 2, BitrateSD},
		{"WYZE_CAKP2JFUS", 0, KCmdSetResolution, 1, BitrateMax},
		{"WYZE_CAKP2JFUS", FrameSize360P, KCmdSetResolution, 2, BitrateSD},
	} {
		client := &Client{model: tc.model}
		wire, response := client.resolutionCommand(tc.quality)
		if string(wire[:2]) != "HL" || binary.LittleEndian.Uint16(wire[4:]) != tc.command || response != tc.command+1 {
			t.Fatalf("wrong resolution command for %s: %x", tc.model, wire)
		}
		frame, bitrate := wire[16], binary.LittleEndian.Uint16(wire[17:])
		if tc.command == KCmdSetResolutionDB {
			frame, bitrate = wire[18], binary.LittleEndian.Uint16(wire[16:])
		}
		if frame != tc.frame || bitrate != tc.bitrate {
			t.Fatalf("%s quality %d: frame %d bitrate %d", tc.model, tc.quality, frame, bitrate)
		}
	}
}
