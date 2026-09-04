# Port von dev-modus/alt/src/audio/midi_engine.py - reiner Python-Dispatcher,
# keine Qt-Abhängigkeit, unverändert übernommen.
import logging
from typing import Type, Dict, List, Optional, Any

from .fluidsynth_backend import FluidSynthBackend
from .roland_backend import RolandBackend

logger = logging.getLogger('midiranger')


class MidiEngine:

    # -----------------------------------------------------------------------
    # Zentrale Audio Engine.
    #
    # Wählt anhand eines Backend-Namens die konkrete Backend-Implementierung
    # und bietet eine einheitliche API für den PlayerController.
    # -----------------------------------------------------------------------

    _BACKENDS: Dict[str, Type] = {
        "fluidsynth": FluidSynthBackend,
        "roland": RolandBackend,
    }

    @classmethod
    def available_backends(cls) -> List[str]:
        """Liste der bekannten Backend-Namen (für Settings-Dialog)."""
        return sorted(cls._BACKENDS.keys())

    def __init__(self, backend_name: str = "fluidsynth", **backend_opts: Any):
        self._backend_name: str = "fluidsynth"
        self.backend = None
        self._backend_opts: Dict[str, Any] = {}
        self._build_backend(backend_name, **backend_opts)
        logger.debug(f"🎧 MidiEngine initialisiert (Backend: {self._backend_name})")

    # ------------------------------------------------------------
    # Backend-Aufbau/Wechsel
    # ------------------------------------------------------------
    def _build_backend(self, backend_name: str, **backend_opts: Any):
        backend_key = (backend_name or "fluidsynth").lower().strip()
        if backend_key not in self._BACKENDS:
            logger.warning(f"⚠️ Unbekanntes Backend '{backend_name}', nutze 'fluidsynth'.")
            backend_key = "fluidsynth"

        backend_cls = self._BACKENDS[backend_key]
        self._backend_name = backend_key
        self._backend_opts = dict(backend_opts or {})

        try:
            if backend_key == "roland":
                self.backend = backend_cls(
                    device_name=self._backend_opts.get("roland_device_name"),
                    init_mode=self._backend_opts.get("roland_init_mode", "gm"),
                )
            else:
                self.backend = backend_cls()
        except Exception as e:
            logger.error(f"💥 Backend '{backend_key}' konnte nicht initialisiert werden: {e}")

            if backend_key != "fluidsynth":
                try:
                    self.backend = FluidSynthBackend()
                    self._backend_name = "fluidsynth"
                    self._backend_opts = {}
                    logger.info("↩ Fallback auf 'fluidsynth' erfolgreich.")
                except Exception as e2:
                    logger.exception(f"💥 Fallback auf 'fluidsynth' scheiterte: {e2}")
                    raise

    def switch_backend(self, backend_name: str, **backend_opts: Any):
        try:
            try:
                if self.backend:
                    self.backend.cleanup()
            except Exception:
                pass

            self._build_backend(backend_name, **backend_opts)
            logger.info(f"🔄 Backend gewechselt auf: {self._backend_name} (opts={self._backend_opts})")
        except Exception as e:
            logger.error(f"💥 switch_backend() fehlgeschlagen: {e}")
            raise

    # ------------------------------------------------------------
    # API (einheitliche Oberfläche)
    # ------------------------------------------------------------

    @property
    def backend_name(self) -> str:
        return self._backend_name

    def get_output_label(self) -> str:
        try:
            if hasattr(self.backend, "get_output_label"):
                label = self.backend.get_output_label()
                if label:
                    return str(label)
        except Exception:
            pass

        try:
            if self._backend_name == "roland":
                dev = getattr(self.backend, "device_name", None) or self._backend_opts.get("roland_device_name")
                if dev:
                    return f"roland / {dev}"
        except Exception:
            pass

        return self._backend_name

    def play(self, midi_path: str):
        return self.backend.play(midi_path)

    def stop(self):
        return self.backend.stop()

    def is_playing(self) -> bool:
        try:
            return bool(self.backend.is_playing())
        except Exception:
            return False

    def set_volume(self, value: float):
        value = max(0.0, min(1.0, float(value)))
        if hasattr(self.backend, "set_volume"):
            try:
                self.backend.set_volume(value)
            except Exception as e:
                logger.warning(f"⚠️ Master-Volume konnte nicht gesetzt werden: {e}")
        else:
            logger.debug("ℹ Aktuelles Backend unterstützt kein Master-Volume (ignoriert).")

    def cleanup(self):
        try:
            if self.backend:
                self.backend.cleanup()
        except Exception:
            pass
