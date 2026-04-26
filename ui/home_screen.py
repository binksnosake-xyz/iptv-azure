# ui/home_screen.py - Ecran d'accueil style Smarters Pro
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGridLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QBrush, QPainterPath, QFont, QPolygon
from PyQt5.QtCore import QPoint


class LogoWidget(QWidget):
    """Logo IPTV Azure : carre arrondi degrade bleu + triangle play."""
    def __init__(self, size=52, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            r = self._size * 0.22
            path.addRoundedRect(0, 0, self._size, self._size, r, r)
            grad = QLinearGradient(0, 0, self._size, self._size)
            grad.setColorAt(0, QColor("#007FFF"))
            grad.setColorAt(1, QColor("#0044BB"))
            p.fillPath(path, QBrush(grad))
            p.setBrush(QColor("#ffffff"))
            p.setPen(Qt.NoPen)
            s = self._size
            tri = QPolygon([
                QPoint(int(s * 0.34), int(s * 0.26)),
                QPoint(int(s * 0.34), int(s * 0.74)),
                QPoint(int(s * 0.76), int(s * 0.50)),
            ])
            p.drawPolygon(tri)
        except Exception:
            pass


class HomeTileButton(QWidget):
    """Tuile cliquable style Smarters Pro avec degrade, icone et label."""
    clicked = pyqtSignal()

    # Couleurs des tuiles (degrade, comme Smarters mais en bleu)
    TILE_COLORS = {
        "live":     ("#0055CC", "#007FFF"),
        "movies":   ("#005599", "#00AAFF"),
        "series":   ("#003388", "#5599FF"),
        "favourites": ("#003366", "#0077CC"),
        "settings": ("#1a2a4a", "#2a4a7a"),
    }

    def __init__(self, key, icon_text, label, parent=None):
        super().__init__(parent)
        self._key = key
        self._hovered = False
        colors = self.TILE_COLORS.get(key, ("#003399", "#007FFF"))
        self._c1 = QColor(colors[0])
        self._c2 = QColor(colors[1])
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(180, 130)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 20, 16, 16)

        lbl_icon = QLabel(icon_text)
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 38px; background: transparent; color: rgba(255,255,255,0.9);")
        layout.addWidget(lbl_icon)

        lbl_text = QLabel(label.upper())
        lbl_text.setAlignment(Qt.AlignCenter)
        lbl_text.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #ffffff;"
            "background: transparent; letter-spacing: 1px;"
        )
        layout.addWidget(lbl_text)

    def paintEvent(self, event):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
            grad = QLinearGradient(0, 0, self.width(), self.height())
            c1 = QColor(self._c1)
            c2 = QColor(self._c2)
            if self._hovered:
                c1 = c1.lighter(130)
                c2 = c2.lighter(130)
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            p.fillPath(path, QBrush(grad))
            if self._hovered:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 25))
                p.drawPath(path)
        except Exception:
            pass

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()


class HomeScreen(QWidget):
    """Ecran d'accueil avec grille de tuiles style Smarters Pro."""
    navigate = pyqtSignal(str)  # 'live', 'movies', 'series', 'favourites', 'settings'
    logout_requested = pyqtSignal()

    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self._user_info = user_info or {}
        self._init_ui()

    def _init_ui(self):
        # Fond degrade radial
        self.setAutoFillBackground(False)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container avec fond
        container = QWidget()
        container.setStyleSheet("""
            background: qradialgradient(
                cx:0.5, cy:0.4, radius:0.9,
                fx:0.5, fy:0.4,
                stop:0 #0d1b3e,
                stop:0.6 #080818,
                stop:1 #030308
            );
        """)
        main_layout.addWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Topbar
        topbar = self._make_topbar()
        layout.addWidget(topbar)

        # Grille de tuiles centree
        center = QWidget()
        center.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setContentsMargins(60, 30, 60, 30)
        center_layout.setSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(16)

        # Tuile Live TV (grande, occupe 2 lignes a gauche)
        live_tile = HomeTileButton("live", "\U0001F4FA", "Live TV")
        live_tile.setMinimumSize(260, 280)
        live_tile.clicked.connect(lambda: self.navigate.emit("live"))
        grid.addWidget(live_tile, 0, 0, 2, 1)

        # Movies
        movies_tile = HomeTileButton("movies", "\U0001F3AC", "Movies")
        movies_tile.setMinimumSize(200, 130)
        movies_tile.clicked.connect(lambda: self.navigate.emit("movies"))
        grid.addWidget(movies_tile, 0, 1, 1, 1)

        # Series
        series_tile = HomeTileButton("series", "\U0001F3AC", "Series")
        series_tile.setMinimumSize(200, 130)
        series_tile.clicked.connect(lambda: self.navigate.emit("series"))
        grid.addWidget(series_tile, 0, 2, 1, 1)

        # Favourites
        fav_tile = HomeTileButton("favourites", "\u2605", "Favourites")
        fav_tile.setMinimumSize(200, 130)
        fav_tile.clicked.connect(lambda: self.navigate.emit("favourites"))
        grid.addWidget(fav_tile, 1, 1, 1, 1)

        # Settings
        settings_tile = HomeTileButton("settings", "\u2699", "Settings")
        settings_tile.setMinimumSize(200, 130)
        settings_tile.clicked.connect(lambda: self.navigate.emit("settings"))
        grid.addWidget(settings_tile, 1, 2, 1, 1)

        center_layout.addLayout(grid)
        layout.addWidget(center, stretch=1)

        # Barre inferieure
        bottom = self._make_bottom_bar()
        layout.addWidget(bottom)

    def _make_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(64)
        bar.setStyleSheet("background: rgba(0,0,0,0.45); border-bottom: 1px solid rgba(0,127,255,0.2);")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0)
        bl.setSpacing(12)

        logo = LogoWidget(size=42)
        lbl_name = QLabel("IPTV Azure")
        lbl_name.setStyleSheet("color:#007FFF; font-size:20px; font-weight:bold; background:transparent;")
        bl.addWidget(logo)
        bl.addWidget(lbl_name)
        bl.addStretch()

        # Infos compte
        user_info = self._user_info
        username = ""
        try:
            ui = user_info.get("user_info", {})
            username = ui.get("username", "")
        except Exception:
            pass

        if username:
            lbl_user = QLabel(f"Connecte : {username}")
            lbl_user.setStyleSheet("color:#aaccff; font-size:12px; background:transparent;")
            bl.addWidget(lbl_user)

        btn_back = QPushButton("\u21A9  Deconnexion")
        btn_back.setObjectName("btn_nav")
        btn_back.clicked.connect(self.logout_requested.emit)
        bl.addWidget(btn_back)
        return bar

    def _make_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(38)
        bar.setStyleSheet("background: rgba(0,0,0,0.5); border-top: 1px solid rgba(0,127,255,0.15);")
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(24, 0, 24, 0)

        # Expiration
        exp = ""
        try:
            ui = self._user_info.get("user_info", {})
            exp_ts = ui.get("exp_date", "")
            if exp_ts:
                import datetime
                try:
                    dt = datetime.datetime.fromtimestamp(int(exp_ts))
                    exp = f"Expiration : {dt.strftime('%d %b %Y')}"
                except Exception:
                    exp = f"Expiration : {exp_ts}"
        except Exception:
            pass

        lbl_exp = QLabel(exp)
        lbl_exp.setStyleSheet("color:#aaccff; font-size:11px; background:transparent;")
        bl.addWidget(lbl_exp)
        bl.addStretch()

        lbl_credits = QLabel("IPTV Azure v1.0.0")
        lbl_credits.setObjectName("label_credits")
        bl.addWidget(lbl_credits)
        return bar

    def update_user_info(self, user_info):
        self._user_info = user_info
