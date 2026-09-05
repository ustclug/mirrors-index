FROM node:22-trixie

ARG ESBUILD_VERSION=0.28.2
ARG PNPM_VERSION=11.3.0
ARG PRETTIER_VERSION=3.8.1
ARG RUFF_VERSION=0.16.6
ARG TYPESCRIPT_VERSION=6.0.3

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=zh_CN.UTF-8 \
    LC_ALL=zh_CN.UTF-8 \
    PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
    TZ=Asia/Shanghai

RUN apt-get update \
    && apt-get install --no-install-recommends --yes \
        ca-certificates \
        chromium \
        git \
        locales \
        make \
        pipx \
        python3 \
        python3-jinja2 \
        python3-requests \
        tzdata \
    && localedef --inputfile=zh_CN --charmap=UTF-8 zh_CN.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

RUN npm install --global \
        "esbuild@${ESBUILD_VERSION}" \
        "pnpm@${PNPM_VERSION}" \
        "prettier@${PRETTIER_VERSION}" \
        "typescript@${TYPESCRIPT_VERSION}" \
    && PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin \
        pipx install "ruff==${RUFF_VERSION}"

WORKDIR /workspace

COPY --chown=node:node package.json pnpm-lock.yaml ./
RUN su node -c 'pnpm install --frozen-lockfile --ignore-scripts'

COPY --chown=node:node . .

RUN install --directory --owner=node --group=node /srv/repo

USER node

EXPOSE 8000
CMD ["bash"]
