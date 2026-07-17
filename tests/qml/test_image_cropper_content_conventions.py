# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ImageCropperContent interaction contracts. 图片裁剪内容交互合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QRectF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication, QImage, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "_internal"
    / "ImageCropperContent.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "image-cropper-content-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 900
    height: 700
    visible: true

    ImageCropper {
        objectName: "cropper"
        type: Enums.imageCropper.type_overlay
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _has_property(item: QQuickItem, name: str) -> bool:
    return item.metaObject().indexOfProperty(name) >= 0


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _window_point(window: QQuickWindow, item: QQuickItem, x: float, y: float):
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _center(window: QQuickWindow, item: QQuickItem) -> QPoint:
    return _window_point(window, item, item.width() / 2, item.height() / 2)


def _drag(window: QQuickWindow, start: QPoint, target: QPoint) -> None:
    middle = QPoint((start.x() + target.x()) // 2, (start.y() + target.y()) // 2)
    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, middle, 20)
    QTest.mouseMove(window, target, 20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    _pump()


def _send_wheel(window: QQuickWindow, point: QPoint, delta: int) -> None:
    event = QWheelEvent(
        QPointF(point),
        QPointF(window.mapToGlobal(point)),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QCoreApplication.sendEvent(window, event)
    _pump()


def _create_image(path: Path) -> QUrl:
    image = QImage(240, 120, QImage.Format.Format_ARGB32)
    image.fill(QColor("#4a90e2"))
    assert image.save(str(path), "PNG")
    return QUrl.fromLocalFile(str(path))


def _create_scene(image_url: QUrl):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    cropper = window.findChild(QQuickItem, "cropper")
    assert cropper is not None
    cropper.setProperty("source", image_url)
    cropper.open()
    assert _wait_for(lambda: _content(cropper) is not None)
    content = _content(cropper)
    assert content is not None
    assert _wait_for(
        lambda: content.property("_imgW") > 0 and content.property("_imgH") > 0
    )
    assert _wait_for(lambda: _crop_area(content) is not None)
    return engine, component, window, cropper, content, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _content(cropper: QQuickItem):
    matches = [
        item
        for item in _visual_descendants(cropper.window().contentItem())
        if _has_property(item, "_imgW")
        and _has_property(item, "imageRotation")
        and _has_property(item, "cropRect")
    ]
    assert len(matches) <= 1
    return matches[0] if matches else None


def _crop_area(content: QQuickItem):
    matches = [
        item
        for item in content.childItems()
        if any(
            child.metaObject().className().startswith("QQuickMouseArea")
            for child in item.childItems()
        )
    ]
    assert len(matches) <= 1
    return matches[0] if matches else None


def _handles(crop_area: QQuickItem) -> list[QQuickItem]:
    matches = [
        item
        for item in _visual_descendants(crop_area)
        if item.metaObject().className().startswith("QQuickRectangle")
        and 0 < item.width() <= 32
        and item.width() == pytest.approx(item.height())
        and any(
            child.metaObject().className().startswith("QQuickMouseArea")
            for child in item.childItems()
        )
    ]
    assert len(matches) == 4
    return sorted(matches, key=lambda item: (round(item.y()), round(item.x())))


def _toolbar_buttons(content: QQuickItem) -> list[QQuickItem]:
    panel = content.parentItem()
    matches = [
        item
        for item in _visual_descendants(panel)
        if _has_property(item, "icon")
        and _has_property(item, "style")
        and _has_property(item, "shape")
    ]
    assert len(matches) == 4
    return sorted(
        matches,
        key=lambda item: item.mapToItem(panel, QPointF()).x(),
    )


def _assert_rect_inside_image(content: QQuickItem, rect: QRectF) -> None:
    img_w = content.property("_imgW")
    img_h = content.property("_imgH")
    max_size = content.property("_maxSize")
    is_circle = content.property("_isCircle")
    pixel_w = rect.width() * (max_size if is_circle else img_w)
    pixel_h = rect.width() * max_size if is_circle else rect.height() * img_h
    assert rect.x() >= -1e-6
    assert rect.y() >= -1e-6
    assert rect.x() + pixel_w / img_w <= 1 + 1e-6
    assert rect.y() + pixel_h / img_h <= 1 + 1e-6


def test_image_cropper_content_move_wheel_toolbar_and_signal_contracts(
    qapp, tmp_path
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene(_create_image(tmp_path / "crop-source.png"))
    engine, component, window, cropper, content, warnings = scene
    updates = []
    content.cropRectUpdated.connect(updates.append)
    try:
        crop_area = _crop_area(content)
        assert crop_area is not None
        assert content.property("_imgW") / content.property("_imgH") == pytest.approx(2)
        assert cropper.property("cropRect") == QRectF(0.1, 0.1, 0.8, 0.8)

        buttons = _toolbar_buttons(content)
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_center(window, buttons[1]))
        assert _wait_for(lambda: content.property("imageRotation") == pytest.approx(90))
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=_center(window, buttons[2]))
        assert _wait_for(lambda: bool(content.property("imageMirror")))

        start = _center(window, crop_area)
        target = QPoint(start.x() + 500, start.y() + 300)
        _drag(window, start, target)
        moved = cropper.property("cropRect")
        assert moved == QRectF(0.2, 0.2, 0.8, 0.8)
        assert updates[-1] == moved
        _assert_rect_inside_image(content, moved)

        content.initDefaultCropRect()
        assert _wait_for(
            lambda: cropper.property("cropRect") == QRectF(0.1, 0.1, 0.8, 0.8)
        )
        crop_area = _crop_area(content)
        assert crop_area is not None
        center_before = QPointF(
            crop_area.x() + crop_area.width() / 2,
            crop_area.y() + crop_area.height() / 2,
        )
        _send_wheel(window, _center(window, crop_area), -120)
        zoomed = cropper.property("cropRect")
        assert (zoomed.width(), zoomed.height()) == pytest.approx((0.72, 0.72))
        center_after = QPointF(
            crop_area.x() + crop_area.width() / 2,
            crop_area.y() + crop_area.height() / 2,
        )
        assert center_after == center_before
        assert updates[-1] == zoomed
        _assert_rect_inside_image(content, zoomed)

        for _ in range(30):
            _send_wheel(window, _center(window, crop_area), -120)
        minimum = cropper.property("cropRect")
        rendered_width = minimum.width() * content.property("_imgW")
        rendered_height = minimum.height() * content.property("_imgH")
        assert rendered_width == pytest.approx(60)
        assert rendered_height == pytest.approx(60)
        _assert_rect_inside_image(content, minimum)

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize(
    ("handle_index", "offset"),
    [
        (0, QPoint(32, 18)),
        (1, QPoint(32, 18)),
        (2, QPoint(32, 18)),
        (3, QPoint(32, 18)),
    ],
)
def test_image_cropper_content_all_rectangle_handles_resize_within_bounds(
    qapp, tmp_path, handle_index, offset
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene(_create_image(tmp_path / "crop-source.png"))
    engine, component, window, cropper, content, warnings = scene
    try:
        start_rect = QRectF(0.2, 0.2, 0.6, 0.6)
        cropper.setProperty("cropRect", start_rect)
        assert _wait_for(lambda: cropper.property("cropRect") == start_rect)
        crop_area = _crop_area(content)
        assert crop_area is not None
        handle = _handles(crop_area)[handle_index]
        start = _center(window, handle)
        _drag(window, start, start + offset)
        resized = cropper.property("cropRect")
        assert resized != start_rect
        _assert_rect_inside_image(content, resized)
        if handle_index == 3:
            img_w = content.property("_imgW")
            img_h = content.property("_imgH")
            width_delta = (resized.width() - start_rect.width()) * img_w
            height_delta = (resized.height() - start_rect.height()) * img_h
            assert width_delta > 0
            assert height_delta > 0
            assert width_delta != pytest.approx(height_delta, abs=2)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_image_cropper_content_circle_handles_preserve_square_and_bounds(
    qapp, tmp_path
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene(_create_image(tmp_path / "crop-source.png"))
    engine, component, window, cropper, content, warnings = scene
    try:
        cropper.setProperty("cropShape", 1)
        start_rect = QRectF(0.2, 0.2, 0.5, 0.5)
        cropper.setProperty("cropRect", start_rect)
        assert _wait_for(lambda: bool(content.property("_isCircle")))
        crop_area = _crop_area(content)
        assert crop_area is not None
        assert crop_area.width() == pytest.approx(crop_area.height())
        for handle_index, offset in enumerate(
            (QPoint(24, 24), QPoint(24, 24), QPoint(24, 24), QPoint(24, 24))
        ):
            cropper.setProperty("cropRect", start_rect)
            _pump()
            crop_area = _crop_area(content)
            handle = _handles(crop_area)[handle_index]
            start = _center(window, handle)
            _drag(window, start, start + offset)
            resized = cropper.property("cropRect")
            assert resized != start_rect
            assert resized.width() == pytest.approx(resized.height())
            assert crop_area.width() == pytest.approx(crop_area.height())
            _assert_rect_inside_image(content, resized)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_image_cropper_content_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
