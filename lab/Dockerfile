# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm
WORKDIR /app

# Trust the session CA only during the build; never disable TLS or APT signatures.
RUN --mount=type=secret,id=proxy_ca,required=true \
    cat /etc/ssl/certs/ca-certificates.crt /run/secrets/proxy_ca > /tmp/build-ca.pem && \
    sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get -o Acquire::https::CaInfo=/tmp/build-ca.pem update && \
    apt-get -o Acquire::https::CaInfo=/tmp/build-ca.pem install -y --no-install-recommends \
      iproute2 tcpdump coturn ffmpeg procps libatomic1 && \
    python -m pip install --cert /tmp/build-ca.pem --no-cache-dir uv==0.13.6 && \
    rm -f /tmp/build-ca.pem && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /app/
RUN --mount=type=secret,id=proxy_ca,required=true \
    cat /etc/ssl/certs/ca-certificates.crt /run/secrets/proxy_ca > /tmp/build-ca.pem && \
    SSL_CERT_FILE=/tmp/build-ca.pem uv sync --frozen --no-install-project && \
    printf 'Acquire::https::CaInfo "/tmp/build-ca.pem";\n' > /tmp/build-apt.conf && \
    APT_CONFIG=/tmp/build-apt.conf NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca \
      /app/.venv/bin/playwright install --with-deps chromium firefox && \
    rm -f /tmp/build-ca.pem /tmp/build-apt.conf && rm -rf /var/lib/apt/lists/*

COPY src /app/src
RUN --mount=type=secret,id=proxy_ca,required=true \
    cat /etc/ssl/certs/ca-certificates.crt /run/secrets/proxy_ca > /tmp/build-ca.pem && \
    SSL_CERT_FILE=/tmp/build-ca.pem uv sync --frozen && rm -f /tmp/build-ca.pem

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
CMD ["python", "-m", "ease_rtc.live_lab", "--help"]
