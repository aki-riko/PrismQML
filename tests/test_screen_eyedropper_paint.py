# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Screen eyedropper paint contracts. 屏幕取色器绘制合同。"""

from __future__ import annotations

import shiboken6
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QBrush, QFont, QImage, QPen

from prismqml.python.providers import screen_eyedropper as eyedropper


_CONSTANTS = eyedropper.ScreenEyedropperConstants
_PAINTER_RENDER_HINT = eyedropper.QPainter.RenderHint


def _rect_tuple(rect):
    return (rect.x(), rect.y(), rect.width(), rect.height())


def _point_tuple(point):
    return (point.x(), point.y())


class _RecordingPainter:
    RenderHint = _PAINTER_RENDER_HINT
    instance = None
    failure = None

    def __init__(self, device):
        type(self).instance = self
        self.events = [("construct", device)]

    def _record(self, name, *args):
        self.events.append((name, *args))
        failure = type(self).failure
        occurrence = sum(event[0] == name for event in self.events)
        if failure is not None and failure[:2] == (name, occurrence):
            raise failure[2]

    def setRenderHint(self, hint):
        self._record("render_hint", hint)

    def setPen(self, pen):
        if isinstance(pen, QPen):
            self._record("set_pen", pen.color().name(), pen.widthF())
        else:
            self._record("set_pen_color", QColor(pen).name())

    def setBrush(self, brush):
        if isinstance(brush, QBrush):
            self._record("set_brush", brush.color().name())
        else:
            self._record("set_brush_style", brush)

    def drawRoundedRect(self, rect, x_radius, y_radius):
        self._record("draw_rounded_rect", _rect_tuple(rect), x_radius, y_radius)

    def drawImage(self, point, image):
        self._record("draw_image", _point_tuple(point), image)

    def drawLine(self, x1, y1, x2, y2):
        self._record("draw_line", x1, y1, x2, y2)

    def setFont(self, font):
        self._record(
            "set_font", font.family(), font.pixelSize(), font.weight(), font.italic()
        )

    def drawText(self, x, y, text):
        self._record("draw_text", x, y, text)


class _CapturedImage:
    def __init__(self, *, is_null=False, scaled_error=None):
        self.is_null = is_null
        self.scaled_error = scaled_error
        self.scaled_token = object()
        self.events = []

    def isNull(self):
        self.events.append(("image.is_null",))
        return self.is_null

    def scaled(self, width, height, aspect_mode, transform_mode):
        self.events.append(
            ("image.scaled", width, height, aspect_mode, transform_mode)
        )
        if self.scaled_error is not None:
            raise self.scaled_error
        return self.scaled_token


class _FontFailureWindow(eyedropper.ScreenEyedropperWindow):
    def __init__(self, error):
        self._font_error = None
        super().__init__()
        self._font_error = error

    def font(self):
        if self._font_error is not None:
            raise self._font_error
        return super().font()


def _paint_with_recorder(monkeypatch, window, failure=None):
    _RecordingPainter.instance = None
    _RecordingPainter.failure = failure
    monkeypatch.setattr(eyedropper, "QPainter", _RecordingPainter)
    window.paintEvent(None)
    return _RecordingPainter.instance.events


def _dispose_window(qapp, window):
    window.close()
    shiboken6.delete(window)
    qapp.processEvents()


def _cleanup_font_probe(qapp, window, original_app_font):
    try:
        if window is not None:
            _dispose_window(qapp, window)
    finally:
        qapp.setFont(original_app_font)


def _assert_font_values(actual, expected):
    assert actual.family() == expected.family()
    assert actual.pointSize() == expected.pointSize()
    assert actual.weight() == expected.weight()
    assert actual.italic() == expected.italic()


def _text_contrast_pixels(image, background):
    left = _CONSTANTS.PREVIEW_MARGIN + _CONSTANTS.PREVIEW_SIZE - 1
    left += _CONSTANTS.TEXT_MARGIN
    count = 0
    for y in range(2, image.height() - 2):
        for x in range(left, image.width() - 2):
            color = image.pixelColor(x, y)
            distance = sum(
                abs(channel - base)
                for channel, base in zip(color.getRgb()[:3], background.getRgb()[:3])
            )
            count += int(distance >= 30)
    return count


def _real_render_window(is_dark, captured):
    window = eyedropper.ScreenEyedropperWindow()
    window._is_dark = is_dark
    window._current_color = QColor("#12abef")
    captured_color = QColor("#2468ac")
    if captured:
        image = QImage(15, 15, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(captured_color)
        window._captured_image = image
    expected_preview = captured_color if captured else window._current_color
    return window, expected_preview


def _render_hidden_case(qapp, is_dark, captured):
    top_levels_before = set(qapp.topLevelWidgets())
    window, expected_preview = _real_render_window(is_dark, captured)
    target = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
    target.fill(Qt.GlobalColor.transparent)
    try:
        assert window.isVisible() is False
        window.render(target, QPoint())
        assert window.isVisible() is False
        expected_bg = QColor("#2d2d2d" if is_dark else "#ffffff")
        result = (target, expected_bg, expected_preview, target.pixelColor(29, 33))
    finally:
        _dispose_window(qapp, window)
    top_levels_after = set(qapp.topLevelWidgets())
    assert top_levels_after == top_levels_before
    return result


def _assert_fallback_events(events, background, border, text):
    assert [event[0] for event in events] == [
        "construct", "render_hint", "set_pen", "set_brush",
        "draw_rounded_rect", "set_brush", "draw_rounded_rect",
        "set_pen", "set_brush_style", "draw_rounded_rect",
        "set_font", "set_pen_color", "draw_text",
    ]
    assert events[1] == (
        "render_hint", eyedropper.QPainter.RenderHint.Antialiasing
    )
    assert events[2] == ("set_pen", border, 1.0)
    assert events[3] == ("set_brush", background)
    assert events[4][1:] == ((0, 0, 121, 65), 6, 6)
    assert events[5] == ("set_brush", "#12abef")
    assert events[6][1:] == ((8, 12, 42, 42), 3, 3)
    assert events[7] == ("set_pen", border, 1.0)
    assert events[8] == ("set_brush_style", Qt.BrushStyle.NoBrush)
    assert events[9][1:] == ((8, 12, 42, 42), 3, 3)
    assert events[10][2] == _CONSTANTS.FONT_SIZE
    assert events[11] == ("set_pen_color", text)
    assert events[12] == ("draw_text", 57, 37, "#12ABEF")


def _assert_captured_events(events, image):
    assert image.events == [
        ("image.is_null",),
        (
            "image.scaled", 42, 42,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        ),
    ]
    assert [event[0] for event in events[5:11]] == [
        "draw_image", "set_pen", "draw_line", "draw_line",
        "set_pen", "set_brush_style",
    ]
    assert events[1] == (
        "render_hint", eyedropper.QPainter.RenderHint.Antialiasing
    )
    assert events[5] == ("draw_image", (8, 12), image.scaled_token)
    assert events[6] == ("set_pen", "#ff0000", 1.0)
    assert events[7] == ("draw_line", 8, 33, 49, 33)
    assert events[8] == ("draw_line", 29, 12, 29, 53)
    assert events[9] == ("set_pen", "#e0e0e0", 1.0)
    assert events[10] == ("set_brush_style", Qt.BrushStyle.NoBrush)
    assert events[11][1:] == ((8, 12, 42, 42), 3, 3)
    assert events[-1] == ("draw_text", 57, 37, "#FFFFFF")


@pytest.mark.parametrize(
    ("is_dark", "background", "border", "text"),
    [
        (False, "#ffffff", "#e0e0e0", "#1a1a1a"),
        (True, "#2d2d2d", "#404040", "#ffffff"),
    ],
)
def test_fallback_paint_preserves_palette_geometry_and_order(
    qapp, monkeypatch, is_dark, background, border, text
):
    window = eyedropper.ScreenEyedropperWindow()
    window._is_dark = is_dark
    window._current_color = QColor("#12abef")
    window._captured_image = None

    try:
        events = _paint_with_recorder(monkeypatch, window)
        _assert_fallback_events(events, background, border, text)
    finally:
        _dispose_window(qapp, window)


def test_captured_paint_preserves_scaling_crosshair_and_border_order(qapp, monkeypatch):
    window = eyedropper.ScreenEyedropperWindow()
    image = _CapturedImage()
    window._captured_image = image

    try:
        events = _paint_with_recorder(monkeypatch, window)
        _assert_captured_events(events, image)
    finally:
        _dispose_window(qapp, window)


def test_null_capture_uses_fallback_without_scaling(qapp, monkeypatch):
    window = eyedropper.ScreenEyedropperWindow()
    image = _CapturedImage(is_null=True)
    window._current_color = QColor("#1268ac")
    window._captured_image = image

    try:
        events = _paint_with_recorder(monkeypatch, window)
        assert image.events == [("image.is_null",)]
        assert "draw_image" not in [event[0] for event in events]
        assert events[5] == ("set_brush", "#1268ac")
        assert events[6][1:] == ((8, 12, 42, 42), 3, 3)
    finally:
        _dispose_window(qapp, window)


@pytest.mark.parametrize(
    ("failure", "error", "captured", "expected_last"),
    [
        (("draw_rounded_rect", 1), ValueError("background"), False, "draw_rounded_rect"),
        (("draw_image", 1), ValueError("image"), True, "draw_image"),
        (("draw_line", 2), RuntimeError("crosshair"), True, "draw_line"),
        (("draw_rounded_rect", 2), KeyboardInterrupt(), False, "draw_rounded_rect"),
        (("draw_rounded_rect", 2), SystemExit(9), True, "draw_rounded_rect"),
        (("draw_text", 1), ValueError("text"), False, "draw_text"),
    ],
)
def test_paint_propagates_failures_with_ordered_partial_state(
    qapp, monkeypatch, failure, error, captured, expected_last
):
    window = eyedropper.ScreenEyedropperWindow()
    if captured:
        window._captured_image = _CapturedImage()

    try:
        with pytest.raises(type(error)) as caught:
            _paint_with_recorder(monkeypatch, window, (*failure, error))
        events = _RecordingPainter.instance.events
        assert caught.value is error
        assert events[-1][0] == expected_last
        assert "draw_text" not in [event[0] for event in events[:-1]]
    finally:
        _dispose_window(qapp, window)


def test_image_scaling_failure_propagates_before_preview_draw(qapp, monkeypatch):
    error = OSError("scale")
    image = _CapturedImage(scaled_error=error)
    window = eyedropper.ScreenEyedropperWindow()
    window._captured_image = image

    try:
        with pytest.raises(OSError) as caught:
            _paint_with_recorder(monkeypatch, window)
        assert caught.value is error
        assert image.events[-1][0] == "image.scaled"
        assert _RecordingPainter.instance.events[-1][0] == "draw_rounded_rect"
    finally:
        _dispose_window(qapp, window)


@pytest.mark.parametrize("error", [RuntimeError("font"), KeyboardInterrupt()])
def test_font_failure_propagates_after_preview_border(qapp, monkeypatch, error):
    window = _FontFailureWindow(error)
    try:
        with pytest.raises(type(error)) as caught:
            _paint_with_recorder(monkeypatch, window)
        events = _RecordingPainter.instance.events
        assert caught.value is error
        assert events[-3:] == [
            ("set_pen", "#e0e0e0", 1.0),
            ("set_brush_style", Qt.BrushStyle.NoBrush),
            ("draw_rounded_rect", (8, 12, 42, 42), 3, 3),
        ]
        assert "set_font" not in [event[0] for event in events]
        assert "draw_text" not in [event[0] for event in events]
    finally:
        _dispose_window(qapp, window)


@pytest.mark.parametrize("widget_override", [False, True])
def test_paint_honors_application_and_widget_font(qapp, monkeypatch, widget_override):
    original_app_font = QFont(qapp.font())
    app_font = QFont(original_app_font)
    app_font.setFamily("PrismQMLAppFontProbe")
    app_font.setPointSize(17)
    app_font.setWeight(QFont.Weight.DemiBold)
    app_font.setItalic(True)
    window = None
    try:
        qapp.setFont(app_font)
        window = eyedropper.ScreenEyedropperWindow()
        expected_font = QFont(app_font)
        if widget_override:
            expected_font.setFamily("PrismQMLWidgetFontProbe")
            expected_font.setPointSize(19)
            expected_font.setWeight(QFont.Weight.Bold)
            window.setFont(expected_font)
        _assert_font_values(window.font(), expected_font)
        events = _paint_with_recorder(monkeypatch, window)
        font_event = next(event for event in events if event[0] == "set_font")
        assert font_event == (
            "set_font", expected_font.family(), _CONSTANTS.FONT_SIZE,
            expected_font.weight(), expected_font.italic(),
        )
        assert window.font().pointSize() == expected_font.pointSize()
        assert window.font().pixelSize() == expected_font.pixelSize()
    finally:
        _cleanup_font_probe(qapp, window, original_app_font)
    assert qapp.font() == original_app_font


@pytest.mark.parametrize("is_dark", [False, True])
@pytest.mark.parametrize("captured", [False, True])
def test_real_hidden_widget_renders_stable_palette_and_preview_pixels(
    qapp, is_dark, captured
):
    target, expected_bg, expected_preview, center = _render_hidden_case(
        qapp, is_dark, captured
    )
    assert (target.width(), target.height()) == (
        _CONSTANTS.WINDOW_WIDTH,
        _CONSTANTS.WINDOW_HEIGHT,
    )
    assert target.pixelColor(60, 4) == expected_bg
    assert _text_contrast_pixels(target, expected_bg) >= len("#12ABEF")
    assert target.pixelColor(18, 22) == expected_preview
    if captured:
        assert center != expected_preview
        assert center.red() > expected_preview.red()
        assert center.red() > max(center.green(), center.blue())
