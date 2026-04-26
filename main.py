# main.py - Point d'entree IPTV Azure
import sys
import os
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

# Ajout du chemin racine au PYTHONPATH si necessaire
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Chemin VLC pour PyInstaller (inclusion des DLL)
if getattr(sys, 'frozen', False):
    vlc_path = os.path.join(app_dir, "vlc")
    if os.path.isdir(vlc_path):
        os.environ["PYTHON_VLC_LIB_PATH"] = os.path.join(vlc_path, "libvlc.dll")
        os.environ["PYTHON_VLC_MODULE_PATH"] = vlc_path
        os.add_dll_directory(vlc_path)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.styles import STYLESHEET
from ui.main_window import MainWindow
from utils.data_manager import ensure_dirs


def main():
    ensure_dirs()
    app = QApplication(sys.argv)
    app.setApplicationName("IPTV Azure")
    app.setApplicationVersion("1.0.0")
    app.setStyleSheet(STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
