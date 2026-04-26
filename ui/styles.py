# ui/styles.py - Feuille de style globale IPTV Azure

STYLESHEET = """
QWidget {
    background-color: #0d0d0d;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0d0d0d;
}

QFrame {
    background-color: #0d0d0d;
    border: none;
}

QPushButton {
    background-color: #007FFF;
    color: #ffffff;
    border: none;
    padding: 8px 18px;
    border-radius: 5px;
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
    background-color: #333355;
    color: #666688;
}

QPushButton#btn_flat {
    background-color: transparent;
    color: #007FFF;
    padding: 4px 10px;
    border-radius: 4px;
}

QPushButton#btn_flat:hover {
    background-color: #1a1a3a;
}

QLineEdit {
    background-color: #1e1e2e;
    border: 1px solid #333355;
    border-radius: 5px;
    padding: 7px 12px;
    color: #ffffff;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1.5px solid #007FFF;
}

QLineEdit::placeholder {
    color: #555577;
}

QTabWidget::pane {
    border: none;
    background-color: #0d0d0d;
}

QTabBar::tab {
    background-color: #111122;
    color: #aaaacc;
    padding: 9px 22px;
    border-radius: 0px;
    font-size: 13px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #0d0d0d;
    color: #007FFF;
    border-bottom: 2px solid #007FFF;
}

QTabBar::tab:hover {
    background-color: #1a1a2e;
    color: #ffffff;
}

QListWidget {
    background-color: #111111;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 8px 14px;
    border-bottom: 1px solid #1a1a2e;
    color: #ccccee;
}

QListWidget::item:selected {
    background-color: #007FFF;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #1a1a3a;
}

QScrollBar:vertical {
    background: #111111;
    width: 7px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #007FFF;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #111111;
    height: 7px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: #007FFF;
    border-radius: 3px;
    min-width: 30px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QSlider::groove:horizontal {
    height: 5px;
    background: #333355;
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

QLabel {
    color: #ffffff;
    background: transparent;
}

QLabel#label_credits {
    color: #007FFF;
    font-size: 11px;
}

QComboBox {
    background-color: #1e1e2e;
    border: 1px solid #333355;
    border-radius: 5px;
    padding: 6px 12px;
    color: #ffffff;
    font-size: 13px;
}

QComboBox:focus {
    border: 1.5px solid #007FFF;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    selection-background-color: #007FFF;
    color: #ffffff;
    border: 1px solid #333355;
}

QToolTip {
    background-color: #1e1e2e;
    color: #ffffff;
    border: 1px solid #007FFF;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

QMessageBox {
    background-color: #111122;
}

QMessageBox QLabel {
    color: #ffffff;
}

QDialog {
    background-color: #111122;
}

QProgressBar {
    background-color: #1e1e2e;
    border: none;
    border-radius: 3px;
    height: 5px;
}

QProgressBar::chunk {
    background-color: #007FFF;
    border-radius: 3px;
}
"""