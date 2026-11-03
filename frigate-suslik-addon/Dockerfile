# syntax=docker/dockerfile:1
FROM golang:1.25@sha256:699337d620559a59b4a2bb298ad59611e535d2ee755a34cf2d2a98f37578dc80 AS go2rtc-build
ADD --checksum=sha256:78aa79bcedec8f155e4060a379613979b0b3ee48ff62ee5164bafc0ac6532386 https://codeload.github.com/AlexxIT/go2rtc/tar.gz/b5948cfb25404cc5cb37b166ecaa2dca20b11d4b /go2rtc.tar.gz
RUN mkdir /go2rtc && tar -xzf /go2rtc.tar.gz --strip-components=1 -C /go2rtc
WORKDIR /go2rtc
COPY go2rtc/doorbell-v1.patch /doorbell-v1.patch
RUN git apply --check /doorbell-v1.patch && git apply /doorbell-v1.patch
COPY go2rtc/tests/ ./
RUN test -z "$(gofmt -l pkg/tutk/dtls/dtls.go pkg/tutk/dtls/doorbell_test.go pkg/tutk/frame.go pkg/tutk/doorbell_test.go pkg/wyze/client.go pkg/wyze/doorbell_test.go internal/app/app.go)" \
    && go test -timeout 90s ./pkg/tutk/... ./pkg/wyze/... ./internal/wyze/... \
    && go vet ./pkg/tutk/... ./pkg/wyze/... ./internal/wyze/... \
    && CGO_ENABLED=0 go build -trimpath -buildvcs=false -ldflags="-s -w" -o /out/go2rtc .

FROM node:22@sha256:18a6d90fd60542269850c80ca03b29b1d9b14d6b221ac7ee8e35b0d33ef904bd AS source
ARG SOURCE_COMMIT=9a82408ce6ccceeccd15bc8997c25683e87364eb
ADD --checksum=sha256:b133942788df170f9cbdbcdfa155bd71957bec6e2e40f85e7c7fdb245dcb2c12 https://codeload.github.com/5310H/frigate/tar.gz/${SOURCE_COMMIT} /source.tar.gz
RUN mkdir /source && tar -xzf /source.tar.gz --strip-components=1 -C /source

FROM source AS web-build
WORKDIR /source/web
RUN npm ci --no-audit --no-fund \
    && npm run build \
    && mv dist/BASE_PATH/monacoeditorwork/* dist/assets/ \
    && rm -rf dist/BASE_PATH

FROM ghcr.io/blakeblackshear/frigate:2b4397b@sha256:14e29e06409f57861a14db8c3d415d18956daf7ea6d7f9131901140723b61254
COPY --from=source /source/frigate/ /opt/frigate/frigate/
COPY --from=web-build /source/web/dist/ /opt/frigate/web/
COPY --from=source /source/LICENSE-SUSLIK /opt/frigate/LICENSE-SUSLIK
COPY --from=go2rtc-build /out/go2rtc /usr/local/go2rtc/bin/go2rtc
COPY --from=go2rtc-build /go2rtc/LICENSE /usr/share/licenses/go2rtc/LICENSE
COPY go2rtc/README.md /usr/share/licenses/go2rtc/DOORBELL-PATCH.md
COPY start.py /ha/start.py
COPY wyze_setup.py /ha/wyze_setup.py
RUN mkdir -p /config /media/frigate \
    && rmdir /config /media/frigate \
    && ln -s /data/config /config \
    && ln -s /data/media /media/frigate \
    && python3 -c 'from pathlib import Path; Path("/opt/frigate/frigate/version.py").write_text("VERSION = \"0.19.0-dev-suslik.2\"\n")'
ARG BUILD_VERSION=0.19.0-dev-suslik.2-3
ARG BUILD_ARCH=amd64
LABEL io.hass.type="app" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/5310H/suslik" \
      org.opencontainers.image.title="Frigate + Suslik HAOS Test"
ENTRYPOINT ["python3", "/ha/start.py"]
CMD []
