# utils/data_manager.py - Gestion persistence JSON
import json
import os
import logging
from config import DATA_DIR, CACHE_DIR, FAVORITES_FILE, RESUME_FILE, PLAYLISTS_FILE, SETTINGS_FILE

logger = logging.getLogger(__name__)


def ensure_dirs():
    """Crée les répertoires de données si absents."""
    for d in [DATA_DIR, CACHE_DIR]:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            logger.error(f"Impossible de créer le dossier {d}: {e}")


def load_json(filepath, default=None):
    """Charge un fichier JSON, retourne default si absent ou corrompu."""
    if default is None:
        default = {}
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erreur lecture {filepath}: {e}")
    return default


def save_json(filepath, data):
    """Sauvegarde des données en JSON de façon atomique."""
    try:
        ensure_dirs()
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, filepath)
        return True
    except Exception as e:
        logger.error(f"Erreur écriture {filepath}: {e}")
        return False


class FavoritesManager:
    def __init__(self):
        self._data = load_json(FAVORITES_FILE, default=[])
        if not isinstance(self._data, list):
            self._data = []

    def _key(self, channel):
        return channel.get("stream_id") or channel.get("url", "")

    def is_favorite(self, channel):
        k = self._key(channel)
        return any(self._key(f) == k for f in self._data)

    def add(self, channel):
        if not self.is_favorite(channel):
            self._data.append(channel)
            self._save()

    def remove(self, channel):
        k = self._key(channel)
        self._data = [f for f in self._data if self._key(f) != k]
        self._save()

    def toggle(self, channel):
        if self.is_favorite(channel):
            self.remove(channel)
            return False
        else:
            self.add(channel)
            return True

    def get_all(self):
        return list(self._data)

    def _save(self):
        save_json(FAVORITES_FILE, self._data)


class ResumeManager:
    def __init__(self):
        self._data = load_json(RESUME_FILE, default={})
        if not isinstance(self._data, dict):
            self._data = {}

    def save_position(self, stream_id, position_ms):
        try:
            self._data[str(stream_id)] = int(position_ms)
            save_json(RESUME_FILE, self._data)
        except Exception as e:
            logger.error(f"Erreur save_position: {e}")

    def get_position(self, stream_id):
        try:
            return int(self._data.get(str(stream_id), 0))
        except Exception:
            return 0

    def clear(self, stream_id):
        try:
            self._data.pop(str(stream_id), None)
            save_json(RESUME_FILE, self._data)
        except Exception as e:
            logger.error(f"Erreur clear position: {e}")


class PlaylistsManager:
    def __init__(self):
        self._data = load_json(PLAYLISTS_FILE, default=[])
        if not isinstance(self._data, list):
            self._data = []

    def get_all(self):
        return list(self._data)

    def add(self, playlist):
        """playlist: dict avec name, type ('xtream'|'m3u'), et les champs requis."""
        self._data.append(playlist)
        self._save()

    def remove(self, index):
        try:
            self._data.pop(index)
            self._save()
        except IndexError:
            pass

    def update(self, index, playlist):
        try:
            self._data[index] = playlist
            self._save()
        except IndexError:
            pass

    def _save(self):
        save_json(PLAYLISTS_FILE, self._data)


class SettingsManager:
    DEFAULTS = {
        "volume": 80,
        "last_playlist_index": 0,
        "theme": "dark",
    }

    def __init__(self):
        self._data = load_json(SETTINGS_FILE, default=dict(self.DEFAULTS))

    def get(self, key, fallback=None):
        return self._data.get(key, self.DEFAULTS.get(key, fallback))

    def set(self, key, value):
        self._data[key] = value
        save_json(SETTINGS_FILE, self._data)
