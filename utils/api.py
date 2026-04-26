# utils/api.py - Client Xtream API et parseur M3U
import requests
import re
import os
import logging
from config import API_TIMEOUT, CACHE_DIR

logger = logging.getLogger(__name__)


class XtreamClient:
    def __init__(self, host, username, password):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.base_url = f"{self.host}/player_api.php?username={username}&password={password}"

    def _get(self, params=""):
        url = self.base_url + (f"&{params}" if params else "")
        try:
            resp = requests.get(url, timeout=API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise ConnectionError("Timeout: le serveur ne répond pas (>20s)")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Impossible de joindre le serveur IPTV")
        except requests.exceptions.HTTPError as e:
            raise ConnectionError(f"Erreur HTTP: {e}")
        except ValueError:
            raise ValueError("Réponse serveur invalide (JSON malformé)")

    def authenticate(self):
        """Retourne les infos du compte ou lève une exception."""
        data = self._get()
        if not isinstance(data, dict):
            raise ValueError("Réponse d'authentification invalide")
        user_info = data.get("user_info", {})
        if user_info.get("auth") == 0:
            raise PermissionError("Identifiants incorrects")
        return data

    def get_live_categories(self):
        return self._get("action=get_live_categories") or []

    def get_live_streams(self, category_id=None):
        params = "action=get_live_streams"
        if category_id:
            params += f"&category_id={category_id}"
        return self._get(params) or []

    def get_vod_categories(self):
        return self._get("action=get_vod_categories") or []

    def get_vod_streams(self, category_id=None):
        params = "action=get_vod_streams"
        if category_id:
            params += f"&category_id={category_id}"
        return self._get(params) or []

    def get_series_categories(self):
        return self._get("action=get_series_categories") or []

    def get_series(self, category_id=None):
        params = "action=get_series"
        if category_id:
            params += f"&category_id={category_id}"
        return self._get(params) or []

    def get_series_info(self, series_id):
        return self._get(f"action=get_series_info&series_id={series_id}") or {}

    def get_vod_info(self, vod_id):
        return self._get(f"action=get_vod_info&vod_id={vod_id}") or {}

    def build_live_url(self, stream_id, ext="ts"):
        return f"{self.host}/live/{self.username}/{self.password}/{stream_id}.{ext}"

    def build_vod_url(self, stream_id, ext="mp4"):
        return f"{self.host}/movie/{self.username}/{self.password}/{stream_id}.{ext}"

    def build_series_url(self, stream_id, ext="mkv"):
        return f"{self.host}/series/{self.username}/{self.password}/{stream_id}.{ext}"


class M3UParser:
    @staticmethod
    def parse_file(filepath):
        """Parse un fichier M3U local, retourne une liste de dicts."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return M3UParser.parse_content(content)
        except Exception as e:
            logger.error(f"Erreur lecture M3U {filepath}: {e}")
            return []

    @staticmethod
    def parse_url(url):
        """Télécharge et parse un M3U depuis une URL."""
        try:
            resp = requests.get(url, timeout=API_TIMEOUT)
            resp.raise_for_status()
            return M3UParser.parse_content(resp.text)
        except Exception as e:
            logger.error(f"Erreur téléchargement M3U {url}: {e}")
            return []

    @staticmethod
    def parse_content(content):
        channels = []
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                info = M3UParser._parse_extinf(line)
                if i + 1 < len(lines):
                    url = lines[i + 1].strip()
                    if url and not url.startswith("#"):
                        info["url"] = url
                        channels.append(info)
                i += 2
            else:
                i += 1
        return channels

    @staticmethod
    def _parse_extinf(line):
        info = {"name": "", "logo": "", "group": "", "stream_id": None}
        try:
            name_match = re.search(r',(.+)$', line)
            if name_match:
                info["name"] = name_match.group(1).strip()
            logo_match = re.search(r'tvg-logo="([^"]*)"', line)
            if logo_match:
                info["logo"] = logo_match.group(1)
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                info["group"] = group_match.group(1)
            id_match = re.search(r'tvg-id="([^"]*)"', line)
            if id_match:
                info["stream_id"] = id_match.group(1)
        except Exception as e:
            logger.warning(f"Erreur parse EXTINF: {e}")
        return info
