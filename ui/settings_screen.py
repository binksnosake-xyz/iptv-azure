# ui/settings_screen.py - Ecran parametres style Smarters Pro
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.home_screen import LogoWidget
from utils.data_manager import SettingsManager


class SettingsTile(QFrame):
    """Tuile parametres style Smarters."""
    clicked = pyqtSignal()

    def __init__(self, icon, label, subtitle="", parent=None):
        super().__init__(parent)
        self._hovered = False
        self.setFixedSize(220, 160)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 20, 16, 16)

        lbl_icon = QLabel(icon)
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size:32px; background:transparent; color:rgba(255,255,255,0.85);")
        layout.addWidget(lbl_icon)

        lbl_text = QLabel(label)
        lbl_text.setAlignment(Qt.AlignCenter)
        lbl_text.setStyleSheet("font-size:13px; font-weight:bold; color:#ffffff; background:transparent;")
        layout.addWidget(lbl_text)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet("font-size:11px; color:#aaccff; background:transparent;")
            layout.addWidget(lbl_sub)

    def _apply_style(self, hovered):
        if hovered:
            self.setStyleSheet(
                "SettingsTile{background:rgba(0,80,200,0.5); border-radius:14px;"
                " border:2px solid #007FFF;}"
            )
        else:
            self.setStyleSheet(
                "SettingsTile{background:rgba(15,30,70,0.8); border-radius:14px;"
                " border:1px solid rgba(0,127,255,0.2);}"
            )

    def enterEvent(self, e):
        self._hovered = True
        self._apply_style(True)

    def leaveEvent(self, e):
        self._hovered = False
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()


class SettingsScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = SettingsManager()
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            background: qradialgradient(
                cx:0.5, cy:0.4, radius:0.9,
                fx:0.5, fy:0.4,
                stop:0 #0d1b3e,
                stop:0.6 #080818,
                stop:1 #030308
            );
        """)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(64)
        topbar.setStyleSheet("background:rgba(0,0,0,0.45); border-bottom:1px solid rgba(0,127,255,0.2);")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(24, 0, 24, 0)
        logo = LogoWidget(size=38)
        lbl_app = QLabel("IPTV Azure")
        lbl_app.setStyleSheet("color:#007FFF; font-size:17px; font-weight:bold; background:transparent;")
        tl.addWidget(logo)
        tl.addWidget(lbl_app)
        tl.addStretch()
        lbl_title = QLabel("PARAMETRES")
        lbl_title.setStyleSheet(
            "color:#ffffff; font-size:18px; font-weight:bold;"
            " background:transparent; letter-spacing:2px;"
        )
        tl.addWidget(lbl_title)
        tl.addStretch()
        btn_back = QPushButton("\u21A9  Retour")
        btn_back.setObjectName("btn_nav")
        btn_back.clicked.connect(self.back_requested.emit)
        tl.addWidget(btn_back)
        main.addWidget(topbar)

        # Tuiles
        center = QWidget()
        center.setStyleSheet("background:transparent;")
        cl = QHBoxLayout(center)
        cl.setAlignment(Qt.AlignCenter)
        cl.setSpacing(20)
        cl.setContentsMargins(40, 40, 40, 40)

        fmt = self._settings.get("stream_format", "ts")
        tile1 = SettingsTile("\u25B6\uFE0F", "Format Stream", f"Actuel : .{fmt}")
        tile1.clicked.connect(self._toggle_stream_format)
        cl.addWidget(tile1)
        self._tile_format = tile1

        vol = self._settings.get("volume", 80)
        tile2 = SettingsTile("\U0001F50A", "Volume par defaut", f"Actuel : {vol}%")
        cl.addWidget(tile2)

        tile3 = SettingsTile("\U0001F5D1", "Vider le cache", "Favoris & reprises")
        tile3.clicked.connect(self._clear_cache)
        cl.addWidget(tile3)

        main.addWidget(center, stretch=1)

        # Credits
        bottom = QFrame()
        bottom.setFixedHeight(38)
        bottom.setStyleSheet("background:rgba(0,0,0,0.5); border-top:1px solid rgba(0,127,255,0.15);")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(24, 0, 24, 0)
        bl.addStretch()
        lbl_c = QLabel("IPTV Azure v1.0.0 - Propulse par Python, PyQt5 & VLC")
        lbl_c.setObjectName("label_credits")
        bl.addWidget(lbl_c)
        bl.addStretch()
        main.addWidget(bottom)

    def _toggle_stream_format(self):
        try:
            fmt = self._settings.get("stream_format", "ts")
            new_fmt = "m3u8" if fmt == "ts" else "ts"
            self._settings.set("stream_format", new_fmt)
            self._tile_format.findChild(QLabel).setText(f"Actuel : .{new_fmt}")
        except Exception:
            pass

    def _clear_cache(self):
        try:
            import os
            from config import FAVORITES_FILE, RESUME_FILE
            for f in [FAVORITES_FILE, RESUME_FILE]:
                if os.path.exists(f):
                    os.remove(f)
        except Exception:
            pass
