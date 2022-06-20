# Multi Video Player

A simple vlc-based which is able to play multiple videos simultaneously at the
same time in multiple windows.

## Requirements

* [VLC media player](https://www.videolan.org/vlc/)
* [Python](https://www.python.org/downloads/)
* [PyQt5](https://pypi.org/project/PyQt5/)
* [python-vlc](https://pypi.org/project/python-vlc/)

## Installation

Just download it from [here](https://raw.githubusercontent.com/i386x/mvplayer/main/mvplayer.pyw).

## Running

### On Microsoft Windows

Double click on `mvplayer.pyw`.

### On Linux

```sh
chmod a+x mvplayer.pyw
./mvplayer.pyw
```

If you are seeing two windows (one frameless with video and one with a black
background), try:
```sh
XDG_SESSION_TYPE=X11 ./mvplayer.pyw
```
