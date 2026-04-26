# config.py - Constantes globales de l'application
import os
import sys

APP_NAME = "IPTV Azure"
APP_VERSION = "1.0.0"
APP_AUTHOR = "IPTV Azure"

# Couleur principale
AZURE = "#007FFF"
BG_DARK = "#0D0D0D"
BG_CARD = "#1A1A2E"
BG_PANEL = "#111122"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#AAAACC"
ACCENT = "#007FFF"

# Chemins de données
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
RESUME_FILE = os.path.join(DATA_DIR, "resume.json")
PLAYLISTS_FILE = os.path.join(DATA_DIR, "playlists.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Timeouts
API_TIMEOUT = 20

# VLC
VLC_ARGS = [
    "--no-xlib",
    "--quiet",
    "--no-video-title-show",
    "--network-caching=3000",
    "--live-caching=3000",
    "--file-caching=3000",
]

# UI
CARD_WIDTH = 200
CARD_HEIGHT = 130
CONTROLS_HIDE_DELAY = 3000  # ms

# Catégories
CATEGORY_ALL = "Tout"
CATEGORY_FAVORITES = "Favoris"
