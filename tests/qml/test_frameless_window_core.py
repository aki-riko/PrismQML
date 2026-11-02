# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""FramelessWindowCore 轻量无边框窗口基类契约。

这个基类存在的理由只有一个: 启动期窗口不该为了一个圆角面板付出 WindowsCore
整套应用窗口镶边的创建成本。所以本文件锁的是**成本**和**最小语义**,
不是外观细节 —— 外观由消费方自己决定。
"""

from pathlib import Path, PurePosixPath

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from scripts.qml_conventions import scan_source_text

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "FramelessWindowCore.qml"
QMLDIR_PATH = ROOT / "prismqml" / "PrismQML" / "qmldir"

_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Fluent.FramelessWindowCore {
    id: win
    width: 400
    height: 300
    visible: false

    property int clickCount: 0
    property int closeRequestedCount: 0
    property int nativeCloseAcceptedCount: 0

    onCloseRequested: closeRequestedCount++
    onNativeCloseAccepted: nativeCloseAcceptedCount++

    Rectangle {
        objectName: "clickTarget"
        width: 120
        height: 50
        color: "orange"

        MouseArea {
            anchors.fill: parent
            onClicked: win.clickCount++
        }
    }
}
"""

_WINDOWS_CORE_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Fluent.WindowsCore {
    width: 400
    height: 300
    visible: false
}
"""


def _pump(milliseconds: int = 120) -> None:
    from PySide6.QtCore import QElapsedTimer

    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < milliseconds:
        QCoreApplication.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "frameless_window_core-runtime.qml"))


def _create(qml_engine, source: bytes):
    component = QQmlComponent(qml_engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create()
    assert instance is not None, [error.toString() for error in component.errors()]
    # setData() 的组件由本作用域持有；一旦它被回收，create() 出的窗口会跟着销毁。
    # 把引用挂在实例上，让它与窗口同寿。
    instance._probe_component = component
    return instance


def _object_count(root) -> int:
    return len(root.findChildren(object))


def test_component_is_registered_in_qmldir():
    """实例化前必须能被 `import PrismQML` 解析到，否则消费方直接启动失败。"""
    text = QMLDIR_PATH.read_text(encoding="utf-8")
    assert "FramelessWindowCore FramelessWindowCore.qml" in text


def test_source_passes_convention_scan():
    """组件自身必须满足仓库的 QML 规范扫描（成员顺序/主题色/import 形式）。"""
    text = SOURCE_PATH.read_text(encoding="utf-8")
    violations = scan_source_text(text, PurePosixPath(SOURCE_PATH.as_posix()))
    assert violations == [], violations


def test_declares_no_engine_only_imports():
    """轻量基类不得引入 QtQuick.Controls 或布局模块，避免把成本带回来。"""
    text = SOURCE_PATH.read_text(encoding="utf-8")
    assert "QtQuick.Controls" not in text
    assert "Qt5Compat" not in text


def test_creates_far_fewer_objects_than_windows_core(qml_engine):
    """核心承诺：同一尺寸下对象数必须显著少于 WindowsCore。

    这条是防回流门禁 —— 任何人往这个基类里塞回标题栏/阴影/动画助手，
    都会让启动期窗口重新变重。
    """
    light = _create(qml_engine, _SCENE)
    light.resize(400, 300)
    light.show()
    _pump()

    heavy = _create(qml_engine, _WINDOWS_CORE_SCENE)
    heavy.resize(400, 300)
    heavy.show()
    _pump()

    light_count = _object_count(light)
    heavy_count = _object_count(heavy)

    heavy.close()
    heavy.deleteLater()
    _pump(40)

    assert light_count < heavy_count // 3, (light_count, heavy_count)

    light.close()
    light.deleteLater()
    _pump(40)


def test_default_property_parents_content_into_content_area(qml_engine):
    """默认属性必须把外部内容挂进 panel，而不是散在 Window 根下。"""
    window = _create(qml_engine, _SCENE)
    window.resize(400, 300)
    window.show()
    _pump()

    target = None
    for child in window.findChildren(object):
        if child.objectName() == "clickTarget":
            target = child
            break

    assert target is not None
    parent = target.parent()
    assert parent is not None
    # 内容挂进 contentArea（其父是圆角面板 Rectangle），不是窗口 contentItem 根。
    assert shiboken6.isValid(target)
    assert parent is not window.contentItem()

    window.close()
    window.deleteLater()
    _pump(40)


def test_content_receives_clicks_through_drag_layer(qml_engine):
    """拖动层不得吞掉内容区控件的点击。"""
    window = _create(qml_engine, _SCENE)
    window.resize(400, 300)
    window.show()
    _pump()

    target = None
    for child in window.findChildren(object):
        if child.objectName() == "clickTarget":
            target = child
            break
    assert target is not None

    item = shiboken6.wrapInstance(shiboken6.getCppPointer(target)[0], QQuickItem)
    point = item.mapToScene(QPointF(60, 25))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point.toPoint(),
    )
    _pump(60)

    assert window.property("clickCount") == 1

    window.close()
    window.deleteLater()
    _pump(40)


def test_request_close_emits_both_signals_once(qml_engine):
    """程序化关闭必须走与原生关闭相同的否决流程，两个信号各来一次。"""
    window = _create(qml_engine, _SCENE)
    window.resize(400, 300)
    window.show()
    _pump()

    window.metaObject().invokeMethod(window, "requestClose")
    _pump(60)

    assert window.property("closeRequestedCount") == 1
    assert window.property("nativeCloseAcceptedCount") == 1

    window.close()
    window.deleteLater()
    _pump(40)


def test_close_request_can_be_vetoed(qml_engine):
    """closeRequestAccepted=false 必须真的把窗口留下。"""
    source = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Fluent.FramelessWindowCore {
    id: win
    width: 300
    height: 200
    visible: false
    property int acceptedCount: 0
    onCloseRequested: closeRequestAccepted = false

    Timer {
        running: true
        interval: 1
        onTriggered: win.requestClose()
    }
}
"""
    window = _create(qml_engine, source)
    window.resize(300, 200)
    window.show()
    _pump(200)

    assert window.property("acceptedCount") == 0
    assert window.property("visible") is True

    window.close()
    window.deleteLater()
    _pump(40)


def test_windows_core_migration_shims_parse_without_effect(qml_engine):
    """从 WindowsCore 迁来的 `shadowMode` / `titleBarHeight` 等写法必须能解析。

    这些属性在本类里不产生视觉效果，只是让迁移源码原样通过 —— 但也不能
    悄悄改变布局：`titleBarHeight` 写多少都不该吃掉内容高度。
    """
    source = b"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Fluent.FramelessWindowCore {
    id: win
    width: 400
    height: 300
    visible: false
    shadowMode: Fluent.Enums.windowShadow.mode_none
    titleBarHeight: 48
    windowTitle: ""
    titleBarPosition: Fluent.Enums.windowType.title_bar_top
    shadowSize: 16

    Rectangle {
        objectName: "fullBleedContent"
        anchors.fill: parent
        color: "green"
    }
}
"""
    window = _create(qml_engine, source)
    window.resize(400, 300)
    window.show()
    _pump(150)

    content = None
    for child in window.findChildren(object):
        if child.objectName() == "fullBleedContent":
            content = child
            break

    assert content is not None
    item = shiboken6.wrapInstance(shiboken6.getCppPointer(content)[0], QQuickItem)
    # 没有标题栏占位：内容必须铺满整窗（允许 1px 边框容差）。
    assert item.width() >= 398, item.width()
    assert item.height() >= 298, item.height()

    window.close()
    window.deleteLater()
    _pump(40)


def test_resize_handles_absent_when_not_resizable(qml_engine):
    """resizable=false 时不得创建缩放手柄对象。"""
    def count_with(resizable: bool) -> int:
        source = f"""
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Fluent.FramelessWindowCore {{
    width: 300
    height: 200
    visible: false
    resizable: {str(resizable).lower()}
}}
""".encode()
        window = _create(qml_engine, source)
        window.resize(300, 200)
        window.show()
        _pump(120)
        total = _object_count(window)
        window.close()
        window.deleteLater()
        _pump(40)
        return total

    with_handles = count_with(True)
    without_handles = count_with(False)
    assert without_handles < with_handles, (without_handles, with_handles)
