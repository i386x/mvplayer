#!/usr/bin/python3
# SPDX-License-Identifier: MIT

import os.path
import platform
import sys

from PyQt5.QtCore import (
    Qt,
    QDir,
    QTimer,
    QUrl,
)
from PyQt5.QtGui import (
    QColor,
    QPalette,
)
from PyQt5.QtMultimedia import (
    QMediaContent,
    QMediaPlayer,
    QMediaPlaylist,
)
from PyQt5.QtMultimediaWidgets import (
    QVideoWidget,
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
        "parent",
        "media",
        "is_paused",
        "is_fullscreen",
        "vlc_instance",
        "vlc_player",
        "video_frame",
        "palette",
        "layout",
    )

    def __init__(self, parent):
        """Initialize window instance."""
        QWidget.__init__(self)
        self.parent = parent
        self.media = None
        self.is_paused = True
        self.is_fullscreen = False

        self.init_vlc()
        self.create()

    def init_vlc(self):
        """Initialize vlc."""
        self.vlc_instance = vlc.Instance("--input-repeat=999999")
        self.vlc_player = self.vlc_instance.media_player_new()

    def create(self):
        """Create window content."""
        #self.setWindowFlags(Qt.CustomizeWindowHint)
        self.video_frame = QFrame(self)
        self.palette = self.video_frame.palette()
        self.palette.setColor(QPalette.Window, QColor(0, 0, 0))
        self.video_frame.setPalette(self.palette)
        self.video_frame.setAutoFillBackground(True)

        video_win_id = int(self.video_frame.winId())
        if platform.system() == "Linux":
            self.vlc_player.set_xwindow(video_win_id)
        elif platform.system() == "Windows":
            self.vlc_player.set_hwnd(video_win_id)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_frame)

        self.setLayout(self.layout)

    def toggle_fullscreen(self):
        """Toggle player to/from full screen mode."""
        #self.hide()
        if not self.is_fullscreen:
            self.hide()
            self.setWindowFlags(Qt.CustomizeWindowHint)
            screenres = QApplication.desktop().screenGeometry(
                0 #self.parent.screen_num
            )
            self.move(screenres.x(), screenres.y())
            self.resize(screenres.width(), screenres.height())
            self.show()
            self.is_fullscreen = True
            #self.showFullScreen()
            #self.vlc_player.set_fullscreen(True)
        else:
            self.hide()
            self.setWindowFlags(Qt.Window)
            screenres = QApplication.desktop().screenGeometry(0)
            self.move(int(screenres.x() / 2), int(screenres.y() / 2))
            self.resize(int(screenres.width() / 2), int(screenres.height() / 2))
            self.show()
            self.is_fullscreen = False
            #self.vlc_player.set_fullscreen(False)
            #self.showNormal()


class VideoWidget(QVideoWidget):
    """Customized video widget."""

    __slots__ = ()

    def __init__(self):
        """Initialize video widget."""
        QVideoWidget.__init__(self)

    def toggle_fullscreen(self):
        """Toggle window to/from full screen mode."""
        self.setFullScreen(not self.isFullScreen())

    def keyPressEvent(self, event):
        """Key pressed handler."""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.setFullScreen(False)
            event.accept()
        else:
            QVideoWidget.keyPressEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        """Double click handler."""
        self.toggle_fullscreen()
        event.accept()


class QtPlayerWindow(QWidget):
    """Player window using Qt video."""

    __slots__ = (
        "parent",
        "media_player",
        "video_widget",
        "layout",
    )

    def __init__(self, parent):
        """Initialize window instance."""
        QWidget.__init__(self)

        self.parent = parent

        self.create()

    def open(self):
        """Open a video."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select a video", QDir.homePath()
        )
        if not filename:
            return

        playlist = QMediaPlaylist()
        playlist.addMedia(QMediaContent(QUrl.fromLocalFile(filename)))
        playlist.setPlaybackMode(QMediaPlaylist.Loop)

        self.media_player.setPlaylist(playlist)

        self.parent.volume_slider.setValue(100)

        self.show()

    def close(self):
        """Close the window."""
        self.stop()
        self.hide()

    def play_pause(self):
        """Play/pause the video."""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            if self.isHidden():
                self.show()
            self.media_player.play()

    def stop(self):
        """Stop the video."""
        self.media_player.stop()

    def toggle_fullscreen(self):
        """Toggle window to/from full screen mode."""
        self.video_widget.toggle_fullscreen()

    def create(self):
        """Create window content."""
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.video_widget = VideoWidget()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_widget)

        self.setLayout(self.layout)

        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

    def set_volume(self, volume):
        """Set video volume."""
        self.media_player.setVolume(volume)

    def set_position(self, position):
        """Set video position."""
        self.media_player.setPosition(position)

    def state_changed(self, state):
        """Called when media state has been changed."""
        self.parent.play_pause_button.setText(
            "Pause" if self.media_player.state() == QMediaPlayer.PlayingState \
            else "Play"
        )

    def position_changed(self, position):
        """Called when video position has been changed."""
        self.parent.position_slider.setValue(position)

    def duration_changed(self, duration):
        """Called when video duration has been changed."""
        self.parent.position_slider.setRange(0, duration)


class ControlPanel(QGroupBox):
    """Panel with controls."""

    __slots__ = (
        "parent",
        "screen_num",
        "player",
        "controls_layout",
        "play_pause_button",
        "stop_button",
        "volume_slider",
        "fullscreen_button",
        "screen_label",
        "open_button",
        "close_button",
        "position_slider",
        "layout",
    )

    def __init__(self, parent, screen_num):
        """Initialize the control panel."""
        QGroupBox.__init__(self)
        self.setStyleSheet("QGroupBox { border: 1px solid darkgrey; }")
        self.setFlat(False)

        self.parent = parent
        self.screen_num = screen_num
        self.player = PlayerWindow(self)
        #self.player = QtPlayerWindow(self)

        self.create()

    def open(self):
        """Open video to play."""
        filename = QFileDialog.getOpenFileName(
            self, "Select a video", os.path.expanduser("~")
        )
        if not filename:
            return

        self.player.media = self.player.vlc_instance.media_new(filename[0])
        self.player.vlc_player.set_media(self.player.media)
        self.player.media.parse()

        self.volume_slider.setValue(100)

        w, h = self.player.vlc_player.video_get_size()

        self.player.setWindowTitle(self.player.media.get_meta(0))
        self.player.resize(w, h)
        self.player.show()
        #self.player.open()

    def close(self):
        """Close video."""
        self.stop()
        self.player.hide()
        #self.player.close()

    def play_pause(self):
        """Play/pause the video."""
        if self.is_playing():
            self.player.vlc_player.pause()
            self.play_pause_button.setText("Play")
            self.player.is_paused = True
        else:
            if self.player.vlc_player.play() == -1:
                return
            if self.player.isHidden():
                self.player.show()
            self.play_pause_button.setText("Pause")
            self.parent.timer.start()
            self.player.is_paused = False
        #self.player.play_pause()

    def stop(self):
        """Stop playing the video."""
        self.player.vlc_player.stop()
        self.player.is_paused = True
        self.play_pause_button.setText("Play")
        #self.player.stop()

    def set_volume(self, volume):
        """Set video volume."""
        self.player.vlc_player.audio_set_volume(volume)
        #self.player.set_volume(volume)

    def set_position(self):
    #def set_position(self, position):
        """Set video position."""
        self.parent.timer.stop()
        pos = self.position_slider.value()
        self.player.vlc_player.set_position(pos / 1000.0)
        self.parent.timer.start()
        #self.player.set_position(position)

    def fullscreen(self):
        """Switch player to full screen."""
        self.player.toggle_fullscreen()

    def create(self):
        """Create controls."""
        self.controls_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.controls_layout.addWidget(self.play_pause_button)
        self.play_pause_button.clicked.connect(self.play_pause)

        self.stop_button = QPushButton("Stop")
        self.controls_layout.addWidget(self.stop_button)
        self.stop_button.clicked.connect(self.stop)

        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setToolTip("Volume")
        self.controls_layout.addWidget(self.volume_slider)
        self.volume_slider.valueChanged.connect(self.set_volume)

        self.controls_layout.addStretch(1)

        self.fullscreen_button = QPushButton("Full Screen")
        self.controls_layout.addWidget(self.fullscreen_button)
        self.fullscreen_button.clicked.connect(self.fullscreen)

        self.screen_label = QLabel()
        self.screen_label.setText(f"Screen #{self.screen_num}")
        self.controls_layout.addWidget(self.screen_label)

        self.open_button = QPushButton("Open")
        self.controls_layout.addWidget(self.open_button)
        self.open_button.clicked.connect(self.open)

        self.close_button = QPushButton("Close")
        self.controls_layout.addWidget(self.close_button)
        self.close_button.clicked.connect(self.close)

        self.position_slider = QSlider(Qt.Horizontal, self)
        self.position_slider.setMaximum(1000)
        #self.position_slider.setRange(0, 0)
        self.position_slider.setToolTip("Position")
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.set_position)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.controls_layout)
        self.layout.addWidget(self.position_slider)

        self.setLayout(self.layout)

    def is_playing(self):
        """Check whether video is playing."""
        return self.player.vlc_player.is_playing()

    def update(self):
        """Update the status of controls."""
        if not self.player.media:
            return
        pos = int(self.player.vlc_player.get_position() * 1000)
        self.position_slider.setValue(pos)
        self.play_pause_button.setText(
            "Play" if self.player.is_paused else "Pause"
        )


class MainWindow(QMainWindow):
    """Main window with controls."""

    __slots__ = (
        "controls",
        "widget",
        "layout",
        "shared_controls_layout",
        "play_pause_all_button",
        "stop_all_button",
    )

    def __init__(self):
        """Initialize main window."""
        QMainWindow.__init__(self)
        self.setWindowTitle("Multi Video Player")

        self.controls = []

        self.create()

    def play_pause_all(self):
        """Play/pause all videos."""
        for control in self.controls:
            control.play_pause()

    def stop_all(self):
        """Stop all videos."""
        for control in self.controls:
            control.stop()

    def create(self):
        """Create controls widgets."""
        self.widget = QWidget(self)
        self.setCentralWidget(self.widget)

        self.layout = QVBoxLayout()

        for i in range(MAX_DISPLAYS):
            control = ControlPanel(self, i + 1)
            self.layout.addWidget(control)
            self.controls.append(control)

        self.shared_controls_layout = QHBoxLayout()

        self.shared_controls_layout.addStretch(1)

        self.play_pause_all_button = QPushButton("Play/Pause all")
        self.shared_controls_layout.addWidget(self.play_pause_all_button)
        self.play_pause_all_button.clicked.connect(self.play_pause_all)

        self.stop_all_button = QPushButton("Stop all")
        self.shared_controls_layout.addWidget(self.stop_all_button)
        self.stop_all_button.clicked.connect(self.stop_all)

        self.shared_controls_layout.addStretch(1)

        self.layout.addLayout(self.shared_controls_layout)

        self.widget.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update)

    def update(self):
        """Update user interface status."""
        for control in self.controls:
            control.update()


if __name__ == "__main__":
    application = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(application.exec_())
