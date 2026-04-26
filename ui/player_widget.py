# ui/player_widget.py - Lecteur VLC integre avec controles overlay
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QPushButton,
    QLabel, QFrame, QSizePolicy, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QKeySequence, QColor
from utils.data_manager import ResumeManager, SettingsManager

logger = logging.getLogger(__name__)


def _ms_to_str(ms):
    """Convertit des millisecondes en chaine mm:ss ou hh:mm:ss."""
    try:
        total_s = max(0, int(ms)) // 1000
        h = total_s // 3600
        m = (total_s % 3600) // 60
        s = total_s % 60
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except Exception:
        return "0:00"


class PlayerWidget(QWidget):
    """Widget principal du lecteur VLC avec overlay de controles auto-cache."""
    stopped = pyqtSignal()
    fullscreen_requested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = None
        self._player = None
        self._current_stream_id = None
        self._current_url = None
        self._is_live = False
        self._resume_mgr = ResumeManager()
        self._settings_mgr = SettingsManager()
        self._controls_visible = True
        self._vlc_ready = False
        self.setMouseTracking(True)
        self._init_ui()
        self._init_vlc()
        self._init_timers()
        self._init_shortcuts()

    def _init_ui(self):
        self.setStyleSheet("background:#000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Frame video VLC
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background:#000000;")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_frame.setMouseTracking(True)
        layout.addWidget(self.video_frame)

        # Overlay controles
        self.controls_overlay = QWidget(self)
        self.controls_overlay.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            " stop:0 rgba(0,0,0,0), stop:1 rgba(0,0,0,200));"
        )
        overlay_layout = QVBoxLayout(self.controls_overlay)
        overlay_layout.setContentsMargins(12, 8, 12, 12)
        overlay_layout.setSpacing(6)
        overlay_layout.addStretch()

        # Titre courant
        self.lbl_title = QLabel("")
        self.lbl_title.setStyleSheet("color:#ffffff; font-size:14px; font-weight:bold; background:transparent;")
        overlay_layout.addWidget(self.lbl_title)

        # Barre de progression
        self.slider_progress = QSlider(Qt.Horizontal)
        self.slider_progress.setRange(0, 1000)
        self.slider_progress.setValue(0)
        self.slider_progress.setCursor(Qt.PointingHandCursor)
        self.slider_progress.sliderMoved.connect(self._on_seek)
        overlay_layout.addWidget(self.slider_progress)

        # Ligne de controles
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.btn_play = QPushButton("\u23F8")
        self.btn_play.setFixedSize(36, 36)
        self.btn_play.setStyleSheet(
            "QPushButton{background:#007FFF;color:#fff;border-radius:18px;font-size:16px;}"
            "QPushButton:hover{background:#3399FF;}"
        )
        self.btn_play.clicked.connect(self.toggle_play)

        self.btn_stop = QPushButton("\u23F9")
        self.btn_stop.setFixedSize(32, 32)
        self.btn_stop.setStyleSheet(
            "QPushButton{background:#1e1e2e;color:#fff;border-radius:4px;font-size:14px;}"
            "QPushButton:hover{background:#333355;}"
        )
        self.btn_stop.clicked.connect(self.stop)

        self.lbl_time = QLabel("0:00 / 0:00")
        self.lbl_time.setStyleSheet("color:#ccccee; font-size:12px; background:transparent; min-width:100px;")

        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(self._settings_mgr.get("volume", 80))
        self.slider_volume.setFixedWidth(90)
        self.slider_volume.setCursor(Qt.PointingHandCursor)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)

        lbl_vol = QLabel("\U0001F50A")
        lbl_vol.setStyleSheet("color:#aaaacc; font-size:14px; background:transparent;")

        self.btn_fullscreen = QPushButton("\u26F6")
        self.btn_fullscreen.setFixedSize(32, 32)
        self.btn_fullscreen.setStyleSheet(
            "QPushButton{background:#1e1e2e;color:#007FFF;border-radius:4px;font-size:14px;}"
            "QPushButton:hover{background:#333355;}"
        )
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)

        for w in [self.btn_play, self.btn_stop, self.lbl_time, lbl_vol,
                  self.slider_volume, self.btn_fullscreen]:
            ctrl_row.addWidget(w)

        ctrl_row.addStretch()
        overlay_layout.addLayout(ctrl_row)
        self.controls_overlay.setMouseTracking(True)

    def _init_vlc(self):
        """Initialise l'instance VLC avec gestion d'erreur complete."""
        try:
            import vlc
            args = [
                "--quiet", "--no-video-title-show",
                "--network-caching=3000", "--live-caching=3000", "--file-caching=3000",
            ]
            self._instance = vlc.Instance(args)
            self._player = self._instance.media_player_new()
        except Exception as e:
            logger.error(f"Erreur initialisation VLC: {e}")
            self._instance = None
            self._player = None

    def _bind_vlc_to_frame(self):
        """Lie VLC au widget video - appele via QTimer pour eviter set_hwnd trop tot."""
        try:
            if self._player is None:
                return
            import sys
            wid = int(self.video_frame.winId())
            if sys.platform == "win32":
                self._player.set_hwnd(wid)
            elif sys.platform == "darwin":
                self._player.set_nsobject(wid)
            else:
                self._player.set_xwindow(wid)
            self._vlc_ready = True
        except Exception as e:
            logger.error(f"Erreur bind VLC frame: {e}")

    def _init_timers(self):
        """Timer de mise a jour de la progression + auto-hide des controles."""
        self._timer_update = QTimer()
        self._timer_update.setInterval(500)
        self._timer_update.timeout.connect(self._update_progress)
        self._timer_update.start()

        self._timer_hide = QTimer()
        self._timer_hide.setInterval(3000)
        self._timer_hide.setSingleShot(True)
        self._timer_hide.timeout.connect(self._hide_controls)

    def _init_shortcuts(self):
        """Raccourcis clavier : Space, F, ESC, fleches, volume."""
        try:
            QShortcut(QKeySequence(Qt.Key_Space), self, self.toggle_play)
            QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self._seek_relative(-10000))
            QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self._seek_relative(10000))
            QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self._change_volume(5))
            QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self._change_volume(-5))
            QShortcut(QKeySequence(Qt.Key_F), self, self._toggle_fullscreen)
            QShortcut(QKeySequence(Qt.Key_Escape), self, self._exit_fullscreen)
        except Exception as e:
            logger.warning(f"Erreur raccourcis clavier: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.controls_overlay.setGeometry(0, 0, self.width(), self.height())

    def mouseMoveEvent(self, event):
        self._show_controls()
        super().mouseMoveEvent(event)

    def _show_controls(self):
        self.controls_overlay.show()
        self._controls_visible = True
        self._timer_hide.start(3000)

    def _hide_controls(self):
        if self._player and self._player.is_playing():
            self.controls_overlay.hide()
            self._controls_visible = False

    def play(self, url, stream_id=None, title="", is_live=False):
        """Demarre la lecture d'un stream."""
        try:
            if self._player is None:
                logger.error("VLC non disponible")
                return
            self._current_url = url
            self._current_stream_id = stream_id
            self._is_live = is_live
            self.lbl_title.setText(title)
            media = self._instance.media_new(url)
            self._player.set_media(media)
            # set_hwnd en differe pour eviter le crash
            QTimer.singleShot(200, self._bind_vlc_to_frame)
            QTimer.singleShot(300, self._start_playback)
        except Exception as e:
            logger.error(f"Erreur lecture play(): {e}")

    def _start_playback(self):
        try:
            if self._player is None:
                return
            volume = self._settings_mgr.get("volume", 80)
            self._player.audio_set_volume(int(volume))
            self._player.play()
            if not self._is_live and self._current_stream_id:
                resume_pos = self._resume_mgr.get_position(self._current_stream_id)
                if resume_pos > 5000:
                    QTimer.singleShot(1500, lambda: self._seek_to_ms(resume_pos))
        except Exception as e:
            logger.error(f"Erreur _start_playback: {e}")

    def _seek_to_ms(self, ms):
        try:
            if self._player:
                self._player.set_time(int(ms))
        except Exception as e:
            logger.error(f"Erreur seek_to_ms: {e}")

    def toggle_play(self):
        try:
            if self._player is None:
                return
            if self._player.is_playing():
                self._player.pause()
                self.btn_play.setText("\u25B6")
            else:
                self._player.play()
                self.btn_play.setText("\u23F8")
        except Exception as e:
            logger.error(f"Erreur toggle_play: {e}")

    def stop(self):
        try:
            if self._player:
                if not self._is_live and self._current_stream_id:
                    pos = self._player.get_time()
                    if pos > 5000:
                        self._resume_mgr.save_position(self._current_stream_id, pos)
                self._player.stop()
            self.btn_play.setText("\u25B6")
            self.slider_progress.setValue(0)
            self.lbl_time.setText("0:00 / 0:00")
            self.stopped.emit()
        except Exception as e:
            logger.error(f"Erreur stop: {e}")

    def _seek_relative(self, delta_ms):
        try:
            if self._player and not self._is_live:
                current = self._player.get_time()
                total = self._player.get_length()
                new_pos = max(0, min(current + delta_ms, total))
                self._player.set_time(new_pos)
        except Exception as e:
            logger.error(f"Erreur seek_relative: {e}")

    def _on_seek(self, value):
        try:
            if self._player and not self._is_live:
                total = self._player.get_length()
                if total > 0:
                    self._player.set_time(int(total * value / 1000))
        except Exception as e:
            logger.error(f"Erreur on_seek: {e}")

    def _on_volume_changed(self, value):
        try:
            if self._player:
                self._player.audio_set_volume(value)
            self._settings_mgr.set("volume", value)
        except Exception as e:
            logger.error(f"Erreur on_volume_changed: {e}")

    def _change_volume(self, delta):
        new_val = max(0, min(100, self.slider_volume.value() + delta))
        self.slider_volume.setValue(new_val)

    def _update_progress(self):
        try:
            if self._player is None:
                return
            if self._player.is_playing() and not self._is_live:
                total = self._player.get_length()
                current = self._player.get_time()
                if total > 0:
                    self.slider_progress.blockSignals(True)
                    self.slider_progress.setValue(int(current * 1000 / total))
                    self.slider_progress.blockSignals(False)
                self.lbl_time.setText(f"{_ms_to_str(current)} / {_ms_to_str(total)}")
            elif self._is_live:
                self.lbl_time.setText("En direct")
        except Exception as e:
            logger.debug(f"Erreur _update_progress: {e}")

    def _toggle_fullscreen(self):
        self.fullscreen_requested.emit(True)

    def _exit_fullscreen(self):
        self.fullscreen_requested.emit(False)

    def set_volume(self, value):
        try:
            self.slider_volume.setValue(value)
        except Exception:
            pass

    def cleanup(self):
        """Nettoyage propre avant fermeture."""
        try:
            self._timer_update.stop()
            self._timer_hide.stop()
            if self._player:
                if not self._is_live and self._current_stream_id:
                    pos = self._player.get_time()
                    if pos > 5000:
                        self._resume_mgr.save_position(self._current_stream_id, pos)
                self._player.stop()
                self._player.release()
            if self._instance:
                self._instance.release()
        except Exception as e:
            logger.error(f"Erreur cleanup VLC: {e}")
