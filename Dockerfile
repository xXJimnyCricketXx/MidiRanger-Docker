# syntax=docker/dockerfile:1

# --- Stage 1: Build ---------------------------------------------------
# python-rtmidi (ALSA-Anbindung für den Roland-Backend-Port) ist eine
# native C-Extension und braucht zum Bauen Compiler + ALSA-Header.
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
        libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime ---------------------------------------------------
FROM python:3.12-slim

# libasound2: Laufzeit-ALSA für python-rtmidi (Roland/UM-ONE).
# libfluidsynth3 (+ libsndfile1): Laufzeit-Synth für pyfluidsynth - ersetzt
# die unter Windows genutzten DLLs aus assets/lib/.
# fluid-soundfont-gm: liefert exakt FluidR3_GM.sf2 unter /usr/share/sounds/sf2/
# - ersetzt die lokale Kopie aus assets/sf2/ (142 MB, nicht Teil des Git-Repos,
# da über GitHubs 100-MB-Push-Limit).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libasound2 \
        libfluidsynth3 \
        libsndfile1 \
        fluid-soundfont-gm \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY manage.py .
COPY midiranger/ midiranger/
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY scripts/entrypoint.sh scripts/entrypoint.sh
RUN chmod +x scripts/entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=midiranger.settings \
    MR_DATA_DIR=/data \
    MR_MIDI_DIR=/midi \
    MR_SOUNDFONT_PATH=/usr/share/sounds/sf2/FluidR3_GM.sf2 \
    PORT=8000

EXPOSE 8000
VOLUME ["/data", "/midi"]

ENTRYPOINT ["scripts/entrypoint.sh"]
