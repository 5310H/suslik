# syntax=docker/dockerfile:1
FROM node:22@sha256:18a6d90fd60542269850c80ca03b29b1d9b14d6b221ac7ee8e35b0d33ef904bd AS source
ARG SOURCE_COMMIT=c8b5768d42204982d30f63af6ecdc419a9c1adcc
ADD --checksum=sha256:a7e34aa3671a0d460e36f91909d21228b50feda3d052040d10ae271d524e7f86 https://codeload.github.com/5310H/frigate/tar.gz/${SOURCE_COMMIT} /source.tar.gz
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
COPY start.py /ha/start.py
RUN mkdir -p /config /media/frigate \
    && rmdir /config /media/frigate \
    && ln -s /data/config /config \
    && ln -s /data/media /media/frigate \
    && python3 -c 'from pathlib import Path; Path("/opt/frigate/frigate/version.py").write_text("VERSION = \"0.19.0-dev-suslik.2\"\n")'
ARG BUILD_VERSION=0.19.0-dev-suslik.2-1
ARG BUILD_ARCH=amd64
LABEL io.hass.type="app" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/5310H/suslik" \
      org.opencontainers.image.title="Frigate + Suslik HAOS Test"
ENTRYPOINT ["python3", "/ha/start.py"]
CMD []
