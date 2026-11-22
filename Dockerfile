FROM debian:13-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-requests ca-certificates && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY genmirrorz.py gencontent.py utils.py genisolist.py version.py ./
COPY config/cname.json config/descriptions.json ./config/
COPY z-genisolist/includes/ ./includes/
ENV MIRRORS_CONFIG_DIR=/config PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
ENTRYPOINT ["python3", "/app/genmirrorz.py"]
CMD ["--output", "/output/mirrorz.json"]
