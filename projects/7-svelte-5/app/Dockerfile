FROM python:3.12-slim

ARG APP_USER=app_user
ARG APP_DIR=/app

RUN groupadd -r ${APP_USER} && useradd -r -g ${APP_USER} ${APP_USER}

# Install gcc and other build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install git for git pip packages
RUN apt-get update && apt-get install -y git && apt-get clean

WORKDIR ${APP_DIR}

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

RUN chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

USER $USER
ENTRYPOINT ["/app/entrypoint.sh"]
