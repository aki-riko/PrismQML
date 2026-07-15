# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic capture pipeline contracts. 亚克力截图管线合同。"""

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QRect, QSize
from PySide6.QtGui import QColor, QImage, QPixmap, QWindow

from prismqml.python.window import mica_window
from acrylic_capture_test_support import (
    CAUGHT_ERRORS as _CAUGHT_ERRORS,
    PIPELINE_STAGES as _PIPELINE_STAGES,
    PROPAGATED_ERRORS as _PROPAGATED_ERRORS,
    CapturedScreen as _CapturedScreen,
    CapturedWindow as _CapturedWindow,
    GuardNumber as _GuardNumber,
    GuardWindow as _GuardWindow,
    PipelineProbe as _PipelineProbe,
    event_names as _event_names,
    make_image as _image,
    run_pipeline as _run,
)


def _pattern_image() -> QImage:
    image = QImage(16, 16, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 255))
    for y in range(6, 10):
        for x in range(6, 10):
            image.setPixelColor(x, y, QColor(255, 255, 255, 255))
    return image


def _dispose_helper(helper):
    assert shiboken6.isValid(helper)
    helper.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(helper)


@pytest.mark.parametrize(
    ("window_kind", "width", "height"),
    (("none", 20, 10), ("probe", 0, 10), ("probe", -1, 10),
     ("probe", 20, 0), ("probe", 20, -1)),
)
def test_invalid_parameters_stop_before_capture(
    monkeypatch, window_kind, width, height
):
    probe = _PipelineProbe()
    probe.install(monkeypatch)
    window = None if window_kind == "none" else probe.window

    result = mica_window.AcrylicHelper.grabAndBlur(
        probe.owner, window, 7, 5, width, height
    )

    assert result == ""
    assert probe.events == [("log.warning", "Invalid parameters for grabAndBlur")]
    assert probe.state.current_id == 0
    assert probe.signal.emitted == []


@pytest.mark.parametrize(
    ("window_value", "width_value", "height_value", "expected"),
    ((False, False, False, ["guard.window", "log.warning"]),
     (True, True, False, ["guard.window", "guard.width", "log.warning"]),
     (True, False, True,
      ["guard.window", "guard.width", "guard.height", "log.warning"])),
)
def test_invalid_guard_preserves_left_to_right_short_circuit(
    monkeypatch, window_value, width_value, height_value, expected
):
    probe = _PipelineProbe()
    probe.install(monkeypatch)
    poison = AssertionError("later guard evaluated")
    window = _GuardWindow(probe.events, window_value)
    width_error = poison if not window_value else None
    height_error = poison if (not window_value or width_value) else None
    width = _GuardNumber(probe.events, "width", width_value, width_error)
    height = _GuardNumber(probe.events, "height", height_value, height_error)

    result = mica_window.AcrylicHelper.grabAndBlur(
        probe.owner, window, 7, 5, width, height
    )

    assert result == ""
    assert _event_names(probe) == expected


@pytest.mark.parametrize("phase", ("window", "width", "height"))
@pytest.mark.parametrize("error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
def test_guard_failures_propagate_outside_try_by_identity(
    monkeypatch, phase, error_type
):
    error = error_type(f"{phase} guard failed")
    probe = _PipelineProbe()
    probe.install(monkeypatch)
    window = _GuardWindow(probe.events, error=error if phase == "window" else None)
    width = _GuardNumber(
        probe.events, "width", error=error if phase == "width" else None
    )
    height = _GuardNumber(
        probe.events, "height", error=error if phase == "height" else None
    )

    with pytest.raises(error_type) as exc_info:
        mica_window.AcrylicHelper.grabAndBlur(
            probe.owner, window, 7, 5, width, height
        )

    assert exc_info.value is error
    stop = ("window", "width", "height").index(phase) + 1
    assert _event_names(probe) == ["guard.window", "guard.width", "guard.height"][:stop]


def test_success_pipeline_preserves_order_coordinates_and_publication(monkeypatch):
    probe = _PipelineProbe()
    probe.owner._blur_radius = 23
    result = _run(probe, monkeypatch)

    assert _event_names(probe) == [*_PIPELINE_STAGES]
    grab = next(event for event in probe.events if event[0] == "screen.grab")
    blur = next(event for event in probe.events if event[0] == "blur")
    assert grab[1:] == (0, 137, -5, 20, 10)
    assert blur[1:] == (probe.source_image, 23)
    assert probe.state.current_image is probe.blurred_image
    assert probe.state.current_id == 1
    assert probe.signal.emitted == ["image://acrylic/1"]
    assert probe.logs == [("debug", "Acrylic image ready: 20x10")]
    assert result == "image://acrylic/1"


def test_primary_screen_fallback_uses_only_the_first_screen(monkeypatch):
    probe = _PipelineProbe()
    probe.use_fallback = True

    result = _run(probe, monkeypatch)

    assert result == "image://acrylic/1"
    assert _event_names(probe)[:3] == (
        ["window.screen", "application.screens", "window.x"]
    )
    grab = next(event for event in probe.events if event[0] == "screen.grab")
    assert grab[1:] == (0, 137, -5, 20, 10)


def test_missing_screen_returns_without_state_or_signal(monkeypatch):
    probe = _PipelineProbe()
    probe.use_fallback = True
    probe.no_screens = True

    result = _run(probe, monkeypatch)

    assert result == ""
    assert _event_names(probe) == [
        "window.screen", "application.screens", "log.error"
    ]
    assert probe.logs == [("error", "No screen available")]
    assert probe.state.current_id == 0
    assert probe.signal.emitted == []


def test_null_pixmap_returns_without_state_or_signal(monkeypatch):
    probe = _PipelineProbe()
    probe.null_pixmap = True

    result = _run(probe, monkeypatch)

    assert result == ""
    assert _event_names(probe) == [*_PIPELINE_STAGES[:6], "log.error"]
    assert probe.logs == [("error", "Failed to grab screen")]
    assert probe.state.current_id == 0
    assert probe.signal.emitted == []


@pytest.mark.parametrize(
    ("window_pos", "screen_origin", "local_pos", "expected"),
    (((30, 40), (-100, 50), (7, 5), (137, -5)),
     ((-400, 120), (-500, -200), (-20, 30), (80, 350))),
)
def test_screen_offsets_preserve_capture_coordinates(
    monkeypatch, window_pos, screen_origin, local_pos, expected
):
    probe = _PipelineProbe()
    probe.window_x, probe.window_y = window_pos
    probe.geometry = QRect(*screen_origin, 1920, 1080)

    _run(probe, monkeypatch, *local_pos)

    grab = next(event for event in probe.events if event[0] == "screen.grab")
    assert grab[1:] == (0, *expected, 20, 10)


def test_real_qimage_blur_publishes_through_existing_provider(qapp, monkeypatch):
    source = _pattern_image()
    screen = _CapturedScreen(QPixmap.fromImage(source), QRect(-100, 50, 800, 600))
    helper = mica_window.AcrylicHelper()
    provider = None

    try:
        helper.blurRadius = 8
        provider = helper.imageProvider
        emitted = []
        helper.imageReady.connect(emitted.append)
        monkeypatch.setattr(mica_window, "debug", lambda _message: None)
        result = helper.grabAndBlur(_CapturedWindow(screen), 7, 5, 16, 16)
        captured = provider.requestImage("1", QSize(), QSize())
        expected = mica_window._gaussian_blur_image(source, 8)
        assert result == "image://acrylic/1"
        assert emitted == [result]
        assert screen.calls == [(0, 137, -5, 16, 16)]
        assert captured == expected and captured.size() == source.size()
        assert captured.pixelColor(5, 5).red() > source.pixelColor(5, 5).red()
        assert captured.pixelColor(6, 6).red() < source.pixelColor(6, 6).red()
    finally:
        provider = None
        _dispose_helper(helper)


def test_deleted_qwindow_runtime_error_is_contained(qapp, monkeypatch):
    window = QWindow()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(window)
    helper = mica_window.AcrylicHelper()
    emitted = []
    errors = []
    helper.imageReady.connect(emitted.append)
    monkeypatch.setattr(mica_window, "error", errors.append)
    monkeypatch.setattr(
        mica_window,
        "warning",
        lambda _message: pytest.fail("deleted QWindow must pass the outer guard"),
    )

    try:
        assert helper.grabAndBlur(window, 0, 0, 20, 10) == ""
        assert len(errors) == 1
        assert errors[0].startswith("Failed to grab and blur: ")
        assert "already deleted" in errors[0]
        assert helper._image_state.image_id == 0
        assert emitted == []
    finally:
        _dispose_helper(helper)


@pytest.mark.parametrize("error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
@pytest.mark.parametrize("stage", _PIPELINE_STAGES)
def test_pipeline_stage_exceptions_preserve_boundary_and_partial_state(
    monkeypatch, stage, error_type
):
    error = error_type(f"stop at {stage}")
    probe = _PipelineProbe(stage, error)
    stage_index = _PIPELINE_STAGES.index(stage)

    if error_type in _CAUGHT_ERRORS:
        assert _run(probe, monkeypatch) == ""
        assert _event_names(probe) == [*_PIPELINE_STAGES[:stage_index + 1], "log.error"]
        assert probe.logs[-1] == ("error", f"Failed to grab and blur: {error}")
    else:
        probe.install(monkeypatch)
        with pytest.raises(error_type) as exc_info:
            mica_window.AcrylicHelper.grabAndBlur(
                probe.owner, probe.window, 7, 5, 20, 10
            )
        assert exc_info.value is error
        assert _event_names(probe) == list(_PIPELINE_STAGES[:stage_index + 1])

    state_published = stage_index > 8
    assert probe.state.current_id == int(state_published)
    assert probe.state.current_image is (
        probe.blurred_image if state_published else None
    )
    assert probe.signal.emitted == (
        ["image://acrylic/1"] if stage_index > 10 else []
    )


@pytest.mark.parametrize("error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
def test_fallback_screen_lookup_preserves_exception_boundary(monkeypatch, error_type):
    error = error_type("fallback failed")
    probe = _PipelineProbe("application.screens", error)
    probe.use_fallback = True

    if error_type in _CAUGHT_ERRORS:
        assert _run(probe, monkeypatch) == ""
        assert _event_names(probe) == [
            "window.screen", "application.screens", "log.error"
        ]
    else:
        probe.install(monkeypatch)
        with pytest.raises(error_type) as exc_info:
            mica_window.AcrylicHelper.grabAndBlur(
                probe.owner, probe.window, 7, 5, 20, 10
            )
        assert exc_info.value is error
        assert _event_names(probe) == ["window.screen", "application.screens"]

    assert probe.state.current_id == 0
    assert probe.signal.emitted == []


@pytest.mark.parametrize("error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
def test_invalid_parameter_warning_failure_propagates_by_identity(
    monkeypatch, error_type
):
    error = error_type("warning failed")
    probe = _PipelineProbe("log.warning", error)
    probe.install(monkeypatch)

    with pytest.raises(error_type) as exc_info:
        mica_window.AcrylicHelper.grabAndBlur(
            probe.owner, None, 7, 5, 20, 10
        )

    assert exc_info.value is error
    assert _event_names(probe) == ["log.warning"]
    assert probe.state.current_id == 0


@pytest.mark.parametrize("case", ("missing_screen", "null_pixmap"))
@pytest.mark.parametrize("error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
def test_early_error_log_failure_preserves_nested_boundary(
    monkeypatch, case, error_type
):
    error = error_type("error log failed")
    probe = _PipelineProbe("log.error", error)
    if case == "missing_screen":
        probe.use_fallback = probe.no_screens = True
        prefix = ["window.screen", "application.screens"]
    else:
        probe.null_pixmap = True
        prefix = list(_PIPELINE_STAGES[:6])
    probe.install(monkeypatch)

    with pytest.raises(error_type) as exc_info:
        mica_window.AcrylicHelper.grabAndBlur(
            probe.owner, probe.window, 7, 5, 20, 10
        )

    assert exc_info.value is error
    repeats = 2 if error_type in _CAUGHT_ERRORS else 1
    assert _event_names(probe) == [*prefix, *(["log.error"] * repeats)]
    assert probe.state.current_id == 0


@pytest.mark.parametrize("logger_error_type", _CAUGHT_ERRORS + _PROPAGATED_ERRORS)
def test_except_logger_failure_overrides_caught_pipeline_error(
    monkeypatch, logger_error_type
):
    original = RuntimeError("capture failed")
    logger_error = logger_error_type("logger failed")
    probe = _PipelineProbe(
        failures={"screen.grab": original, "log.error": logger_error}
    )
    probe.install(monkeypatch)

    with pytest.raises(logger_error_type) as exc_info:
        mica_window.AcrylicHelper.grabAndBlur(
            probe.owner, probe.window, 7, 5, 20, 10
        )

    assert exc_info.value is logger_error
    assert _event_names(probe) == [*_PIPELINE_STAGES[:5], "log.error"]
    assert probe.state.current_id == 0


@pytest.mark.parametrize("failure", ("missing_screen", "null_pixmap", "blur"))
def test_existing_capture_survives_prepublication_failure(monkeypatch, failure):
    probe = _PipelineProbe()
    if failure == "missing_screen":
        probe.use_fallback = probe.no_screens = True
    elif failure == "null_pixmap":
        probe.null_pixmap = True
    else:
        probe.failures["blur"] = RuntimeError("blur failed")
    old_image = _image(QColor(90, 80, 70, 255))
    probe.state.current_image = old_image
    probe.state.current_id = 6

    assert _run(probe, monkeypatch) == ""

    assert probe.state.current_image is old_image
    assert probe.state.current_id == 6
    assert probe.signal.emitted == []


def test_successive_captures_increment_id_and_publish_latest_image(monkeypatch):
    probe = _PipelineProbe()
    probe.owner._blur_radius = 11
    first = _run(probe, monkeypatch)
    latest = _image(QColor(100, 110, 120, 255))
    probe.blurred_image = latest
    probe.owner._blur_radius = 37
    second = _run(probe, monkeypatch)

    assert (first, second) == ("image://acrylic/1", "image://acrylic/2")
    assert probe.state.current_id == 2
    assert probe.state.current_image is latest
    assert probe.signal.emitted == [first, second]
    assert [event[2] for event in probe.events if event[0] == "blur"] == [11, 37]
