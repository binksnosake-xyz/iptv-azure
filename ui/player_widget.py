# ui/player_widget.py - Lecteur VLC integre avec controles overlay
import sys
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QPushButton,
    QLabel, QFrame, QSizePolicy, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from utils.data_manager import ResumeManager, SettingsManager

logger = logging.getLogger(__name__)


def _ms_to_str(ms):
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
    stopped = pyqtSignal()
    fullscreen_requested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = None
        self._player = None
        self._media = None
        self._current_stream_id = None
        self._current_url = None
        self._is_live = False
        self._resume_mgr = ResumeManager()
        self._settings_mgr = SettingsManager()
        self._vlc_bound = False
        self._pending_url = None
        self._pending_title = None
        self._pending_stream_id = None
        self._pending_is_live = False
        self.setMouseTracking(True)
        self._init_ui()
        self._init_vlc()
        self._init_timers()
        self._init_shortcuts()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        self.setStyleSheet("background:#000000;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Frame video noire qui recoit le rendu VLC
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background:#000000;")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_frame.setMouseTracking(True)
        self.video_frame.setAttribute(Qt.WA_OpaquePaintEvent, True)
        main_layout.addWidget(self.video_frame)

        # Overlay controles (par dessus video_frame)
        self.controls_overlay = QWidget(self)
        self.controls_overlay.setObjectName("controls_overlay")
        self.controls_overlay.setStyleSheet(
            "QWidget#controls_overlay{"
            "background: qlineargradient("
            "x1:0,y1:0,x2:0,y2:1,"
            "stop:0 rgba(0,0,0,0),"
            "stop:0.6 rgba(0,0,0,120),"
            "stop:1 rgba(0,0,0,210));"
            "}"
        )
        self.controls_overlay.setMouseTracking(True)
        overlay_layout = QVBoxLayout(self.controls_overlay)
        overlay_layout.setContentsMargins(14, 8, 14, 12)
        overlay_layout.setSpacing(6)
        overlay_layout.addStretch()

        # Titre
        self.lbl_title = QLabel("")
        self.lbl_title.setStyleSheet(
            "color:#ffffff; font-size:14px; font-weight:bold; background:transparent;"
        )
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
        ctrl_row.setSpacing(10)

        self.btn_play = QPushButton("\u25B6")
        self.btn_play.setFixedSize(38, 38)
        self.btn_play.setStyleSheet(
            "QPushButton{background:#007FFF;color:#fff;border-radius:19px;font-size:16px;border:none;}"
            "QPushButton:hover{background:#3399FF;}"
        )
        self.btn_play.clicked.connect(self.toggle_play)

        self.btn_stop = QPushButton("\u23F9")
        self.btn_stop.setFixedSize(34, 34)
        self.btn_stop.setStyleSheet(
            "QPushButton{background:#1e1e2e;color:#fff;border-radius:4px;font-size:14px;border:none;}"
            "QPushButton:hover{background:#333355;}"
        )
        self.btn_stop.clicked.connect(self.stop)

        self.lbl_time = QLabel("0:00 / 0:00")
        self.lbl_time.setStyleSheet(
            "color:#ccccee; font-size:12px; background:transparent; min-width:110px;"
        )

        lbl_vol = QLabel("\U0001F50A")
        lbl_vol.setStyleSheet("color:#aaaacc; font-size:14px; background:transparent;")

        self.slider_volume = QSlider(Qt.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(self._settings_mgr.get("volume", 80))
        self.slider_volume.setFixedWidth(95)
        self.slider_volume.setCursor(Qt.PointingHandCursor)
        self.slider_volume.valueChanged.connect(self._on_volume_changed)

        self.btn_fullscreen = QPushButton("\u2B1C")
        self.btn_fullscreen.setFixedSize(34, 34)
        self.btn_fullscreen.setStyleSheet(
            "QPushButton{background:#1e1e2e;color:#007FFF;border-radius:4px;font-size:14px;border:none;}"
            "QPushButton:hover{background:#333355;}"
        )
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)

        for w in [
            self.btn_play, self.btn_stop,
            self.lbl_time, lbl_vol,
            self.slider_volume, self.btn_fullscreen
        ]:
            ctrl_row.addWidget(w)

        ctrl_row.addStretch()
        overlay_layout.addLayout(ctrl_row)

    # ------------------------------------------------------------------ VLC
    def _init_vlc(self):
        try:
            import vlc
            self._vlc = vlc
            instance_args = [
                "--quiet",
                "--no-video-title-show",
                "--network-caching=3000",
                "--live-caching=3000",
                "--file-caching=3000",
                "--no-sub-autodetect-file",
            ]
            self._instance = vlc.Instance(instance_args)
            if self._instance is None:
                raise RuntimeError("vlc.Instance() a retourne None")
            self._player = self._instance.media_player_new()
            if self._player is None:
                raise RuntimeError("media_player_new() a retourne None")
            logger.info("VLC initialise avec succes")
        except Exception as e:
            logger.error(f"Erreur critique initialisation VLC : {e}")
            self._instance = None
            self._player = None

    def _bind_vlc(self):
        """
        Lie VLC au widget video.
        DOIT etre appele apres que le widget soit affiche (showEvent ou QTimer).
        """
        try:
            if self._player is None:
                return False
            # S'assurer que le widget est visible et a un handle valide
            self.video_frame.show()
            wid = int(self.video_frame.winId())
            if wid == 0:
                logger.warning("winId() == 0, retry dans 200ms")
                return False
            if sys.platform == "win32":
                self._player.set_hwnd(wid)
            elif sys.platform == "darwin":
                self._player.set_nsobject(wid)
            else:
                self._player.set_xwindow(wid)
            self._vlc_bound = True
            logger.info(f"VLC lie au widget (wid={wid})")
            return True
        except Exception as e:
            logger.error(f"Erreur _bind_vlc : {e}")
            return False

    def showEvent(self, event):
        """Premiere apparition du widget : lier VLC immediatement."""
        super().showEvent(event)
        if not self._vlc_bound:
            QTimer.singleShot(100, self._try_bind)

    def _try_bind(self):
        """Tente de lier VLC, relance si le winId n'est pas encore disponible."""
        if not self._bind_vlc():
            QTimer.singleShot(200, self._try_bind)
        else:
            # Si une lecture etait en attente, la lancer maintenant
            if self._pending_url:
                self._do_play()

    # ------------------------------------------------------------------ Lecture
    def play(self, url, stream_id=None, title="", is_live=False):
        """Interface publique : demarre la lecture d'un flux."""
        try:
            if self._player is None:
                logger.error("VLC non disponible - lecture impossible")
                return
            self._pending_url = url
            self._pending_stream_id = stream_id
            self._pending_title = title
            self._pending_is_live = is_live
            self._current_url = url
            self._current_stream_id = stream_id
            self._is_live = is_live
            self.lbl_title.setText(title)

            if self._vlc_bound:
                # VLC est deja lie, on peut lire directement
                self._do_play()
            else:
                # VLC pas encore lie, on lie d'abord puis on lira dans _try_bind
                QTimer.singleShot(100, self._try_bind)
        except Exception as e:
            logger.error(f"Erreur play() : {e}")

    def _do_play(self):
        """Demarre reellement la lecture apres que VLC soit lie."""
        try:
            if self._player is None or self._pending_url is None:
                return
            # Stop lecture precedente proprement
            try:
                self._player.stop()
            except Exception:
                pass

            # Creer le media
            media = self._instance.media_new(self._pending_url)
            if media is None:
                logger.error("media_new() a retourne None")
                return

            # Options reseau supplementaires
            media.add_option(":network-caching=3000")
            media.add_option(":live-caching=3000")

            self._player.set_media(media)
            self._media = media

            # Re-lier le hwnd juste avant play() pour etre sur
            self._bind_vlc()

            # Volume
            volume = self._settings_mgr.get("volume", 80)
            self._player.audio_set_volume(int(volume))

            # Lancer la lecture
            result = self._player.play()
            if result == -1:
                logger.error("self._player.play() a retourne -1 (erreur VLC)")
                return

            self.btn_play.setText("\u23F8")
            self._pending_url = None

            # Reprise de position (VOD uniquement)
            if not self._pending_is_live and self._pending_stream_id:
                resume_pos = self._resume_mgr.get_position(self._pending_stream_id)
                if resume_pos > 5000:
                    QTimer.singleShot(2000, lambda: self._seek_to_ms(resume_pos))

        except Exception as e:
            logger.error(f"Erreur _do_play() : {e}")

    def _seek_to_ms(self, ms):
        try:
            if self._player and self._player.is_playing():
                self._player.set_time(int(ms))
        except Exception as e:
            logger.error(f"Erreur seek_to_ms : {e}")

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
            logger.error(f"Erreur toggle_play : {e}")

    def stop(self):
        try:
            if self._player:
                if not self._is_live and self._current_stream_id:
                    pos = self._player.get_time()
                    if pos and pos > 5000:
                        self._resume_mgr.save_position(self._current_stream_id, pos)
                self._player.stop()
            self.btn_play.setText("\u25B6")
            self.slider_progress.setValue(0)
            self.lbl_time.setText("0:00 / 0:00")
            self._pending_url = None
            self.stopped.emit()
        except Exception as e:
            logger.error(f"Erreur stop() : {e}")

    def _seek_relative(self, delta_ms):
        try:
            if self._player and not self._is_live:
                current = self._player.get_time()
                total = self._player.get_length()
                if current is not None and total and total > 0:
                    new_pos = max(0, min(current + delta_ms, total))
                    self._player.set_time(new_pos)
        except Exception as e:
            logger.error(f"Erreur seek_relative : {e}")

    def _on_seek(self, value):
        try:
            if self._player and not self._is_live:
                total = self._player.get_length()
                if total and total > 0:
                    self._player.set_time(int(total * value / 1000))
        except Exception as e:
            logger.error(f"Erreur on_seek : {e}")

    def _on_volume_changed(self, value):
        try:
            if self._player:
                self._player.audio_set_volume(value)
            self._settings_mgr.set("volume", value)
        except Exception as e:
            logger.error(f"Erreur on_volume_changed : {e}")

    def _change_volume(self, delta):
        try:
            new_val = max(0, min(100, self.slider_volume.value() + delta))
            self.slider_volume.setValue(new_val)
        except Exception:
            pass

    def _update_progress(self):
        try:
            if self._player is None:
                return
            if self._player.is_playing():
                if not self._is_live:
                    total = self._player.get_length()
                    current = self._player.get_time()
                    if total and total > 0 and current is not None:
                        self.slider_progress.blockSignals(True)
                        self.slider_progress.setValue(int(current * 1000 / total))
                        self.slider_progress.blockSignals(False)
                        self.lbl_time.setText(
                            f"{_ms_to_str(current)} / {_ms_to_str(total)}"
                        )
                else:
                    self.lbl_time.setText("\U0001F534 En direct")
        except Exception as e:
            logger.debug(f"Erreur _update_progress : {e}")

    # ------------------------------------------------------------------ Fullscreen
    def _toggle_fullscreen(self):
        self.fullscreen_requested.emit(True)

    def _exit_fullscreen(self):
        self.fullscreen_requested.emit(False)

    # ------------------------------------------------------------------ Timers / Events
    def _init_timers(self):
        self._timer_update = QTimer()
        self._timer_update.setInterval(500)
        self._timer_update.timeout.connect(self._update_progress)
        self._timer_update.start()

        self._timer_hide = QTimer()
        self._timer_hide.setInterval(3000)
        self._timer_hide.setSingleShot(True)
        self._timer_hide.timeout.connect(self._hide_controls)

    def _init_shortcuts(self):
        try:
            QShortcut(QKeySequence(Qt.Key_Space), self, self.toggle_play)
            QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self._seek_relative(-10000))
            QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self._seek_relative(10000))
            QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self._change_volume(5))
            QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self._change_volume(-5))
            QShortcut(QKeySequence(Qt.Key_F), self, self._toggle_fullscreen)
            QShortcut(QKeySequence(Qt.Key_Escape), self, self._exit_fullscreen)
        except Exception as e:
            logger.warning(f"Erreur raccourcis clavier : {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.controls_overlay.setGeometry(0, 0, self.width(), self.height())
        except Exception:
            pass

    def mouseMoveEvent(self, event):
        self._show_controls()
        super().mouseMoveEvent(event)

    def _show_controls(self):
        try:
            self.controls_overlay.show()
            self._timer_hide.start(3000)
        except Exception:
            pass

    def _hide_controls(self):
        try:
            if self._player and self._player.is_playing():
                self.controls_overlay.hide()
        except Exception:
            pass

    def set_volume(self, value):
        try:
            self.slider_volume.setValue(value)
        except Exception:
            pass

    # ------------------------------------------------------------------ Cleanup
    def cleanup(self):
        try:
            self._timer_update.stop()
            self._timer_hide.stop()
            if self._player:
                if not self._is_live and self._current_stream_id:
                    pos = self._player.get_time()
                    if pos and pos > 5000:
                        self._resume_mgr.save_position(self._current_stream_id, pos)
                self._player.stop()
                self._player.release()
            if self._instance:
                self._instance.release()
        except Exception as e:
            logger.error(f"Erreur cleanup VLC : {e}")
