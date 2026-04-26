# ui/content_screen.py - Ecran contenu avec posters carrousel style Smarters
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QAction, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QThread
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QBrush, QPainterPath
from ui.home_screen import LogoWidget

logger = logging.getLogger(__name__)


class PosterCard(QFrame):
    """Carte poster cliquable (style Netflix/Smarters)."""
    clicked = pyqtSignal(object)
    context_menu_requested = pyqtSignal(object, object)  # channel_data, global_pos

    def __init__(self, channel_data, width=140, height=190, parent=None):
        super().__init__(parent)
        self._data = channel_data
        self._hovered = False
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "PosterCard{background:#0d1530; border-radius:10px;"
            " border:1px solid rgba(0,127,255,0.15);}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Image / placeholder
        self.lbl_poster = QLabel()
        self.lbl_poster.setFixedSize(width, height - 36)
        self.lbl_poster.setAlignment(Qt.AlignCenter)
        self.lbl_poster.setStyleSheet(
            "background:#0a1020; border-radius:10px 10px 0 0;"
        )
        # Placeholder icone
        self.lbl_poster.setText("\U0001F4F9")
        self.lbl_poster.setStyleSheet(
            "background:#0a1020; border-radius:10px 10px 0 0;"
            " font-size:32px; color:#1a3a6a;"
        )
        layout.addWidget(self.lbl_poster)

        # Nom
        name = channel_data.get("name") or channel_data.get("title") or ""
        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setWordWrap(False)
        lbl_name.setFixedHeight(36)
        lbl_name.setStyleSheet(
            "font-size:11px; color:#ccddff; background:#0d1530;"
            " border-radius:0 0 10px 10px; padding:0 6px;"
        )
        # Tronquer le nom si trop long
        fm = lbl_name.fontMetrics()
        elided = fm.elidedText(name, Qt.ElideRight, width - 12)
        lbl_name.setText(elided)
        layout.addWidget(lbl_name)

    def enterEvent(self, e):
        self._hovered = True
        self.setStyleSheet(
            "PosterCard{background:#152040; border-radius:10px;"
            " border:2px solid #007FFF;}"
        )

    def leaveEvent(self, e):
        self._hovered = False
        self.setStyleSheet(
            "PosterCard{background:#0d1530; border-radius:10px;"
            " border:1px solid rgba(0,127,255,0.15);}"
        )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._data)
        elif e.button() == Qt.RightButton:
            self.context_menu_requested.emit(self._data, e.globalPos())

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._data)


class LiveChannelRow(QFrame):
    """Ligne chaine Live style Smarters - icone + nom."""
    clicked = pyqtSignal(object)
    context_menu_requested = pyqtSignal(object, object)

    def __init__(self, channel_data, is_fav=False, has_resume=False, parent=None):
        super().__init__(parent)
        self._data = channel_data
        self._hovered = False
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(12)

        lbl_icon = QLabel("\U0001F4FA")
        lbl_icon.setStyleSheet("font-size:18px; color:#4488cc; background:transparent;")
        lbl_icon.setFixedWidth(28)
        layout.addWidget(lbl_icon)

        name = channel_data.get("name") or channel_data.get("title") or "?"
        if has_resume:
            name = "\U0001F534 " + name
        if is_fav:
            name = "\u2605 " + name
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size:13px; color:#e0eeff; background:transparent;")
        layout.addWidget(lbl_name, stretch=1)

    def _apply_style(self, hovered):
        if hovered:
            self.setStyleSheet(
                "LiveChannelRow{background:rgba(0,80,180,0.4);"
                " border-radius:8px; border:1px solid rgba(0,127,255,0.4);}"
            )
        else:
            self.setStyleSheet(
                "LiveChannelRow{background:rgba(10,25,65,0.7);"
                " border-radius:8px; border:1px solid rgba(0,127,255,0.08);}"
            )

    def enterEvent(self, e):
        self._hovered = True
        self._apply_style(True)

    def leaveEvent(self, e):
        self._hovered = False
        self._apply_style(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._data)
        elif e.button() == Qt.RightButton:
            self.context_menu_requested.emit(self._data, e.globalPos())

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._data)


class CarouselSection(QWidget):
    """Section horizontale scrollable (Top Added, Top Rated, etc.)."""
    item_clicked = pyqtSignal(object)
    item_context = pyqtSignal(object, object)

    def __init__(self, title, items, card_w=140, card_h=190, parent=None):
        super().__init__(parent)
        self._items = items
        self._card_w = card_w
        self._card_h = card_h
        self.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header section
        header = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setObjectName("label_section")
        header.addWidget(lbl_title)
        header.addStretch()
        btn_all = QPushButton("Voir tout")
        btn_all.setObjectName("btn_flat")
        btn_all.setStyleSheet("color:#007FFF; font-size:12px;")
        header.addWidget(btn_all)
        layout.addLayout(header)

        # Separateur
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background:#007FFF; border-radius:1px;")
        layout.addWidget(sep)

        # Scroll horizontal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(card_h + 16)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 6, 0, 6)
        inner_layout.setSpacing(10)

        for ch in items:
            card = PosterCard(ch, card_w, card_h)
            card.clicked.connect(self.item_clicked.emit)
            card.context_menu_requested.connect(self.item_context.emit)
            inner_layout.addWidget(card)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)


class LiveSection(QWidget):
    """Section liste Live style Smarters - grille de lignes."""
    item_clicked = pyqtSignal(object)
    item_context = pyqtSignal(object, object)

    def __init__(self, title, channels, favorites_mgr, resume_mgr, parent=None):
        super().__init__(parent)
        self._channels = channels
        self.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(8)
        row = 0
        col = 0
        for ch in channels:
            is_fav = False
            has_resume = False
            try:
                is_fav = favorites_mgr.is_favorite(ch)
            except Exception:
                pass
            try:
                sid = ch.get("stream_id")
                if sid:
                    has_resume = resume_mgr.get_position(sid) > 5000
            except Exception:
                pass
            row_widget = LiveChannelRow(ch, is_fav=is_fav, has_resume=has_resume)
            row_widget.clicked.connect(self.item_clicked.emit)
            row_widget.context_menu_requested.connect(self.item_context.emit)
            grid.addWidget(row_widget, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        layout.addLayout(grid)


class ContentScreen(QWidget):
    """
    Ecran de contenu principal.
    Mode 'live' : grille 2 colonnes style Smarters.
    Mode 'vod'/'series' : carrousels de posters style Netflix.
    """
    play_requested = pyqtSignal(object)   # channel_data
    back_requested = pyqtSignal()
    favorite_toggled = pyqtSignal(object)

    def __init__(self, title, mode, items, categories, favorites_mgr, resume_mgr, parent=None):
        super().__init__(parent)
        self._title = title
        self._mode = mode  # 'live', 'vod', 'series'
        self._all_items = items
        self._displayed_items = items
        self._categories = categories
        self._favorites_mgr = favorites_mgr
        self._resume_mgr = resume_mgr
        self._current_cat_id = None
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
        topbar = self._make_topbar()
        main.addWidget(topbar)

        # Zone scrollable principale
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background:transparent;")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(28, 16, 28, 28)
        self._content_layout.setSpacing(28)

        self._scroll.setWidget(self._content_widget)
        main.addWidget(self._scroll, stretch=1)

        self._render_content(self._all_items)

    def _make_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(64)
        bar.setStyleSheet("background:rgba(0,0,0,0.45); border-bottom:1px solid rgba(0,127,255,0.2);")
        tl = QHBoxLayout(bar)
        tl.setContentsMargins(24, 0, 24, 0)
        tl.setSpacing(12)

        logo = LogoWidget(size=38)
        lbl_app = QLabel("IPTV Azure")
        lbl_app.setStyleSheet("color:#007FFF; font-size:17px; font-weight:bold; background:transparent;")
        tl.addWidget(logo)
        tl.addWidget(lbl_app)
        tl.addStretch()

        lbl_title = QLabel(self._title.upper())
        lbl_title.setStyleSheet(
            "color:#ffffff; font-size:18px; font-weight:bold;"
            " background:transparent; letter-spacing:2px;"
        )
        tl.addWidget(lbl_title)
        tl.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.setFixedWidth(220)
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._on_search)
        tl.addWidget(self.search_input)

        btn_cats = QPushButton("\u2630  Categories")
        btn_cats.setObjectName("btn_nav")
        btn_cats.clicked.connect(self.back_requested.emit)
        tl.addWidget(btn_cats)

        return bar

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_content(self, items):
        self._clear_content()
        if not items:
            lbl_empty = QLabel("Aucun contenu disponible.")
            lbl_empty.setStyleSheet("color:#555577; font-size:14px; background:transparent;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self._content_layout.addWidget(lbl_empty)
            self._content_layout.addStretch()
            return

        if self._mode == "live":
            section = LiveSection(
                self._title, items,
                self._favorites_mgr, self._resume_mgr
            )
            section.item_clicked.connect(self.play_requested.emit)
            section.item_context.connect(self._show_context_menu)
            self._content_layout.addWidget(section)
        else:
            # Carrousels VOD/Series
            chunk_size = 20

            # Top Added
            top_added = items[:chunk_size]
            if top_added:
                sec = CarouselSection("Top Added", top_added)
                sec.item_clicked.connect(self.play_requested.emit)
                sec.item_context.connect(self._show_context_menu)
                self._content_layout.addWidget(sec)

            # Top Rated (milieu de la liste)
            mid = len(items) // 2
            top_rated = items[mid:mid + chunk_size]
            if top_rated:
                sec2 = CarouselSection("Top Rated", top_rated)
                sec2.item_clicked.connect(self.play_requested.emit)
                sec2.item_context.connect(self._show_context_menu)
                self._content_layout.addWidget(sec2)

            # A-Z
            az = sorted(items, key=lambda x: (x.get("name") or x.get("title") or "").lower())
            az_section = CarouselSection("Ordre alphabetique (A-Z)", az)
            az_section.item_clicked.connect(self.play_requested.emit)
            az_section.item_context.connect(self._show_context_menu)
            self._content_layout.addWidget(az_section)

        self._content_layout.addStretch()

    def _on_search(self, text):
        text = text.strip().lower()
        if text:
            filtered = [
                it for it in self._all_items
                if text in (it.get("name") or it.get("title") or "").lower()
            ]
        else:
            filtered = self._all_items
        self._render_content(filtered)

    def filter_by_category(self, cat_data):
        cat_id = cat_data.get("category_id")
        self._current_cat_id = cat_id
        if cat_id is None:
            self._render_content(self._all_items)
        elif cat_id == "__fav__":
            favs = self._favorites_mgr.get_all()
            self._render_content(favs)
        else:
            filtered = [
                it for it in self._all_items
                if str(it.get("category_id", "")) == str(cat_id)
                or str(it.get("group", "")) == str(cat_id)
            ]
            self._render_content(filtered)

    def _show_context_menu(self, ch, global_pos):
        try:
            menu = QMenu(self)
            menu.setStyleSheet(
                "QMenu{background:#12122a; color:#fff; border:1px solid #007FFF; border-radius:6px;}"
                "QMenu::item{padding:8px 20px;}"
                "QMenu::item:selected{background:#007FFF; border-radius:4px;}"
            )
            is_fav = self._favorites_mgr.is_favorite(ch)
            if is_fav:
                act_fav = QAction("\u2605  Retirer des favoris", self)
            else:
                act_fav = QAction("\u2606  Ajouter aux favoris", self)
            act_fav.triggered.connect(lambda: self.favorite_toggled.emit(ch))
            menu.addAction(act_fav)

            act_play = QAction("\u25B6  Lire", self)
            act_play.triggered.connect(lambda: self.play_requested.emit(ch))
            menu.addAction(act_play)

            menu.exec_(global_pos)
        except Exception as e:
            logger.error(f"Erreur context menu: {e}")

    def update_items(self, items):
        self._all_items = items
        self._render_content(items)
