# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker input regressions. 颜色选择器输入区回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "_internal"
    / "ColorPickerInputs.qml"
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_component():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SOURCE_PATH)))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _descendants(root):
    result = []
    pending = list(root.children())
    if isinstance(root, QQuickItem):
        pending.extend(root.childItems())
    seen = set()
    while pending:
        child = pending.pop()
        if child in seen:
            continue
        seen.add(child)
        result.append(child)
        pending.extend(child.children())
        if isinstance(child, QQuickItem):
            pending.extend(child.childItems())
    return result


def _find_unique(root, predicate):
    matches = [child for child in _descendants(root) if predicate(child)]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def _hex_input(root):
    return _find_unique(
        root,
        lambda child: child.metaObject().indexOfProperty("maximumLength") >= 0
        and child.property("maximumLength") == 6
        and child.metaObject().indexOfProperty("selectByMouse") >= 0
        and child.metaObject().indexOfProperty("text") >= 0,
    )


def _channel_sliders(root):
    sliders = [
        child for child in _descendants(root)
        if child.metaObject().indexOfProperty("channel") >= 0
        and child.metaObject().indexOfProperty("baseColor") >= 0
        and child.metaObject().indexOfProperty("value") >= 0
    ]
    assert len(sliders) == 3
    return {slider.property("channel"): slider for slider in sliders}


def _rgb(color):
    return tuple(round(channel * 255) for channel in color.getRgbF()[:3])


def _new_visible_windows(windows_before):
    return [
        window for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _destroy(engine, component, root):
    root.deleteLater()
    del component
    engine.deleteLater()
    _pump(1)


def test_color_picker_inputs_selected_color_contract(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_component()
    try:
        root.setProperty("selectedColor", QColor("#336699"))
        _pump()
        assert root.property("_r") == 51
        assert root.property("_g") == 102
        assert root.property("_b") == 153
        assert root.property("_hex") == "336699"
        assert _hex_input(root).property("text") == "336699"
        sliders = _channel_sliders(root)
        assert [sliders[index].property("value") for index in (0, 1, 2)] == [
            51, 102, 153
        ]
        assert root.property("implicitWidth") == 260
        assert root.property("implicitHeight") > 0
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _destroy(engine, component, root)


def test_color_picker_inputs_channel_and_hex_updates(qapp):
    engine, component, root, warnings = _create_component()
    try:
        root.setProperty("selectedColor", QColor("#336699"))
        _pump()
        changed = []
        root.colorChanged.connect(changed.append)
        sliders = _channel_sliders(root)
        sliders[0].valueModified.emit(255)
        _pump()
        assert _rgb(root.property("selectedColor")) == (255, 102, 153)
        hex_input = _hex_input(root)
        hex_input.setProperty("text", "ABCDEF")
        hex_input.editingFinished.emit()
        _pump()
        assert _rgb(root.property("selectedColor")) == (171, 205, 239)
        assert len(changed) == 2
        assert warnings == []
    finally:
        _destroy(engine, component, root)


def test_color_picker_inputs_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        item for item in violations if item.rule in {"QML008", "QML009"}
    ] == []


def test_color_picker_inputs_uses_enum_mode_step():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "Enums.colorPickerMetrics.dropdownModeCycleStep" in source
    assert "colorMode + 1" not in source
    assert source.count("selectionColor: Enums.accentColor") == source.count(
        "TextInput {"
    )
    assert source.count("selectedTextColor: Enums.accentForeground") == source.count(
        "TextInput {"
    )
