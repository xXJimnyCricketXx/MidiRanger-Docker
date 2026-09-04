<p align="center">
  <img src="./static/ressources/midiranger-banner.png" alt="MidiRanger banner" width="100%">
</p>

<p align="center">
  A self-hostable MIDI library manager and player, controllable from any browser on your network.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Self--Hosted-Yes-green.svg" alt="Self-hosted">
  <img src="https://img.shields.io/badge/Docker-Ready-blue.svg" alt="Docker ready">
  <a href="https://github.com/xXJimnyCricketXx/MidiRanger-Docker/actions/workflows/docker-publish.yml">
    <img src="https://github.com/xXJimnyCricketXx/MidiRanger-Docker/actions/workflows/docker-publish.yml/badge.svg" alt="Build status">
  </a>
</p>

## Overview

MidiRanger lets you organize and play a MIDI file collection from a web dashboard instead of
a desktop app. Import songs, tag them with title/artist/genre/BPM/key, mix each channel
(mute/solo/volume/pan) before playing, and send playback either to a software synth
(FluidSynth) or out to real MIDI hardware (e.g. a Roland UM-ONE feeding a hardware
synth/organ) — all from any PC, tablet, or phone on your LAN.

Django rewrite of an earlier PySide6 desktop app. The MIDI/mixer engine
(`mido` / `python-rtmidi` / `pyfluidsynth`) is carried over from the original with only its
Qt (`QObject`/`Signal`) glue removed; playback state is pushed live to the browser over
WebSocket.

## Contents

- [Features](#features)
- [Quick Start (Docker Compose)](#quick-start-docker-compose)
- [Unraid](#unraid)
- [Configuration](#configuration)
- [Tech Stack](#tech-stack)
- [Development](#development)
- [Legacy Database Migration](#legacy-database-migration)

## Features

- **Library Management** — Import MIDI files, tag title/artist/genre/collection/BPM/key/time
  signature, organize by source, favorite songs, and search across your whole collection.
- **Mixer** — Per-channel mute/solo/volume/pan before playback, with GM instrument names
  resolved automatically; export the mixed result as a new MIDI file.
- **Dual Playback Backends** — FluidSynth software synth out of the box, or real hardware
  MIDI output (GM/GS/XG reset detection included) for something like a Roland UM-ONE.
- **Playlists** — Group songs into playlists and play them back in order.
- **Live Status** — Now-playing and status-bar messages update over WebSocket without a
  page reload, so every open browser tab stays in sync.
- **Library Tools** — Bulk metadata analysis, a database-consistency check for missing/moved
  files, and a folder scanner to import new songs in bulk.
- **Backup & Export** — Manual database+library backups, and ZIP export of selected songs.
- **Color Themes** — Several built-in visual themes.
- **Legacy Import** — One-shot migration command to pull songs, sources, and playlists in
  from the original desktop app's SQLite database.

## Quick Start (Docker Compose)

```bash
git clone https://github.com/xXJimnyCricketXx/MidiRanger-Docker.git
cd MidiRanger-Docker
cp .env.example .env
# edit .env and set at least DJANGO_SECRET_KEY (see Configuration below)
docker compose up -d
```

The app is then available at `http://localhost:8000`. Playback over real MIDI hardware
needs the host's ALSA devices passed through (already wired up in `docker-compose.yml` via
`/dev/snd`).

## Unraid

A ready-made template is available at
[`unraid-template/midiranger.xml`](unraid-template/midiranger.xml). In Unraid, go to
**Docker → Add Container**, paste the raw GitHub URL of that file into the **Template**
field, and the port, paths, and variables will be pre-filled. The MIDI library folder
(`originals/`, `uploads/`, `lyrics/`, `mixer_output/`) is its own path mapping, so it can
live on any share — it doesn't have to sit under appdata.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | yes | Random, complex secret used for sessions/CSRF — change this |
| `DJANGO_DEBUG` | no | Debug mode — leave `false` outside of troubleshooting |
| `DJANGO_ALLOWED_HOSTS` | no | Comma-separated allowed hostnames/IPs (`*` = all) |
| `SEED_ADMIN_USERNAME` | no | Admin username, created only on first start (default: `admin`) |
| `SEED_ADMIN_PASSWORD` | no | Admin password, created only on first start — change it afterwards |
| `PORT` | no | Host port the web UI is served on (default: `8000`) |
| `APPDATA_PATH` | docker-compose only | Host folder for DB/logs/backups |
| `MIDI_PATH` | docker-compose only | Existing `midi/` folder (can live on any share) |

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python / Django, Django Channels (WebSocket) |
| Database | SQLite |
| Frontend | Django Templates |
| Realtime Server | Daphne (ASGI) |
| Audio Engine | FluidSynth (`pyfluidsynth`), `mido`, `python-rtmidi` |

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed
python manage.py runserver 0.0.0.0:8000
```

## Legacy Database Migration

If you have an existing `midiranger.db` from the original desktop app, import its songs,
sources, and playlists with:

```bash
python manage.py migrate_legacy_db /path/to/midiranger.db
```

Safe to re-run — existing entries (matched by filename) are updated in place rather than
duplicated. Run **Tools → Datenbank prüfen** afterwards to refresh the missing-file status
against your current MIDI folder.
