package dtls

import (
	"context"
	"net"
	"testing"
	"time"

	pion "github.com/pion/dtls/v3"
)

func TestWyzeHandshakeSupportsDoorbellAESAndV3ChaCha(t *testing.T) {
	for _, legacy := range []bool{true, false} {
		name := "v3_chacha"
		if legacy {
			name = "doorbell_aes"
		}
		t.Run(name, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 6*time.Second)
			defer cancel()
			server, err := net.ListenPacket("udp4", "127.0.0.1:0")
			if err != nil {
				t.Fatal(err)
			}
			defer server.Close()
			client, err := net.ListenPacket("udp4", "127.0.0.1:0")
			if err != nil {
				t.Fatal(err)
			}
			defer client.Close()
			psk := []byte("test-only-doorbell-psk")
			cfg := buildDTLSConfig(psk, true)
			if !legacy {
				cfg.CipherSuites = nil
				cfg.CustomCipherSuites = CustomCipherSuites
			}
			remote, err := pion.Server(server, client.LocalAddr(), cfg)
			if err != nil {
				t.Fatal(err)
			}
			defer remote.Close()
			serverDone := make(chan error, 1)
			go func() { serverDone <- remote.HandshakeContext(ctx) }()
			incoming := make(chan []byte, 32)
			go func() {
				for {
					b := make([]byte, 2048)
					n, _, err := client.ReadFrom(b)
					if err != nil {
						return
					}
					select {
					case incoming <- b[:n]:
					case <-ctx.Done():
						return
					}
				}
			}()
			conn, err := NewDTLSClient(ctx, 0, server.LocalAddr(), func(b []byte, _ uint8) error {
				_, err := client.WriteTo(b, server.LocalAddr())
				return err
			}, incoming, psk)
			if err != nil {
				t.Fatal(err)
			}
			defer conn.Close()
			if err := <-serverDone; err != nil {
				t.Fatal(err)
			}
			// Exercise encrypted data, not just the cipher configuration.
			go func() { _, _ = conn.Write([]byte("doorbell-frame")) }()
			_ = remote.SetReadDeadline(time.Now().Add(time.Second))
			b := make([]byte, 64)
			n, err := remote.Read(b)
			if err != nil || string(b[:n]) != "doorbell-frame" {
				t.Fatalf("encrypted transfer: %q %v", b[:n], err)
			}
		})
	}
}
