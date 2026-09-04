# MidiRanger

Self-hosted MIDI file manager and player. Import and organize your MIDI library, edit
per-channel mix (mute/solo/volume/pan), and play songs out to a real MIDI device
(e.g. a Roland UM-ONE mk2 feeding a hardware synth/organ) — controlled from any
browser on your LAN (PC or tablet).

Django rewrite of the original PySide6 desktop app. The MIDI/mixer engine
(`mido`/`python-rtmidi`/`pyfluidsynth`) is carried over from the original with only
its Qt (`QObject`/`Signal`) glue removed; the UI is rebuilt as server-rendered
Django templates.

Status: early development, not yet functional beyond login/dashboard/settings.

## Development

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed
python manage.py runserver 0.0.0.0:8000
```

## Docker

Built and published automatically to `ghcr.io` via GitHub Actions. See
`unraid-template/midiranger.xml` for the Unraid Community Applications template.
