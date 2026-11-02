ARG BUILD_FROM=ghcr.io/bennobaer-dev/suslik:0.1.1.048-cpu@sha256:0a73af4efad3a595d7104881015d7eca51f4d318d820c40f018c9f093c0df636
FROM ${BUILD_FROM}
ARG BUILD_VERSION=0.1.1.048-1
ARG BUILD_ARCH=amd64
LABEL io.hass.type="addon" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}"
COPY configure.py /app/ha_configure.py
COPY run.sh /app/ha_run.sh
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["/bin/sh", "/app/ha_run.sh"]
CMD []
