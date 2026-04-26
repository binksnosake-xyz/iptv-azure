# utils/api.py - Client Xtream API robuste + parseur M3U
import requests
import re
import logging
from config import API_TIMEOUT

logger = logging.getLogger(__name__)

# Ports a tester automatiquement si aucun port dans l'URL
FALLBACK_PORTS = [80, 8080, 8000, 25461, 2082]


def normalize_host(host):
    """
    Normalise l'URL du serveur :
    - Supprime les espaces
    - Ajoute http:// si absent
    - Supprime le slash final
    - NE supprime PAS le www. (fait partie du domaine)
    Exemples :
      'kdfgh.com:8080'        -> 'http://kdfgh.com:8080'
      'http://kdfgh.com:8080' -> 'http://kdfgh.com:8080'
      'http://www.r56mail.com/' -> 'http://www.r56mail.com'
      'www.r56mail.com'       -> 'http://www.r56mail.com'
    """
    host = host.strip()
    if not host:
        return host
    # Ajoute le schema si absent
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    # Supprime le slash final
    host = host.rstrip("/")
    return host


def has_explicit_port(host):
    """
    Detecte si l'URL contient deja un port explicite.
    Exemples :
      http://kdfgh.com:8080      -> True
      http://www.r56mail.com     -> False
      https://serveur.com:443    -> True
    """
    try:
        # Retire le schema http:// ou https://
        without_schema = re.sub(r'^https?://', '', host)
        # Prend uniquement le host:port (avant le premier /)
        host_part = without_schema.split("/")[0]
        # Verifie si il y a un ':' dans la partie host (signe d'un port)
        # Attention : IPv6 contient des ':' aussi, on ignore ce cas rare
        return bool(re.search(r':\d+$', host_part))
    except Exception:
        return False


def test_auth_url(host, username, password):
    """
    Tente une authentification sur un host donne.
    Retourne (data_dict, None) si succes, (None, error_str) si echec.
    """
    url = f"{host}/player_api.php?username={username}&password={password}"
    logger.debug(f"Test auth sur : {url}")
    try:
        resp = requests.get(url, timeout=API_TIMEOUT)
        # Certains serveurs retournent 403/404 meme avec de bons identifiants
        # On tente quand meme de parser le JSON
        try:
            data = resp.json()
        except ValueError:
            return None, f"Reponse non-JSON (status={resp.status_code}) sur {host}"

        if not isinstance(data, dict):
            return None, f"JSON invalide (pas un objet) sur {host}"

        user_info = data.get("user_info", {})
        # Accepte auth=1 (int), auth='1' (string), ou absence du champ
        auth_val = user_info.get("auth", 1)
        if str(auth_val) == "0":
            return None, "Identifiants incorrects (auth=0)"

        return data, None

    except requests.exceptions.Timeout:
        return None, f"Timeout (>{API_TIMEOUT}s) sur {host}"
    except requests.exceptions.ConnectionError as e:
        return None, f"Connexion refusee sur {host} : {e}"
    except requests.exceptions.HTTPError as e:
        return None, f"Erreur HTTP {e} sur {host}"
    except Exception as e:
        return None, f"Erreur inattendue sur {host} : {e}"


class XtreamClient:
    def __init__(self, host, username, password):
        self.host = normalize_host(host)
        self.username = username
        self.password = password
        self._update_base_url()

    def _update_base_url(self):
        self.base_url = (
            f"{self.host}/player_api.php"
            f"?username={self.username}&password={self.password}"
        )

    def _get(self, params=""):
        url = self.base_url + (f"&{params}" if params else "")
        try:
            resp = requests.get(url, timeout=API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise ConnectionError("Timeout : le serveur ne repond pas (>20s)")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Impossible de joindre le serveur IPTV")
        except requests.exceptions.HTTPError as e:
            raise ConnectionError(f"Erreur HTTP : {e}")
        except ValueError:
            raise ValueError("Reponse serveur invalide (JSON malforme)")
        except Exception as e:
            raise ConnectionError(f"Erreur inattendue : {e}")

    def authenticate(self):
        """
        Authentification robuste :
        1. Teste l'URL telle quelle
        2. Si echec ET pas de port -> teste les ports alternatifs
        3. Remonte une erreur claire si tout echoue

        Compatible avec :
        - KDMAX  : http://kdfgh.com:8080  (port explicite)
        - KING365: http://www.r56mail.com (sans port, www.)
        - Shooters et autres sans port
        """
        # Tentative directe
        data, err = test_auth_url(self.host, self.username, self.password)
        if data:
            logger.info(f"[AUTH] Connexion reussie sur {self.host}")
            return data

        logger.warning(f"[AUTH] Echec direct sur {self.host} : {err}")

        # Si pas de port explicite, on teste les fallback
        if not has_explicit_port(self.host):
            for port in FALLBACK_PORTS:
                test_host = f"{self.host}:{port}"
                data, err2 = test_auth_url(test_host, self.username, self.password)
                if data:
                    logger.info(f"[AUTH] Connexion reussie sur {test_host} (fallback port {port})")
                    self.host = test_host
                    self._update_base_url()
                    return data
                logger.warning(f"[AUTH] Echec port {port} : {err2}")

        # Tout a echoue
        raise ConnectionError(
            f"Connexion impossible au serveur.\n"
            f"Verifie l'URL, le port, le nom d'utilisateur et le mot de passe.\n"
            f"URL testee : {self.host}\n"
            f"Derniere erreur : {err}"
        )

    def get_live_categories(self):
        try:
            return self._get("action=get_live_categories") or []
        except Exception as e:
            logger.error(f"Erreur get_live_categories : {e}")
            return []

    def get_live_streams(self, category_id=None):
        try:
            params = "action=get_live_streams"
            if category_id:
                params += f"&category_id={category_id}"
            return self._get(params) or []
        except Exception as e:
            logger.error(f"Erreur get_live_streams : {e}")
            return []

    def get_vod_categories(self):
        try:
            return self._get("action=get_vod_categories") or []
        except Exception as e:
            logger.error(f"Erreur get_vod_categories : {e}")
            return []

    def get_vod_streams(self, category_id=None):
        try:
            params = "action=get_vod_streams"
            if category_id:
                params += f"&category_id={category_id}"
            return self._get(params) or []
        except Exception as e:
            logger.error(f"Erreur get_vod_streams : {e}")
            return []

    def get_series_categories(self):
        try:
            return self._get("action=get_series_categories") or []
        except Exception as e:
            logger.error(f"Erreur get_series_categories : {e}")
            return []

    def get_series(self, category_id=None):
        try:
            params = "action=get_series"
            if category_id:
                params += f"&category_id={category_id}"
            return self._get(params) or []
        except Exception as e:
            logger.error(f"Erreur get_series : {e}")
            return []

    def get_series_info(self, series_id):
        try:
            return self._get(f"action=get_series_info&series_id={series_id}") or {}
        except Exception as e:
            logger.error(f"Erreur get_series_info : {e}")
            return {}

    def get_vod_info(self, vod_id):
        try:
            return self._get(f"action=get_vod_info&vod_id={vod_id}") or {}
        except Exception as e:
            logger.error(f"Erreur get_vod_info : {e}")
            return {}

    def build_live_url(self, stream_id, ext="ts"):
        return f"{self.host}/live/{self.username}/{self.password}/{stream_id}.{ext}"

    def build_vod_url(self, stream_id, ext="mp4"):
        return f"{self.host}/movie/{self.username}/{self.password}/{stream_id}.{ext}"

    def build_series_url(self, stream_id, ext="mkv"):
        return f"{self.host}/series/{self.username}/{self.password}/{stream_id}.{ext}"


class M3UParser:
    @staticmethod
    def parse_file(filepath):
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return M3UParser.parse_content(content)
        except Exception as e:
            logger.error(f"Erreur lecture M3U {filepath} : {e}")
            return []

    @staticmethod
    def parse_url(url):
        try:
            resp = requests.get(url, timeout=API_TIMEOUT)
            resp.raise_for_status()
            return M3UParser.parse_content(resp.text)
        except Exception as e:
            logger.error(f"Erreur telechargement M3U {url} : {e}")
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
            logger.warning(f"Erreur parse EXTINF : {e}")
        return info
