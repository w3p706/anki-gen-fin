# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

RUN apt update &&  apt -y install wget curl

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Installs nightly cg3 see here: https://mikalikes.men/how-to-install-visl-cg3-on-mac-windows-and-linux/
RUN curl https://apertium.projectjj.com/apt/apertium-packaging.public.gpg > /etc/apt/trusted.gpg.d/apertium.gpg && \
    curl https://apertium.projectjj.com/apt/apertium.pref >/etc/apt/preferences.d/apertium.pref && \
    echo "deb http://apertium.projectjj.com/apt/nightly bookworm main" > /etc/apt/sources.list.d/apertium.list && \
    apt-get -qy update >/dev/null 2>&1 && \
    yes | apt-get install cg3 && \
    cg3 --version

# https://github.com/mikahama/uralicNLP?tab=readme-ov-file#faster-analysis-and-generation
# https://github.com/mikahama/uralicNLP?tab=readme-ov-file#download-models
RUN pip install --upgrade --force-reinstall pyhfst --no-cache-dir && \
    python -m uralicNLP.download --languages fin eng 


FROM base as container

# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY ankigenfin ./ankigenfin
COPY anki-card-template ./anki-card-template
COPY process.py .
COPY data_tools.py .
COPY logger.py .
COPY seed.sqlite3 .




FROM base as create_seed_db

# Switch to the non-privileged user to run the application.
RUN chmod -R a+w . 
USER appuser

# Copy the source code into the container.
COPY --chown=appuser:appuser ankigenfin ./ankigenfin
COPY anki-card-template ./anki-card-template
COPY process.py .
COPY data_tools.py .
COPY logger.py .
COPY config.yml .

# # this is needed because of @retry decorator will run on import
ENV CONFIG config.yml  

RUN python data_tools.py generate-seed-db

# https://stackoverflow.com/a/58752370
FROM scratch as seed_db
COPY --from=create_seed_db /app/seed.sqlite3 .

