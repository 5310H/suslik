# syntax=docker/dockerfile:1
FROM node:20@sha256:8f693eaa7e0a8e71560c9a82b55fd54c2ae920a2ba5d2cde28bac7d1c01c9ba5 AS source
ARG SOURCE_COMMIT=dc27b5a9eaeb2f469336722fa51f36cc05cfccba
ADD --checksum=sha256:cdbc4c41e6219129c2bc96523339fb031a930d626de6ac0e6651e769267c0c60 https://codeload.github.com/5310H/frigate/tar.gz/${SOURCE_COMMIT} /source.tar.gz
RUN mkdir /source && tar -xzf /source.tar.gz --strip-components=1 -C /source

FROM source AS web-build
WORKDIR /source/web
RUN npm ci --no-audit --no-fund \
    && npm run build \
    && mv dist/BASE_PATH/monacoeditorwork/* dist/assets/ \
    && rm -rf dist/BASE_PATH

FROM ghcr.io/blakeblackshear/frigate:0.18.2@sha256:fd60f99ffd4eb6c42360ed4e14953e270586f239309ab3983e55b2e97ffac09a
COPY --from=source /source/frigate/ /opt/frigate/frigate/
COPY --from=web-build /source/web/dist/ /opt/frigate/web/
COPY --from=source /source/LICENSE-SUSLIK /opt/frigate/LICENSE-SUSLIK
COPY start.py /ha/start.py
RUN mkdir -p /config /media/frigate \
    && rmdir /config /media/frigate \
    && ln -s /data/config /config \
    && ln -s /data/media /media/frigate \
    && python3 -c 'from pathlib import Path; Path("/opt/frigate/frigate/version.py").write_text("VERSION = \"0.18.2-suslik.1\"\n")'
ARG BUILD_VERSION=0.18.2-suslik.1-2
ARG BUILD_ARCH=amd64
LABEL io.hass.type="app" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/5310H/suslik" \
      org.opencontainers.image.title="Frigate + Suslik HAOS Test"
ENTRYPOINT ["python3", "/ha/start.py"]
CMD []
