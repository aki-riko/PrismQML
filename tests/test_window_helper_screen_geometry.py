# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""WindowHelper screen geometry regressions."""

from typing import ClassVar, Optional

import pytest
from PySide6.QtCore import QPoint

from prismqml.python.core import window_helper as window_helper_module
from prismqml.python.core.window_helper import WindowHelper


class _FakeGeometry:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self._values = x, y, width, height

    def x(self) -> int:
        return self._values[0]

    def y(self) -> int:
        return self._values[1]

    def width(self) -> int:
        return self._values[2]

    def height(self) -> int:
        return self._values[3]


class _FakeScreen:
    def __init__(self, geometry: _FakeGeometry) -> None:
        self._geometry = geometry

    def availableGeometry(self) -> _FakeGeometry:
        return self._geometry


class _FakeApplication:
    def __init__(self, screen: _FakeScreen) -> None:
        self._screen = screen
        self.requested_point: Optional[QPoint] = None

    def screenAt(self, point: QPoint) -> _FakeScreen:
        self.requested_point = point
        return self._screen

    def primaryScreen(self) -> _FakeScreen:
        return self._screen


class _FakeQGuiApplication:
    current: ClassVar[Optional[_FakeApplication]] = None

    @classmethod
    def instance(cls) -> Optional[_FakeApplication]:
        return cls.current


def test_available_screen_geometry_preserves_negative_monitor_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geometry = _FakeGeometry(-1920, 40, 1920, 1040)
    application = _FakeApplication(_FakeScreen(geometry))
    _FakeQGuiApplication.current = application
    monkeypatch.setattr(window_helper_module, "QGuiApplication", _FakeQGuiApplication)

    result = WindowHelper().availableScreenGeometryAt(-1200, 520)

    assert application.requested_point is not None
    assert (application.requested_point.x(), application.requested_point.y()) == (
        -1200,
        520,
    )
    assert result == {"x": -1920, "y": 40, "width": 1920, "height": 1040}
