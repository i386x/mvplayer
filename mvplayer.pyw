#!/usr/bin/python3
# SPDX-License-Identifier: MIT

import platform
import sys

from PyQt5.QtCore import (
    Qt,
    QDir,
    QTimer,
)
from PyQt5.QtGui import (
    QColor,
    QPalette,
)
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
import vlc

MAX_DISPLAYS = 4


class PlayerWindow(QWidget):
    """Player window using vlc."""

    __slots__ = (
        "_owner",
        "_media",
        "_volume",
        "_wnd_x",
        "_wnd_y",
        "_wnd_w",
        "_wnd_h",
        "_wnd_flags",
        "_ly_margins",
        "_is_fullscreen",
        "_vlc_instance",
        "_vlc_player",
        "_video_frame",
        "_palette",
        "_layout",
    )

    def __init__(self, owner):
        """Initialize window instance."""
        QWidget.__init__(self)
        self._owner = owner
        self._media = None
        self._volume = 100
        self._wnd_x = None
        self._wnd_y = None
        self._wnd_w = None
        self._wnd_h = None
        self._wnd_flags = None
        self._ly_margins = None
        self._is_fullscreen = False

        self.init_vlc()
        self.create_ui()

    def init_vlc(self):
        """Initialize vlc."""
        self._vlc_instance = vlc.Instance("--input-repeat=999999")
        self._vlc_player = self._vlc_instance.media_player_new()

    def create_ui(self):
        """Create window content."""
        self.setMinimumSize(640, 480)

        self._video_frame = QFrame()
        self._palette = self._video_frame.palette()
        self._palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self._video_frame.setPalette(self._palette)
        self._video_frame.setAutoFillBackground(True)

        video_win_id = int(self._video_frame.winId())
        if platform.system() == "Linux":
            self._vlc_player.set_xwindow(video_win_id)
        elif platform.system() == "Windows":
            self._vlc_player.set_hwnd(video_win_id)

        self._layout = QVBoxLayout()
        self._layout.addWidget(self._video_frame)

        self.setLayout(self._layout)

    def set_volume_action(self, volume):
        """Set video volume."""
        self._volume = volume
        if not self._media:
            return
        self._vlc_player.audio_set_volume(self._volume)

    def set_position_action(self):
        """Set video position."""
        if not self._media:
            return
        self._owner._owner._timer.stop()
        pos = self._owner._position_slider.value()
        self._vlc_player.set_position(pos / 1000.0)
        self._owner._owner._timer.start()

    def open_action(self):
        """Open a video to play."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select a video", QDir.homePath()
        )
        if not filename:
            return

        self.release_media()
        self._media = self._vlc_instance.media_new(filename)
        self._vlc_player.set_media(self._media)
        self._media.parse()

        self._owner._volume_slider.setValue(self._volume)

        self.setWindowTitle(self._media.get_meta(0))
        self.show()

    def close_action(self):
        """Close the window."""
        if not self._media:
            return
        if self._is_fullscreen:
            self.toggle_fullscreen_action()
        self.hide()
        self.release_media()

    def release_media(self):
        """Release resources associated with the video."""
        if not self._media:
            return
        self.stop_action()
        self._vlc_player.set_media(None)
        self._media = None

    def play_pause_action(self):
        """Play/pause the video."""
        if self._vlc_player.is_playing():
            self._vlc_player.pause()
            self._owner._play_pause_button.setText("Play")
        else:
            if self._vlc_player.play() == -1:
                return
            if self.isHidden():
                self.show()
            self._owner._play_pause_button.setText("Pause")
            self._owner._owner._timer.start()

    def stop_action(self):
        """Stop the video."""
        self._vlc_player.stop()
        self._owner._play_pause_button.setText("Play")

    def toggle_fullscreen_action(self):
        """Toggle player to/from full screen mode."""
        if not self._media:
            return
        self.hide()
        if not self._is_fullscreen:
            self._wnd_x = self.x()
            self._wnd_y = self.y()
            self._wnd_w = self.width()
            self._wnd_h = self.height()
            self._wnd_flags = self.windowFlags()
            self._ly_margins = self._layout.contentsMargins()

            screen_num = self._owner._screen_num
            screen_count = QApplication.desktop().screenCount()
            screenres = QApplication.desktop().screenGeometry(
                screen_num if screen_num < screen_count else 0
            )
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self._layout.setContentsMargins(0, 0, 0, 0)
            self.move(screenres.x(), screenres.y())
            self.resize(screenres.width(), screenres.height())
            self.showFullScreen()
            self._is_fullscreen = True
        else:
            self.setWindowFlags(self._wnd_flags)
            self._layout.setContentsMargins(
                self._ly_margins.left(),
                self._ly_margins.top(),
                self._ly_margins.right(),
                self._ly_margins.bottom()
            )
            self.move(self._wnd_x, self._wnd_y)
            self.resize(self._wnd_w, self._wnd_h)
            self.showNormal()
            self._is_fullscreen = False


class ControlPanel(QGroupBox):
    """Panel with controls."""

    __slots__ = (
        "_owner",
        "_screen_num",
        "_player",
        "_controls_layout",
        "_play_pause_button",
        "_stop_button",
        "_volume_slider",
        "_fullscreen_button",
        "_screen_label",
        "_open_button",
        "_close_button",
        "_position_slider",
        "_layout",
    )

    def __init__(self, owner, screen_num):
        """Initialize the control panel."""
        QGroupBox.__init__(self)
        self.setStyleSheet("QGroupBox { border: 1px solid darkgrey; }")
        self.setFlat(False)

        self._owner = owner
        self._screen_num = screen_num
        self._player = PlayerWindow(self)

        self.create_ui()

    def create_ui(self):
        """Create controls."""
        self._controls_layout = QHBoxLayout()

        self._play_pause_button = QPushButton("Play")
        self._controls_layout.addWidget(self._play_pause_button)
        self._play_pause_button.clicked.connect(self._player.play_pause_action)

        self._stop_button = QPushButton("Stop")
        self._controls_layout.addWidget(self._stop_button)
        self._stop_button.clicked.connect(self._player.stop_action)

        self._volume_slider = QSlider(Qt.Horizontal, self)
        self._volume_slider.setMaximum(100)
        self._volume_slider.setValue(100)
        self._volume_slider.setToolTip("Volume")
        self._controls_layout.addWidget(self._volume_slider)
        self._volume_slider.valueChanged.connect(
            self._player.set_volume_action
        )

        self._controls_layout.addStretch(1)

        self._fullscreen_button = QPushButton("Full Screen")
        self._controls_layout.addWidget(self._fullscreen_button)
        self._fullscreen_button.clicked.connect(
            self._player.toggle_fullscreen_action
        )

        self._screen_label = QLabel()
        self._screen_label.setText(f"Screen #{self._screen_num}")
        self._controls_layout.addWidget(self._screen_label)

        self._open_button = QPushButton("Open")
        self._controls_layout.addWidget(self._open_button)
        self._open_button.clicked.connect(self._player.open_action)

        self._close_button = QPushButton("Close")
        self._controls_layout.addWidget(self._close_button)
        self._close_button.clicked.connect(self._player.close_action)

        self._position_slider = QSlider(Qt.Horizontal, self)
        self._position_slider.setMaximum(1000)
        self._position_slider.setToolTip("Position")
        self._position_slider.sliderMoved.connect(
            self._player.set_position_action
        )
        self._position_slider.sliderPressed.connect(
            self._player.set_position_action
        )

        self._layout = QVBoxLayout()
        self._layout.addLayout(self._controls_layout)
        self._layout.addWidget(self._position_slider)

        self.setLayout(self._layout)

    def update_ui(self):
        """Update the status of controls."""
        if self._player._media:
            pos = int(self._player._vlc_player.get_position() * 1000)
            text = "Pause" if self._player._vlc_player.is_playing() else "Play"
        else:
            pos = 0
            text = "Play"
        self._position_slider.setValue(pos)
        self._play_pause_button.setText(text)


class MainWindow(QMainWindow):
    """Main window with controls."""

    __slots__ = (
        "_controls",
        "_widget",
        "_layout",
        "_shared_controls_layout",
        "_play_pause_all_button",
        "_stop_all_button",
    )

    def __init__(self):
        """Initialize main window."""
        QMainWindow.__init__(self)
        self.setWindowTitle("Multi Video Player")

        self._controls = []

        self.create_ui()

    def play_pause_all_action(self):
        """Play/pause all videos."""
        for control in self._controls:
            control._player.play_pause_action()

    def stop_all_action(self):
        """Stop all videos."""
        for control in self._controls:
            control._player.stop_action()

    def create_ui(self):
        """Create controls widgets."""
        self._widget = QWidget(self)
        self.setCentralWidget(self._widget)

        self._layout = QVBoxLayout()

        for i in range(MAX_DISPLAYS):
            control = ControlPanel(self, i + 1)
            self._layout.addWidget(control)
            self._controls.append(control)

        self._shared_controls_layout = QHBoxLayout()

        self._shared_controls_layout.addStretch(1)

        self._play_pause_all_button = QPushButton("Play/Pause all")
        self._shared_controls_layout.addWidget(self._play_pause_all_button)
        self._play_pause_all_button.clicked.connect(self.play_pause_all_action)

        self._stop_all_button = QPushButton("Stop all")
        self._shared_controls_layout.addWidget(self._stop_all_button)
        self._stop_all_button.clicked.connect(self.stop_all_action)

        self._shared_controls_layout.addStretch(1)

        self._layout.addLayout(self._shared_controls_layout)

        self._widget.setLayout(self._layout)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self.update_ui)

    def update_ui(self):
        """Update user interface status."""
        for control in self._controls:
            control.update_ui()


if __name__ == "__main__":
    application = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(application.exec_())
