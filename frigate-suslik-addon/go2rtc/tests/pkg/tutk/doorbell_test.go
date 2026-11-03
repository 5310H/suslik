package tutk

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"testing"
	"time"
)

func doorbellPacket(kind, channel byte, size int, payload []byte) []byte {
	header := 28
	if kind == FrameTypeStartAlt || kind == FrameTypeEndExt {
		header = 36
	}
	b := make([]byte, header+len(payload)+size)
	b[0], b[1] = channel, kind
	total, marker, frame := 12, 14, 24
	if header == 36 {
		total, marker, frame = 20, 22, 32
	}
	binary.LittleEndian.PutUint16(b[total:], 1)
	binary.LittleEndian.PutUint16(b[marker:], uint16(size))
	binary.LittleEndian.PutUint32(b[frame:], 7)
	copy(b[header:], payload)
	fi := b[header+len(payload):]
	fi[0], fi[2] = CodecH264, 1
	binary.LittleEndian.PutUint32(fi[8:], 123456)
	binary.LittleEndian.PutUint32(fi[12:], 1700000000)
	binary.LittleEndian.PutUint32(fi[16:], uint32(len(payload)))
	binary.LittleEndian.PutUint32(fi[20:], 7)
	return b
}

func TestDoorbellAndV3FrameLayouts(t *testing.T) {
	payload := []byte{0, 0, 0, 1, 0x65, 0x88, 0x99}
	for _, kind := range []byte{FrameTypeEndSingle, FrameTypeEndExt, FrameTypeStartAlt} {
		for _, size := range []int{40, 48} {
			t.Run(fmt.Sprintf("kind_%d_trailer_%d", kind, size), func(t *testing.T) {
				wire := doorbellPacket(kind, ChannelIVideo, size, payload)
				h := NewFrameHandler(false)
				defer h.Close()
				h.Handle(wire)
				select {
				case got := <-h.Recv():
					if !bytes.Equal(got.Payload, payload) || got.Codec != CodecH264 || !got.IsKeyframe || got.FrameNo != 7 {
						t.Fatalf("corrupted frame: %+v", got)
					}
				default:
					t.Fatal("valid camera frame was discarded")
				}
			})
		}
	}
}

func TestContinuationIndexesAreNotFrameInfo(t *testing.T) {
	for _, index := range []uint16{40, 48, 100} {
		wire := make([]byte, 28)
		wire[1] = FrameTypeCont
		binary.LittleEndian.PutUint16(wire[12:], 150)
		binary.LittleEndian.PutUint16(wire[14:], index)
		h := ParsePacketHeader(wire)
		if h.HasFrameInfo || h.PktIdx != index {
			t.Fatalf("continuation %d misread as a trailer: %+v", index, h)
		}
	}
}

func TestTruncatedDoorbellPacketsDoNotPanic(t *testing.T) {
	wire := doorbellPacket(FrameTypeEndSingle, ChannelIVideo, 48, []byte{1, 2, 3})
	for n := 0; n < len(wire); n++ {
		h := NewFrameHandler(false)
		h.Handle(wire[:n])
		h.Close()
	}
}

func TestDeviceTimestampWrapAndDeadClock(t *testing.T) {
	var normal tsTracker
	normal.update(950000)
	if got := normal.update(0); got != 50000 {
		t.Fatalf("timestamp wrap: got %d", got)
	}
	if got := normal.update(50000); got != 100000 || normal.synth {
		t.Fatalf("advancing v3 timestamps changed: %d", got)
	}
	var dead tsTracker
	dead.update(0)
	for n := 0; n < tsDeadThreshold; n++ {
		dead.lastWall = time.Now().Add(-50 * time.Millisecond)
		dead.update(0)
	}
	before := dead.accumUS
	dead.lastWall = time.Now().Add(-50 * time.Millisecond)
	after := dead.update(0)
	if !dead.synth || after <= before || after-before < 40000 || after-before > 1000000 {
		t.Fatalf("doorbell timeline failed to advance: %d -> %d", before, after)
	}
}
