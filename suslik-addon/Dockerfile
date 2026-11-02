FROM ghcr.io/bennobaer-dev/suslik:0.1.1.048-cpu@sha256:0a73af4efad3a595d7104881015d7eca51f4d318d820c40f018c9f093c0df636
ARG BUILD_VERSION=0.1.1.048-2
ARG BUILD_ARCH=amd64
LABEL io.hass.type="app" io.hass.version="${BUILD_VERSION}" io.hass.arch="${BUILD_ARCH}"
COPY configure.py /app/ha_configure.py
COPY run.sh /app/ha_run.sh
ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8199/health', timeout=5).close()"]
ENTRYPOINT ["/bin/sh", "/app/ha_run.sh"]
CMD []
