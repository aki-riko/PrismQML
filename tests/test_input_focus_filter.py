# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""App input focus regression tests. App 输入焦点回归测试。"""

import os
import runpy
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS = runpy.run_path(str(REPO_ROOT / "scripts" / "test_process.py"))
prepare_automated_test_process = TEST_PROCESS["prepare_automated_test_process"]

prepare_automated_test_process()

CHILD_ARGUMENT = "--input-focus-child"
QML = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    id: root
    visible: true
    width: 420
    height: 260
    property int commitCount: 0
    property int secondCommitCount: 0
    property int targetClickCount: 0

    Fluent.Card {
        id: card
        objectName: "focusCard"
        anchors.fill: parent
        anchors.margins: 20

        Fluent.LineEdit {
            id: edit
            objectName: "focusEdit"
            x: 24
            y: 24
            width: 260
            text: "gpt-5.6-sol"
            onEditingFinished: root.commitCount += 1
        }

        Fluent.LineEdit {
            id: secondEdit
            objectName: "focusSecondEdit"
            x: 24
            y: 80
            width: 260
            text: "second"
            onEditingFinished: root.secondCommitCount += 1
        }

        TextEdit {
            id: textEdit
            objectName: "focusTextEdit"
            x: 24
            y: 136
            width: 260
            height: 40
            text: "multiline"
            activeFocusOnPress: true
        }

        MouseArea {
            id: target
            objectName: "focusTarget"
            x: card.width - 80
            y: 30
            width: 50
            height: 50
            onClicked: root.targetClickCount += 1
        }
    }
}
"""


def _visual_items(item):
    """Yield the complete QQuickItem visual tree. 遍历完整视觉树。"""
    stack = [item]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(current.childItems())


def _scene_point(item, x, y):
    """Map one item-local point into window coordinates. 转换到窗口坐标。"""
    from PySide6.QtCore import QPoint, QPointF

    point = item.mapToScene(QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _create_focus_window(app):
    """Create the real Card and LineEdit test window. 创建真实控件窗口。"""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtTest import QTest
    import prismqml

    engine = app.engine
    engine.addImportPath(str(Path(prismqml.__file__).resolve().parent))
    component = QQmlComponent(engine)
    component.setData(QML, QUrl("inline:input-focus-regression.qml"))
    for _ in range(100):
        if component.status() != QQmlComponent.Status.Loading:
            break
        QTest.qWait(20)
    assert not component.isError(), " | ".join(
        error.toString() for error in component.errors()
    )
    window = component.create()
    assert window is not None
    QTest.qWait(150)
    return component, window


def _find_focus_items(window):
    """Return the real focus targets. 返回真实焦点目标。"""
    items = list(_visual_items(window.contentItem()))
    card = next(item for item in items if item.objectName() == "focusCard")
    edit = next(item for item in items if item.objectName() == "focusEdit")
    second_edit = next(item for item in items if item.objectName() == "focusSecondEdit")
    text_edit = next(item for item in items if item.objectName() == "focusTextEdit")
    target = next(item for item in items if item.objectName() == "focusTarget")
    first_input = next(
        item for item in _visual_items(edit) if item.inherits("QQuickTextInput")
    )
    second_input = next(
        item for item in _visual_items(second_edit) if item.inherits("QQuickTextInput")
    )
    return card, first_input, second_input, text_edit, target


def _verify_click_flow(window, card, text_input) -> None:
    """Verify inside clicks keep focus and card blank clicks blur. 验证点击链。"""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtTest import QTest

    input_point = _scene_point(
        text_input, text_input.width() / 2, text_input.height() / 2
    )
    blank_point = _scene_point(card, card.width() - 30, card.height() - 30)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, input_point
    )
    QTest.qWait(50)
    assert QGuiApplication.focusObject().inherits("QQuickTextInput")
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, input_point
    )
    QTest.qWait(50)
    assert QGuiApplication.focusObject().inherits("QQuickTextInput")
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, blank_point
    )
    QTest.qWait(50)
    focus_object = QGuiApplication.focusObject()
    assert not (focus_object and focus_object.inherits("QQuickTextInput"))
    assert window.property("commitCount") == 1


def _click_item(window, item) -> None:
    """Click the center of one visual item. 点击视觉项中心。"""
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    point = _scene_point(item, item.width() / 2, item.height() / 2)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    QTest.qWait(50)


def _verify_cross_input_and_delivery(window, second_input, text_edit, target) -> None:
    """Verify input switching and downstream delivery. 验证切换与继续投递。"""
    from PySide6.QtGui import QGuiApplication

    _click_item(window, second_input)
    assert QGuiApplication.focusObject() is second_input
    _click_item(window, text_edit)
    assert QGuiApplication.focusObject() is text_edit
    assert window.property("secondCommitCount") == 1
    _click_item(window, target)
    focus_object = QGuiApplication.focusObject()
    assert not (
        focus_object
        and (
            focus_object.inherits("QQuickTextInput")
            or focus_object.inherits("QQuickTextEdit")
        )
    )
    assert window.property("targetClickCount") == 1


def _run_child() -> int:
    """Run the regression in a fresh QApplication process. 在全新进程中验证。"""
    sys.path.insert(0, str(REPO_ROOT))
    from prismqml import App
    import prismqml.python.core.input_focus_filter as focus_filter_module

    app = App([])
    installed_filter = focus_filter_module._filter
    assert installed_filter is not None
    assert installed_filter.parent() == app.qapp
    component, window = _create_focus_window(app)
    card, first_input, second_input, text_edit, target = _find_focus_items(window)
    _verify_click_flow(window, card, first_input)
    _verify_cross_input_and_delivery(window, second_input, text_edit, target)
    window.close()
    del component
    App._reset()
    assert focus_filter_module._filter is None
    print("INPUT_FOCUS_FILTER_OK")
    return 0


def test_app_installs_filter_and_blurs_card_click() -> None:
    """Verify App auto-installs the filter with a real click. 验证自动安装与真实点击。"""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), CHILD_ARGUMENT],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    assert completed.returncode == 0, output
    assert "INPUT_FOCUS_FILTER_OK" in completed.stdout


if __name__ == "__main__" and CHILD_ARGUMENT in sys.argv:
    raise SystemExit(_run_child())
