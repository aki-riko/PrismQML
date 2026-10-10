# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NumberBox expression input and validation mode contracts.

NumberBox 表达式输入与校验模式合同。
"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "number-box-expression.qml")
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"
    width: 360
    height: 200
    visible: true

    readonly property int overridden: Enums.input.validation_invalid_input_overridden
    readonly property int disabled: Enums.input.validation_invalid_input_disabled

    SpinBoxCore {
        id: numberBox
        objectName: "numberBox"
        x: 20
        y: 20
        width: 200
        height: 32
        minimum: 0
        maximum: 10
        decimals: 2
        value: 4
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _create_scene():
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
    _pump(60)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(1)


def _box(window) -> QQuickItem:
    item = window.findChild(QQuickItem, "numberBox")
    assert item is not None
    return item


def _editor(box: QQuickItem) -> QQuickItem:
    matches = [
        child
        for child in box.findChildren(QQuickItem)
        if child.metaObject().indexOfProperty("validator") >= 0
        and child.metaObject().indexOfProperty("selectByMouse") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _commit(window, box: QQuickItem, text: str) -> None:
    """Focus the field, replace its text and commit with Return.

    聚焦输入框, 替换文本并用回车提交。
    """
    editor = _editor(box)
    assert QMetaObject.invokeMethod(editor, "forceActiveFocus")
    assert _wait_for(lambda: editor.property("activeFocus")), "editor never focused"
    editor.setProperty("text", text)
    _pump(40)
    QTest.keyClick(window, Qt.Key.Key_Return)
    _pump(60)


def test_defaults_keep_the_classic_number_box(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        assert box.property("acceptsExpression") is False
        assert box.property("validationMode") == window.property("overridden")
        assert box.property("displayValue") == "4.00"

        # A plain number still commits 普通数字仍然提交
        _commit(window, box, "7")
        assert box.property("value") == 7
        assert box.property("displayValue") == "7.00"

        # Out-of-range input is clamped, exactly as before 越界输入照旧钳制
        _commit(window, box, "99")
        assert box.property("value") == 10
        assert box.property("displayValue") == "10.00"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_expression_mode_relaxes_the_input_validator(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        editor = _editor(box)
        classic = editor.property("validator").metaObject().className()
        assert "DoubleValidator" in classic

        box.setProperty("acceptsExpression", True)
        _pump(40)
        relaxed = editor.property("validator").metaObject().className()
        assert relaxed != classic
        assert "RegularExpressionValidator" in relaxed

        box.setProperty("acceptsExpression", False)
        _pump(40)
        assert editor.property("validator").metaObject().className() == classic
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_expression_input_is_evaluated(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        box.setProperty("acceptsExpression", True)
        _pump(40)

        _commit(window, box, "2*3+1")
        assert box.property("value") == 7
        assert box.property("displayValue") == "7.00"

        _commit(window, box, "(1+1)*2")
        assert box.property("value") == 4

        _commit(window, box, "1/4")
        assert box.property("value") == 0.25
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_expression_result_is_clamped_by_default(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        box.setProperty("acceptsExpression", True)
        _pump(40)

        _commit(window, box, "2*9")
        assert box.property("value") == 10
        assert box.property("displayValue") == "10.00"

        # A malformed expression keeps the previous value 非法表达式保留上一次的值
        _commit(window, box, "2*")
        assert box.property("value") == 10
        assert box.property("displayValue") == "10.00"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_validation_disabled_rejects_out_of_range_input(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        box.setProperty("validationMode", window.property("disabled"))
        _pump(40)

        _commit(window, box, "99")
        assert box.property("value") == 4
        assert box.property("displayValue") == "4.00"

        _commit(window, box, "9")
        assert box.property("value") == 9
        assert box.property("displayValue") == "9.00"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_validation_disabled_rejects_out_of_range_expression(qapp) -> None:
    engine, component, window, warnings = _create_scene()
    try:
        box = _box(window)
        box.setProperty("acceptsExpression", True)
        box.setProperty("validationMode", window.property("disabled"))
        _pump(40)

        _commit(window, box, "3*4")
        assert box.property("value") == 4
        assert box.property("displayValue") == "4.00"

        _commit(window, box, "3*2")
        assert box.property("value") == 6
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
