# ui/styles.py - Feuille de style globale IPTV Azure - Style Smarters Pro

STYLESHEET = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    background-color: #080818;
    color: #ffffff;
    font-size: 13px;
}

QMainWindow {
    background-color: #080818;
}

QFrame {
    background-color: transparent;
    border: none;
}

/* Boutons principaux */
QPushButton {
    background-color: #007FFF;
    color: #ffffff;
    border: none;
    padding: 9px 20px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #3399FF;
}
QPushButton:pressed {
    background-color: #005FBF;
}
QPushButton:disabled {
    background-color: #1e1e3a;
    color: #555577;
}

/* Boutons transparents */
QPushButton#btn_flat {
    background-color: transparent;
    color: #007FFF;
    padding: 5px 12px;
    border-radius: 5px;
    font-weight: normal;
}
QPushButton#btn_flat:hover {
    background-color: rgba(0,127,255,0.15);
}

/* Boutons nav top */
QPushButton#btn_nav {
    background-color: rgba(255,255,255,0.08);
    color: #ccddff;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
}
QPushButton#btn_nav:hover {
    background-color: rgba(0,127,255,0.25);
    color: #ffffff;
}

/* Inputs */
QLineEdit {
    background-color: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    padding: 8px 14px;
    color: #ffffff;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1.5px solid #007FFF;
    background-color: rgba(0,127,255,0.08);
}
QLineEdit::placeholder {
    color: #444466;
}

/* Tabs */
QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #778899;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: bold;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected {
    color: #007FFF;
    border-bottom: 2px solid #007FFF;
    background: transparent;
}
QTabBar::tab:hover {
    color: #aaccff;
}

/* Listes categories style Smarters */
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 0px;
    border: none;
    background: transparent;
}
QListWidget::item:selected {
    background: transparent;
    border: none;
}
QListWidget::item:hover {
    background: transparent;
}

/* Scrollbars */
QScrollBar:vertical {
    background: rgba(255,255,255,0.03);
    width: 6px;
    border-radius: 3px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #007FFF;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: rgba(255,255,255,0.03);
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #007FFF;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Slider progression */
QSlider::groove:horizontal {
    height: 4px;
    background: rgba(255,255,255,0.15);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #007FFF;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background: #007FFF;
    border-radius: 2px;
}

/* Labels */
QLabel {
    color: #ffffff;
    background: transparent;
}
QLabel#label_credits {
    color: #007FFF;
    font-size: 11px;
}
QLabel#label_section {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
}
QLabel#label_section_sub {
    color: #007FFF;
    font-size: 12px;
}

/* ComboBox */
QComboBox {
    background-color: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 6px;
    padding: 7px 14px;
    color: #ffffff;
    font-size: 13px;
}
QComboBox:focus {
    border: 1.5px solid #007FFF;
}
QComboBox QAbstractItemView {
    background-color: #12122a;
    selection-background-color: #007FFF;
    color: #ffffff;
    border: 1px solid #007FFF;
}

/* Tooltips */
QToolTip {
    background-color: #12122a;
    color: #ffffff;
    border: 1px solid #007FFF;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
}

/* MessageBox */
QMessageBox {
    background-color: #12122a;
}
QMessageBox QLabel {
    color: #ffffff;
}

/* Dialog */
QDialog {
    background-color: #12122a;
}

/* ProgressBar */
QProgressBar {
    background-color: rgba(255,255,255,0.08);
    border: none;
    border-radius: 3px;
    height: 4px;
}
QProgressBar::chunk {
    background-color: #007FFF;
    border-radius: 3px;
}

/* SplashLabel */
QLabel#splash_title {
    color: #007FFF;
    font-size: 36px;
    font-weight: bold;
}
QLabel#splash_sub {
    color: #aaccff;
    font-size: 14px;
}
"""

# Fond degrade radial style Smarters (bleu nuit)
BG_RADIAL_STYLE = """
    background: qradialgradient(
        cx:0.5, cy:0.5, radius:1.0,
        fx:0.5, fy:0.5,
        stop:0 #0d1a3a,
        stop:0.5 #080818,
        stop:1 #030308
    );
"""

# Style tuile home screen
HOME_TILE_STYLE = """
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {c1}, stop:1 {c2});
    border-radius: 16px;
    border: none;
"""

# Style categorie item
CAT_ITEM_STYLE = """
    background: rgba(15,30,70,0.85);
    border-radius: 10px;
    border: 1px solid rgba(0,127,255,0.18);
"""
CAT_ITEM_HOVER_STYLE = """
    background: rgba(0,80,180,0.55);
    border-radius: 10px;
    border: 1px solid rgba(0,127,255,0.6);
"""
CAT_ITEM_SELECTED_STYLE = """
    background: rgba(0,127,255,0.35);
    border-radius: 10px;
    border: 2px solid #007FFF;
"""
