# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared acrylic capture test probes. 亚克力截图测试共享探针。"""

from types import SimpleNamespace

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage

from prismqml.python.window import mica_window


CAUGHT_ERRORS = (ValueError, OSError, RuntimeError)
PROPAGATED_ERRORS = (TypeError, AttributeError, KeyboardInterrupt, SystemExit)
PIPELINE_STAGES = (
    "window.screen",
    "window.x",
    "window.y",
    "screen.geometry",
    "screen.grab",
    "pixmap.is_null",
    "pixmap.to_image",
    "blur",
    "state.set_image",
    "state.image_id",
    "signal.emit",
    "log.debug",
)


def make_image(color: QColor) -> QImage:
    image = QImage(8, 6, QImage.Format.Format_ARGB32)
    image.fill(color)
    return image


class StateProbe:
    def __init__(self, probe):
        self._probe = probe
        self.current_id = 0
        self.current_image = None

    def set_image(self, image):
        self._probe.step("state.set_image", image)
        self.current_image = image
        self.current_id += 1

    @property
    def image_id(self):
        self._probe.step("state.image_id", self.current_id)
        return self.current_id


class SignalProbe:
    def __init__(self, probe):
        self._probe = probe
        self.emitted = []

    def emit(self, value):
        self._probe.step("signal.emit", value)
        self.emitted.append(value)


class PixmapProbe:
    def __init__(self, probe):
        self._probe = probe

    def isNull(self):
        self._probe.step("pixmap.is_null")
        return self._probe.null_pixmap

    def toImage(self):
        self._probe.step("pixmap.to_image")
        return self._probe.source_image


class ScreenProbe:
    def __init__(self, probe):
        self._probe = probe

    def geometry(self):
        self._probe.step("screen.geometry")
        return self._probe.geometry

    def grabWindow(self, *args):
        self._probe.step("screen.grab", *args)
        return self._probe.pixmap


class WindowProbe:
    def __init__(self, probe):
        self._probe = probe

    def screen(self):
        self._probe.step("window.screen")
        return None if self._probe.use_fallback else self._probe.screen

    def x(self):
        self._probe.step("window.x")
        return self._probe.window_x

    def y(self):
        self._probe.step("window.y")
        return self._probe.window_y


class PipelineProbe:
    def __init__(self, fail_stage=None, error=None, failures=None):
        self.failures = dict(failures or {})
        if fail_stage is not None:
            self.failures[fail_stage] = error
        self.events = []
        self.logs = []
        self.use_fallback = False
        self.no_screens = False
        self.null_pixmap = False
        self.window_x = 30
        self.window_y = 40
        self.geometry = QRect(-100, 50, 1920, 1080)
        self.source_image = make_image(QColor(10, 20, 30, 255))
        self.blurred_image = make_image(QColor(40, 50, 60, 255))
        self.state = StateProbe(self)
        self.signal = SignalProbe(self)
        self.pixmap = PixmapProbe(self)
        self.screen = ScreenProbe(self)
        self.window = WindowProbe(self)
        self.owner = SimpleNamespace(
            _image_state=self.state,
            _blur_radius=8,
            imageReady=self.signal,
        )

    def step(self, stage, *values):
        self.events.append((stage, *values))
        if stage in self.failures:
            raise self.failures[stage]

    def application_screens(self):
        self.step("application.screens")
        return [] if self.no_screens else [self.screen, object()]

    def blur(self, image, radius):
        self.step("blur", image, radius)
        return self.blurred_image

    def log(self, level, message):
        self.step(f"log.{level}", message)
        self.logs.append((level, message))

    def install(self, monkeypatch):
        application = SimpleNamespace(screens=self.application_screens)
        monkeypatch.setattr(mica_window, "QApplication", application)
        monkeypatch.setattr(mica_window, "_gaussian_blur_image", self.blur)
        monkeypatch.setattr(mica_window, "warning", lambda msg: self.log("warning", msg))
        monkeypatch.setattr(mica_window, "error", lambda msg: self.log("error", msg))
        monkeypatch.setattr(mica_window, "debug", lambda msg: self.log("debug", msg))


class CapturedScreen:
    def __init__(self, pixmap, geometry):
        self._pixmap = pixmap
        self._geometry = geometry
        self.calls = []

    def geometry(self):
        return self._geometry

    def grabWindow(self, *args):
        self.calls.append(args)
        return self._pixmap


class CapturedWindow:
    def __init__(self, screen, x=30, y=40):
        self._screen = screen
        self._x = x
        self._y = y

    def screen(self):
        return self._screen

    def x(self):
        return self._x

    def y(self):
        return self._y


class GuardWindow:
    def __init__(self, events, value=True, error=None):
        self._events = events
        self._value = value
        self._error = error

    def __bool__(self):
        self._events.append(("guard.window",))
        if self._error is not None:
            raise self._error
        return self._value


class GuardNumber:
    def __init__(self, events, name, value=False, error=None):
        self._events = events
        self._name = name
        self._value = value
        self._error = error

    def __le__(self, _other):
        self._events.append((f"guard.{self._name}",))
        if self._error is not None:
            raise self._error
        return self._value


def run_pipeline(probe, monkeypatch, x=7, y=5, width=20, height=10):
    probe.install(monkeypatch)
    return mica_window.AcrylicHelper.grabAndBlur(
        probe.owner, probe.window, x, y, width, height
    )


def event_names(probe):
    return [event[0] for event in probe.events]
