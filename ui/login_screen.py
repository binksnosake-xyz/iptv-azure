# ui/login_screen.py - Ecran de connexion/playlist selector
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QFrame, QComboBox, QFileDialog,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QLinearGradient, QColor, QBrush, QPainterPath
from utils.workers import AuthWorker, M3UWorker
from utils.data_manager import PlaylistsManager, SettingsManager


class LogoWidget(QWidget):
    """Logo moderne : carre arrondi degrade bleu + triangle play blanc."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 80, 80, 16, 16)
            gradient = QLinearGradient(0, 0, 80, 80)
            gradient.setColorAt(0, QColor("#007FFF"))
            gradient.setColorAt(1, QColor("#005FBF"))
            painter.fillPath(path, QBrush(gradient))
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(Qt.NoPen)
            from PyQt5.QtGui import QPolygon
            from PyQt5.QtCore import QPoint
            triangle = QPolygon([
                QPoint(28, 22),
                QPoint(28, 58),
                QPoint(60, 40),
            ])
            painter.drawPolygon(triangle)
        except Exception as e:
            pass


class LoginScreen(QWidget):
    login_success = pyqtSignal(object, str)  # (client_or_channels, type)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlists_mgr = PlaylistsManager()
        self.settings_mgr = SettingsManager()
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 40, 60, 40)

        # Logo + titre
        top = QHBoxLayout()
        top.setAlignment(Qt.AlignCenter)
        top.setSpacing(16)
        logo = LogoWidget()
        top.addWidget(logo)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("IPTV Azure")
        lbl_title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        lbl_title.setStyleSheet("color: #007FFF;")
        lbl_subtitle = QLabel("Lecteur IPTV Premium")
        lbl_subtitle.setStyleSheet("color: #aaaacc; font-size: 13px;")
        title_col.addWidget(lbl_title)
        title_col.addWidget(lbl_subtitle)
        top.addLayout(title_col)
        layout.addLayout(top)

        # Playlists sauvegardees
        saved_frame = QFrame()
        saved_frame.setStyleSheet("background:#111122; border-radius:8px; padding:4px;")
        saved_layout = QVBoxLayout(saved_frame)
        saved_layout.setContentsMargins(12, 10, 12, 10)
        lbl_saved = QLabel("Playlists sauvegardees")
        lbl_saved.setStyleSheet("color:#aaaacc; font-size:12px; font-weight:bold;")
        saved_layout.addWidget(lbl_saved)
        pl_row = QHBoxLayout()
        self.combo_playlists = QComboBox()
        self.combo_playlists.setMinimumWidth(260)
        pl_row.addWidget(self.combo_playlists)
        btn_load = QPushButton("Charger")
        btn_load.setObjectName("btn_flat")
        btn_load.clicked.connect(self._load_saved_playlist)
        pl_row.addWidget(btn_load)
        btn_del = QPushButton("Supprimer")
        btn_del.setObjectName("btn_flat")
        btn_del.setStyleSheet("color:#ff6666;")
        btn_del.clicked.connect(self._delete_saved_playlist)
        pl_row.addWidget(btn_del)
        saved_layout.addLayout(pl_row)
        layout.addWidget(saved_frame)
        self._refresh_playlists_combo()

        # Onglets Xtream / M3U
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(420)

        # --- Onglet Xtream ---
        xtream_tab = QWidget()
        xt_layout = QVBoxLayout(xtream_tab)
        xt_layout.setSpacing(12)
        xt_layout.setContentsMargins(16, 16, 16, 16)

        self.inp_host = QLineEdit()
        self.inp_host.setPlaceholderText("Serveur (ex: http://monserveur.com:8080)")
        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Nom d'utilisateur")
        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("Mot de passe")
        self.inp_pass.setEchoMode(QLineEdit.Password)
        self.inp_name_xt = QLineEdit()
        self.inp_name_xt.setPlaceholderText("Nom de la playlist (optionnel)")

        for w in [self.inp_host, self.inp_user, self.inp_pass, self.inp_name_xt]:
            xt_layout.addWidget(w)

        self.btn_connect = QPushButton("Se connecter")
        self.btn_connect.setMinimumHeight(40)
        self.btn_connect.clicked.connect(self._do_xtream_login)
        xt_layout.addWidget(self.btn_connect)

        self.tabs.addTab(xtream_tab, "Xtream API")

        # --- Onglet M3U ---
        m3u_tab = QWidget()
        m3u_layout = QVBoxLayout(m3u_tab)
        m3u_layout.setSpacing(12)
        m3u_layout.setContentsMargins(16, 16, 16, 16)

        self.inp_m3u_url = QLineEdit()
        self.inp_m3u_url.setPlaceholderText("URL M3U (http://...) ou chemin local")
        m3u_layout.addWidget(self.inp_m3u_url)

        btn_browse = QPushButton("Parcourir fichier local")
        btn_browse.setObjectName("btn_flat")
        btn_browse.clicked.connect(self._browse_m3u)
        m3u_layout.addWidget(btn_browse)

        self.inp_name_m3u = QLineEdit()
        self.inp_name_m3u.setPlaceholderText("Nom de la playlist (optionnel)")
        m3u_layout.addWidget(self.inp_name_m3u)

        self.btn_load_m3u = QPushButton("Charger M3U")
        self.btn_load_m3u.setMinimumHeight(40)
        self.btn_load_m3u.clicked.connect(self._do_m3u_load)
        m3u_layout.addWidget(self.btn_load_m3u)

        self.tabs.addTab(m3u_tab, "M3U Playlist")

        layout.addWidget(self.tabs)

        # Status
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #007FFF; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        # Credits
        lbl_credits = QLabel("IPTV Azure v1.0.0 — Propulse par Python, PyQt5 & VLC")
        lbl_credits.setObjectName("label_credits")
        lbl_credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_credits)

    def _refresh_playlists_combo(self):
        self.combo_playlists.clear()
        playlists = self.playlists_mgr.get_all()
        if not playlists:
            self.combo_playlists.addItem("Aucune playlist sauvegardee")
        else:
            for pl in playlists:
                self.combo_playlists.addItem(pl.get("name", "Sans nom"))

    def _load_saved_playlist(self):
        playlists = self.playlists_mgr.get_all()
        idx = self.combo_playlists.currentIndex()
        if not playlists or idx < 0 or idx >= len(playlists):
            return
        pl = playlists[idx]
        if pl.get("type") == "xtream":
            self.tabs.setCurrentIndex(0)
            self.inp_host.setText(pl.get("host", ""))
            self.inp_user.setText(pl.get("username", ""))
            self.inp_pass.setText(pl.get("password", ""))
            self.inp_name_xt.setText(pl.get("name", ""))
        elif pl.get("type") == "m3u":
            self.tabs.setCurrentIndex(1)
            self.inp_m3u_url.setText(pl.get("url", ""))
            self.inp_name_m3u.setText(pl.get("name", ""))

    def _delete_saved_playlist(self):
        playlists = self.playlists_mgr.get_all()
        idx = self.combo_playlists.currentIndex()
        if not playlists or idx < 0 or idx >= len(playlists):
            return
        self.playlists_mgr.remove(idx)
        self._refresh_playlists_combo()

    def _browse_m3u(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Ouvrir une playlist M3U", "",
                "Playlists M3U (*.m3u *.m3u8);;Tous les fichiers (*)"
            )
            if path:
                self.inp_m3u_url.setText(path)
        except Exception as e:
            self.lbl_status.setText(f"Erreur: {e}")

    def _do_xtream_login(self):
        host = self.inp_host.text().strip()
        username = self.inp_user.text().strip()
        password = self.inp_pass.text().strip()
        if not host or not username or not password:
            self.lbl_status.setText("Veuillez remplir tous les champs.")
            return
        self.btn_connect.setEnabled(False)
        self.lbl_status.setText("Connexion en cours...")
        self._worker = AuthWorker(host, username, password)
        self._worker.success.connect(self._on_xtream_success)
        self._worker.error.connect(self._on_login_error)
        self._worker.start()

    def _on_xtream_success(self, data):
        try:
            from utils.api import XtreamClient
            host = self.inp_host.text().strip()
            username = self.inp_user.text().strip()
            password = self.inp_pass.text().strip()
            name = self.inp_name_xt.text().strip() or host
            client = XtreamClient(host, username, password)
            self._save_playlist_xtream(host, username, password, name)
            self.lbl_status.setText("Connexion reussie !")
            self.btn_connect.setEnabled(True)
            self.login_success.emit(client, "xtream")
        except Exception as e:
            self._on_login_error(str(e))

    def _on_login_error(self, msg):
        self.lbl_status.setText(f"Erreur : {msg}")
        self.btn_connect.setEnabled(True)
        self.btn_load_m3u.setEnabled(True)

    def _do_m3u_load(self):
        source = self.inp_m3u_url.text().strip()
        if not source:
            self.lbl_status.setText("Veuillez entrer une URL ou un chemin M3U.")
            return
        self.btn_load_m3u.setEnabled(False)
        self.lbl_status.setText("Chargement M3U...")
        is_url = source.startswith("http://") or source.startswith("https://")
        self._worker = M3UWorker(source, is_url=is_url)
        self._worker.success.connect(self._on_m3u_success)
        self._worker.error.connect(self._on_login_error)
        self._worker.start()

    def _on_m3u_success(self, channels):
        try:
            source = self.inp_m3u_url.text().strip()
            name = self.inp_name_m3u.text().strip() or source
            self._save_playlist_m3u(source, name)
            self.lbl_status.setText(f"{len(channels)} chaines chargees.")
            self.btn_load_m3u.setEnabled(True)
            self.login_success.emit(channels, "m3u")
        except Exception as e:
            self._on_login_error(str(e))

    def _save_playlist_xtream(self, host, username, password, name):
        try:
            playlists = self.playlists_mgr.get_all()
            for pl in playlists:
                if pl.get("type") == "xtream" and pl.get("host") == host and pl.get("username") == username:
                    return
            self.playlists_mgr.add({
                "type": "xtream", "host": host,
                "username": username, "password": password, "name": name
            })
            self._refresh_playlists_combo()
        except Exception as e:
            pass

    def _save_playlist_m3u(self, url, name):
        try:
            playlists = self.playlists_mgr.get_all()
            for pl in playlists:
                if pl.get("type") == "m3u" and pl.get("url") == url:
                    return
            self.playlists_mgr.add({"type": "m3u", "url": url, "name": name})
            self._refresh_playlists_combo()
        except Exception as e:
            pass
