# ui/categories_screen.py - Ecran categories 2 colonnes style Smarters Pro
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.home_screen import LogoWidget


class CategoryCard(QFrame):
    """Carte de categorie style Smarters (fond bleu nuit, icone moniteur, texte)."""
    clicked = pyqtSignal(object)  # emet la donnee de la categorie

    def __init__(self, cat_data, selected=False, parent=None):
        super().__init__(parent)
        self.cat_data = cat_data
        self._selected = selected
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(58)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        lbl_icon = QLabel("\U0001F5B3")
        lbl_icon.setStyleSheet("font-size:18px; color:#aaccff; background:transparent;")
        lbl_icon.setFixedWidth(26)
        layout.addWidget(lbl_icon)

        name = cat_data.get("category_name") or cat_data.get("name") or "?"
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            "font-size:13px; color:#ffffff; background:transparent; font-weight: bold;"
            if selected else
            "font-size:13px; color:#cce0ff; background:transparent;"
        )
        lbl_name.setWordWrap(False)
        layout.addWidget(lbl_name, stretch=1)

    def _apply_style(self):
        if self._selected:
            self.setStyleSheet(
                "CategoryCard{background:rgba(0,127,255,0.3); border-radius:10px;"
                " border:2px solid #007FFF;}"
            )
        elif self._hovered:
            self.setStyleSheet(
                "CategoryCard{background:rgba(0,80,180,0.45); border-radius:10px;"
                " border:1px solid rgba(0,127,255,0.5);}"
            )
        else:
            self.setStyleSheet(
                "CategoryCard{background:rgba(10,25,65,0.8); border-radius:10px;"
                " border:1px solid rgba(0,127,255,0.12);}"
            )

    def set_selected(self, val):
        self._selected = val
        self._apply_style()

    def enterEvent(self, e):
        self._hovered = True
        if not self._selected:
            self._apply_style()

    def leaveEvent(self, e):
        self._hovered = False
        if not self._selected:
            self._apply_style()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.cat_data)


class CategoriesScreen(QWidget):
    """
    Ecran de selection de categorie - grille 2 colonnes style Smarters Pro.
    Emet category_selected(cat_data) quand l'utilisateur choisit une categorie.
    """
    category_selected = pyqtSignal(object)
    back_requested = pyqtSignal()

    def __init__(self, title, categories, parent=None):
        super().__init__(parent)
        self._title = title
        self._categories = categories
        self._cards = []
        self._selected_id = None
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
        tl.setSpacing(12)

        logo = LogoWidget(size=38)
        tl.addWidget(logo)
        lbl_app = QLabel("IPTV Azure")
        lbl_app.setStyleSheet("color:#007FFF; font-size:17px; font-weight:bold; background:transparent;")
        tl.addWidget(lbl_app)
        tl.addStretch()

        lbl_title = QLabel(self._title.upper())
        lbl_title.setStyleSheet(
            "color:#ffffff; font-size:18px; font-weight:bold;"
            " background:transparent; letter-spacing:2px;"
        )
        lbl_title.setAlignment(Qt.AlignCenter)
        tl.addStretch()
        tl.addWidget(lbl_title)
        tl.addStretch()

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.setFixedWidth(220)
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._on_search)
        tl.addWidget(self.search_input)

        btn_back = QPushButton("\u21A9  Retour")
        btn_back.setObjectName("btn_nav")
        btn_back.clicked.connect(self.back_requested.emit)
        tl.addWidget(btn_back)
        main.addWidget(topbar)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none; background:transparent;}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background:transparent;")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(10)
        self._grid_layout.setContentsMargins(28, 20, 28, 20)

        scroll.setWidget(self._grid_widget)
        main.addWidget(scroll, stretch=1)

        self._populate(self._categories)

    def _populate(self, categories):
        # Vider
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        # ALL en premier (toute la largeur)
        all_cat = {"category_id": None, "category_name": "ALL"}
        all_card = CategoryCard(all_cat, selected=(self._selected_id is None))
        all_card.clicked.connect(self._on_card_clicked)
        self._grid_layout.addWidget(all_card, 0, 0, 1, 2)
        self._cards.append(all_card)

        # FAVOURITE
        fav_cat = {"category_id": "__fav__", "category_name": "FAVOURITE"}
        fav_card = CategoryCard(fav_cat, selected=False)
        fav_card.clicked.connect(self._on_card_clicked)
        self._grid_layout.addWidget(fav_card, 1, 1, 1, 1)
        self._cards.append(fav_card)

        row = 1
        col = 0
        for cat in categories:
            card = CategoryCard(cat, selected=False)
            card.clicked.connect(self._on_card_clicked)
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # Espaceur bas
        self._grid_layout.setRowStretch(row + 1, 1)

    def _on_card_clicked(self, cat_data):
        cat_id = cat_data.get("category_id")
        self._selected_id = cat_id
        for card in self._cards:
            is_sel = card.cat_data.get("category_id") == cat_id
            card.set_selected(is_sel)
        self.category_selected.emit(cat_data)

    def _on_search(self, text):
        text = text.strip().lower()
        filtered = [
            c for c in self._categories
            if text in (c.get("category_name") or "").lower()
        ] if text else self._categories
        self._populate(filtered)

    def update_categories(self, categories):
        self._categories = categories
        self._populate(categories)
