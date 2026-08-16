# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""WindowHelper screen geometry regressions."""

from typing import ClassVar, Optional

import pytest
from PySide6.QtCore import QEasingCurve, QPoint

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
    def __init__(
        self,
        available_geometry: _FakeGeometry,
        geometry: Optional[_FakeGeometry] = None,
        device_pixel_ratio: float = 1.0,
    ) -> None:
        self._available_geometry = available_geometry
        self._geometry = geometry or available_geometry
        self._device_pixel_ratio = device_pixel_ratio

    def availableGeometry(self) -> _FakeGeometry:
        return self._available_geometry

    def geometry(self) -> _FakeGeometry:
        return self._geometry

    def devicePixelRatio(self) -> float:
        return self._device_pixel_ratio


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


def test_screen_geometry_includes_reserved_system_area(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    available_geometry = _FakeGeometry(-1920, 40, 1920, 1040)
    full_geometry = _FakeGeometry(-1920, 0, 1920, 1080)
    application = _FakeApplication(_FakeScreen(available_geometry, full_geometry))
    _FakeQGuiApplication.current = application
    monkeypatch.setattr(window_helper_module, "QGuiApplication", _FakeQGuiApplication)

    result = WindowHelper().screenGeometryAt(-1200, 1060)

    assert application.requested_point is not None
    assert (application.requested_point.x(), application.requested_point.y()) == (
        -1200,
        1060,
    )
    assert result == {"x": -1920, "y": 0, "width": 1920, "height": 1080}


def test_device_pixel_ratio_uses_screen_at_global_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    geometry = _FakeGeometry(-1920, 40, 1920, 1040)
    application = _FakeApplication(
        _FakeScreen(geometry, device_pixel_ratio=1.5)
    )
    _FakeQGuiApplication.current = application
    monkeypatch.setattr(window_helper_module, "QGuiApplication", _FakeQGuiApplication)

    assert WindowHelper().devicePixelRatioAt(-1200, 520) == 1.5
    assert application.requested_point is not None
    assert (application.requested_point.x(), application.requested_point.y()) == (
        -1200,
        520,
    )


def test_device_pixel_ratio_falls_back_without_application(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous_application = _FakeQGuiApplication.current
    _FakeQGuiApplication.current = None
    monkeypatch.setattr(window_helper_module, "QGuiApplication", _FakeQGuiApplication)
    try:
        assert WindowHelper().devicePixelRatioAt(0, 0) == 1.0
    finally:
        _FakeQGuiApplication.current = previous_application


@pytest.mark.parametrize(
    "curve_type",
    [
        QEasingCurve.Type.Linear,
        QEasingCurve.Type.OutCubic,
        QEasingCurve.Type.OutQuart,
        QEasingCurve.Type.OutBack,
        QEasingCurve.Type.OutBounce,
    ],
)
def test_easing_value_matches_qt_curve(curve_type: QEasingCurve.Type) -> None:
    helper = WindowHelper()
    expected_curve = QEasingCurve(curve_type)

    for progress in (0.0, 0.2, 0.5, 0.8, 1.0):
        assert helper.easingValueForProgress(curve_type.value, progress) == pytest.approx(
            expected_curve.valueForProgress(progress)
        )

    assert helper.easingValueForProgress(-1, -0.5) == 0.0
    assert helper.easingValueForProgress(-1, 1.5) == 1.0
    assert helper.easingValueForProgress(
        QEasingCurve.Type.NCurveTypes.value, 0.5
    ) == pytest.approx(0.5)
