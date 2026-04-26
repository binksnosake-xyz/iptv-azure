# ui/main_window.py - Fenetre principale de l'application IPTV Azure
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget, QListWidgetItem, QLineEdit,
    QLabel, QPushButton, QFrame, QSplitter, QAction,
    QMenu, QSizePolicy, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon
from ui.player_widget import PlayerWidget
from ui.login_screen import LoginScreen
from utils.workers import LiveStreamsWorker, VODWorker, SeriesWorker
from utils.data_manager import FavoritesManager, SettingsManager
from config import CATEGORY_ALL, CATEGORY_FAVORITES

logger = logging.getLogger(__name__)


class ChannelItem(QListWidgetItem):
    """Item de liste representant un canal/film/serie."""
    def __init__(self, data):
        name = data.get("name") or data.get("title") or "Sans nom"
        super().__init__(name)
        self.channel_data = data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPTV Azure")
        self.setMinimumSize(1100, 680)
        self._client = None
        self._mode = None  # 'xtream' ou 'm3u'
        self._all_live = []
        self._all_vod = []
        self._all_series = []
        self._live_cats = []
        self._vod_cats = []
        self._series_cats = []
        self._current_cat = CATEGORY_ALL
        self._favorites_mgr = FavoritesManager()
        self._settings_mgr = SettingsManager()
        self._worker = None
        self._is_fullscreen = False
        self._init_ui()

    def _init_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Ecran de login
        self.login_screen = LoginScreen()
        self.login_screen.login_success.connect(self._on_login_success)
        self.stack.addWidget(self.login_screen)

        # Ecran principal
        self.main_widget = QWidget()
        self._build_main_ui()
        self.stack.addWidget(self.main_widget)

        self.stack.setCurrentIndex(0)

    def _build_main_ui(self):
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre superieure
        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet("background:#111122; border-bottom: 2px solid #007FFF;")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(16, 0, 16, 0)
        top_layout.setSpacing(12)

        lbl_logo = QLabel("IPTV Azure")
        lbl_logo.setStyleSheet("color:#007FFF; font-size:18px; font-weight:bold;")
        top_layout.addWidget(lbl_logo)
        top_layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher...")
        self.search_bar.setFixedWidth(260)
        self.search_bar.setFixedHeight(32)
        self.search_bar.textChanged.connect(self._on_search)
        top_layout.addWidget(self.search_bar)

        btn_back = QPushButton("Deconnexion")
        btn_back.setObjectName("btn_flat")
        btn_back.clicked.connect(self._go_to_login)
        top_layout.addWidget(btn_back)

        layout.addWidget(topbar)

        # Onglets principaux
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Onglet Live
        self.live_tab = self._make_content_tab()
        self.tabs.addTab(self.live_tab["widget"], "Live")

        # Onglet VOD
        self.vod_tab = self._make_content_tab()
        self.tabs.addTab(self.vod_tab["widget"], "Films (VOD)")

        # Onglet Series
        self.series_tab = self._make_content_tab()
        self.tabs.addTab(self.series_tab["widget"], "Series")

        # Onglet Favoris
        self.fav_tab = self._make_content_tab()
        self.tabs.addTab(self.fav_tab["widget"], "Favoris")

        # Player
        self.player = PlayerWidget()
        self.player.setMinimumHeight(340)
        self.player.fullscreen_requested.connect(self._on_fullscreen_requested)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.player)
        splitter.setSizes([340, 340])
        splitter.setStyleSheet("QSplitter::handle{background:#007FFF; height:2px;}")

        layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Pret")
        self.status_label.setStyleSheet(
            "color:#007FFF; font-size:11px; padding:3px 12px;"
            "background:#0d0d0d; border-top:1px solid #1a1a2e;"
        )
        layout.addWidget(self.status_label)

    def _make_content_tab(self):
        """Cree un onglet avec sidebar categories + liste principale."""
        widget = QWidget()
        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # Sidebar categories
        sidebar = QListWidget()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(
            "QListWidget{background:#0d0d0d; border-right:1px solid #1a1a2e;}"
            "QListWidget::item{padding:9px 14px; color:#aaaacc;}"
            "QListWidget::item:selected{background:#007FFF; color:#fff;}"
            "QListWidget::item:hover{background:#1a1a2e;}"
        )

        # Liste principale
        content_list = QListWidget()
        content_list.setStyleSheet(
            "QListWidget{background:#111111; border:none;}"
            "QListWidget::item{padding:10px 14px; border-bottom:1px solid #1a1a2e;}"
            "QListWidget::item:selected{background:#007FFF; color:#fff;}"
            "QListWidget::item:hover{background:#1a1a2e;}"
        )
        content_list.setContextMenuPolicy(Qt.CustomContextMenu)
        content_list.customContextMenuRequested.connect(
            lambda pos, lst=content_list: self._show_context_menu(pos, lst)
        )
        content_list.itemDoubleClicked.connect(self._on_item_double_clicked)

        h.addWidget(sidebar)
        h.addWidget(content_list)

        tab_data = {"widget": widget, "sidebar": sidebar, "list": content_list}
        sidebar.currentRowChanged.connect(
            lambda row, td=tab_data: self._on_category_selected(row, td)
        )
        return tab_data

    def _on_login_success(self, data, mode):
        try:
            self._mode = mode
            if mode == "xtream":
                self._client = data
                self._load_all_xtream()
            elif mode == "m3u":
                self._load_m3u_channels(data)
            self.stack.setCurrentIndex(1)
        except Exception as e:
            logger.error(f"Erreur on_login_success: {e}")
            self._show_error(str(e))

    def _load_all_xtream(self):
        self._set_status("Chargement Live...")
        self._worker = LiveStreamsWorker(self._client)
        self._worker.success.connect(self._on_live_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_live_loaded(self, categories, streams):
        try:
            self._live_cats = categories
            self._all_live = streams
            self._populate_tab(self.live_tab, categories, streams)
            self._set_status(f"{len(streams)} chaines Live chargees")
            self._load_vod()
        except Exception as e:
            logger.error(f"Erreur on_live_loaded: {e}")

    def _load_vod(self):
        self._set_status("Chargement VOD...")
        self._worker = VODWorker(self._client)
        self._worker.success.connect(self._on_vod_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_vod_loaded(self, categories, streams):
        try:
            self._vod_cats = categories
            self._all_vod = streams
            self._populate_tab(self.vod_tab, categories, streams)
            self._set_status(f"{len(streams)} films VOD charges")
            self._load_series()
        except Exception as e:
            logger.error(f"Erreur on_vod_loaded: {e}")

    def _load_series(self):
        self._set_status("Chargement Series...")
        self._worker = SeriesWorker(self._client)
        self._worker.success.connect(self._on_series_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_series_loaded(self, categories, series):
        try:
            self._series_cats = categories
            self._all_series = series
            self._populate_tab(self.series_tab, categories, series)
            self._set_status("Pret")
            self._refresh_favorites_tab()
        except Exception as e:
            logger.error(f"Erreur on_series_loaded: {e}")

    def _load_m3u_channels(self, channels):
        try:
            groups = sorted(set(c.get("group", "") for c in channels if c.get("group")))
            cats = [{"category_id": g, "category_name": g} for g in groups]
            self._all_live = channels
            self._live_cats = cats
            self._populate_tab(self.live_tab, cats, channels)
            self._set_status(f"{len(channels)} chaines M3U chargees")
            self._refresh_favorites_tab()
        except Exception as e:
            logger.error(f"Erreur load_m3u_channels: {e}")

    def _populate_tab(self, tab_data, categories, items):
        try:
            sidebar = tab_data["sidebar"]
            lst = tab_data["list"]
            sidebar.clear()
            lst.clear()
            sidebar.addItem(CATEGORY_ALL)
            for cat in categories:
                name = cat.get("category_name") or cat.get("name") or "?"
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, cat.get("category_id") or cat.get("id"))
                sidebar.addItem(item)
            sidebar.setCurrentRow(0)
            self._fill_list(lst, items)
        except Exception as e:
            logger.error(f"Erreur populate_tab: {e}")

    def _fill_list(self, lst, items):
        try:
            lst.clear()
            resume_mgr = self._get_resume_mgr()
            favs_mgr = self._favorites_mgr
            for ch in items:
                name = ch.get("name") or ch.get("title") or "Sans nom"
                stream_id = ch.get("stream_id")
                has_resume = False
                if resume_mgr and stream_id:
                    pos = resume_mgr.get_position(stream_id)
                    has_resume = pos > 5000
                fav = favs_mgr.is_favorite(ch)
                display = name
                if has_resume:
                    display = "\U0001F534 " + display
                if fav:
                    display = "\u2605 " + display
                item = ChannelItem(ch)
                item.setText(display)
                lst.addItem(item)
        except Exception as e:
            logger.error(f"Erreur fill_list: {e}")

    def _get_resume_mgr(self):
        try:
            from utils.data_manager import ResumeManager
            return ResumeManager()
        except Exception:
            return None

    def _on_category_selected(self, row, tab_data):
        try:
            sidebar = tab_data["sidebar"]
            lst = tab_data["list"]
            search = self.search_bar.text().strip().lower()
            if row == 0:
                pool = self._get_pool_for_tab(tab_data)
            else:
                item = sidebar.item(row)
                cat_id = item.data(Qt.UserRole) if item else None
                pool = self._get_pool_for_tab(tab_data)
                if cat_id:
                    pool = [c for c in pool if str(c.get("category_id", "")) == str(cat_id)
                            or str(c.get("group", "")) == str(cat_id)]
            if search:
                pool = [c for c in pool if search in (c.get("name") or c.get("title") or "").lower()]
            self._fill_list(lst, pool)
        except Exception as e:
            logger.error(f"Erreur on_category_selected: {e}")

    def _get_pool_for_tab(self, tab_data):
        if tab_data is self.live_tab:
            return self._all_live
        elif tab_data is self.vod_tab:
            return self._all_vod
        elif tab_data is self.series_tab:
            return self._all_series
        elif tab_data is self.fav_tab:
            return self._favorites_mgr.get_all()
        return []

    def _on_search(self, text):
        try:
            idx = self.tabs.currentIndex()
            tab_map = [self.live_tab, self.vod_tab, self.series_tab, self.fav_tab]
            if idx < len(tab_map):
                td = tab_map[idx]
                row = td["sidebar"].currentRow()
                self._on_category_selected(row, td)
        except Exception as e:
            logger.error(f"Erreur on_search: {e}")

    def _on_tab_changed(self, idx):
        try:
            if idx == 3:
                self._refresh_favorites_tab()
        except Exception as e:
            logger.error(f"Erreur on_tab_changed: {e}")

    def _refresh_favorites_tab(self):
        try:
            favs = self._favorites_mgr.get_all()
            self.fav_tab["sidebar"].clear()
            self.fav_tab["sidebar"].addItem(CATEGORY_ALL)
            self._fill_list(self.fav_tab["list"], favs)
        except Exception as e:
            logger.error(f"Erreur refresh_favorites_tab: {e}")

    def _show_context_menu(self, pos, lst):
        try:
            item = lst.itemAt(pos)
            if not item or not isinstance(item, ChannelItem):
                return
            ch = item.channel_data
            menu = QMenu(self)
            menu.setStyleSheet(
                "QMenu{background:#1e1e2e; color:#fff; border:1px solid #007FFF;}"
                "QMenu::item:selected{background:#007FFF;}"
            )
            is_fav = self._favorites_mgr.is_favorite(ch)
            if is_fav:
                action_fav = QAction("\u2605 Retirer des favoris", self)
            else:
                action_fav = QAction("\u2606 Ajouter aux favoris", self)
            action_fav.triggered.connect(lambda: self._toggle_favorite(ch))
            menu.addAction(action_fav)

            action_play = QAction("\u25B6 Lire", self)
            action_play.triggered.connect(lambda: self._play_channel(ch))
            menu.addAction(action_play)

            menu.exec_(lst.viewport().mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Erreur context menu: {e}")

    def _on_item_double_clicked(self, item):
        try:
            if isinstance(item, ChannelItem):
                self._play_channel(item.channel_data)
        except Exception as e:
            logger.error(f"Erreur double click: {e}")

    def _play_channel(self, ch):
        try:
            url = None
            stream_id = ch.get("stream_id")
            title = ch.get("name") or ch.get("title") or ""
            is_live = False

            if self._mode == "xtream" and self._client:
                if "stream_type" not in ch:
                    # Live
                    url = self._client.build_live_url(stream_id)
                    is_live = True
                elif ch.get("stream_type") == "movie":
                    ext = ch.get("container_extension", "mp4")
                    url = self._client.build_vod_url(stream_id, ext)
                elif ch.get("stream_type") == "live":
                    url = self._client.build_live_url(stream_id)
                    is_live = True
                else:
                    url = self._client.build_series_url(stream_id)
            else:
                url = ch.get("url", "")

            if not url:
                self._show_error("Impossible de construire l'URL du flux.")
                return

            self.player.play(url, stream_id=stream_id, title=title, is_live=is_live)
            self._set_status(f"Lecture : {title}")
        except Exception as e:
            logger.error(f"Erreur play_channel: {e}")
            self._show_error(str(e))

    def _toggle_favorite(self, ch):
        try:
            added = self._favorites_mgr.toggle(ch)
            msg = "Ajoute aux favoris" if added else "Retire des favoris"
            self._set_status(msg)
            self._refresh_favorites_tab()
        except Exception as e:
            logger.error(f"Erreur toggle_favorite: {e}")

    def _on_load_error(self, msg):
        self._set_status(f"Erreur : {msg}")
        logger.error(f"Erreur de chargement: {msg}")

    def _go_to_login(self):
        try:
            self.player.stop()
            self.stack.setCurrentIndex(0)
        except Exception as e:
            logger.error(f"Erreur go_to_login: {e}")

    def _on_fullscreen_requested(self, enter):
        try:
            if enter and not self._is_fullscreen:
                self._is_fullscreen = True
                self.showFullScreen()
            elif not enter and self._is_fullscreen:
                self._is_fullscreen = False
                self.showNormal()
        except Exception as e:
            logger.error(f"Erreur fullscreen: {e}")

    def _set_status(self, text):
        try:
            self.status_label.setText(text)
        except Exception:
            pass

    def _show_error(self, msg):
        try:
            QMessageBox.warning(self, "Erreur", msg)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self.player.cleanup()
        except Exception as e:
            logger.error(f"Erreur closeEvent: {e}")
        event.accept()
