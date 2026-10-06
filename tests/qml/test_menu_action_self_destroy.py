# coding: utf-8
# SPDX-License-Identifier: MIT
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""A menu action must not close a menu its own handler already destroyed.

菜单动作不得关闭已被自身处理器销毁的菜单。

Real failure (Kaleidos console, 2026-10-06 19:30:01): a ContextMenu is destroyed from
inside its own action handler, then MenuContent still called ``close()`` on the dead
menu, and Qt reported ``attempted to evaluate a function in an invalid context``
followed by ``Property 'close' of object ContextMenu_QMLTYPE_nnn(...) is not a
function``. The production trigger was a delegate-owned menu rebuilt by a synchronous
model reset; here the menu is destroyed by deactivating its Loader, which removes the
dependency on delegate incubation and pins the same contract.

真实故障（Kaleidos 控制台 2026-10-06 19:30:01）：ContextMenu 在自己的动作处理器内被
销毁，MenuContent 随后仍对已销毁的菜单调用 ``close()``，Qt 打印
``attempted to evaluate a function in an invalid context``，紧接着抛出
``Property 'close' ... is not a function``。线上触发源是 delegate 菜单被同步模型重置
重建；这里改用停用 Loader 销毁菜单，去掉对 delegate 孵化的依赖，钉住同一条契约。
"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "menu-action-self-destroy.qml")
)
SCENE_SOURCE = """
import QtQuick as QQ
import PrismQML

// QtQuick stays qualified: an unqualified ``import PrismQML`` would shadow the
// QtQuick types this scene depends on.
// QtQuick 保持带前缀导入：不加前缀的 ``import PrismQML`` 会遮蔽本场景依赖的
// QtQuick 类型。
QQ.Item {
    id: root
    width: 420
    height: 320

    property int handled: 0

    QQ.Loader {
        id: host
        objectName: "menuHost"
        anchors.fill: parent
        active: true
        sourceComponent: QQ.Component {
            ContextMenu {
                autoBindRightClick: false
                Action {
                    text: "Remove row"
                    onTriggered: {
                        // Deactivating the loader destroys the menu that owns this action
                        // inside the same call stack, so MenuContent then closes a menu
                        // that no longer exists.
                        // 停用 Loader 会在同一个调用栈内销毁拥有该动作的菜单，于是
                        // MenuContent 关闭的是一个已经不存在的菜单。
                        host.active = false
                        root.handled += 1
                    }
                }
            }
        }
    }
}
"""

ACTION_TEXT = "Remove row"


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    scene = component.create(engine.rootContext())
    assert isinstance(scene, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    return engine, component, scene, warnings


def _dispose_scene(qapp, engine, component, scene) -> None:
    for obj in (scene, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def _menus(owner: QObject) -> list[QObject]:
    return [
        child
        for child in owner.findChildren(QObject)
        if child.metaObject().className().startswith("ContextMenu")
    ]


def _action(menu: QObject, text: str) -> QObject:
    matches = [
        child
        for child in menu.findChildren(QObject)
        if child.metaObject().indexOfSignal("triggered()") >= 0
        and child.property("text") == text
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in menu.findChildren(QObject)
    ]
    return matches[0]


def test_menu_action_does_not_close_after_own_menu_is_destroyed(qapp):
    """The action still runs, and no dangling close reaches the dead menu.

    动作照常生效，且不会对已销毁的菜单留下悬挂的 close 调用。
    """
    engine, component, scene, warnings = _create_scene()
    try:
        if not _wait_for(lambda: len(_menus(scene)) == 1):
            raise AssertionError(
                [
                    child.metaObject().className()
                    for child in scene.findChildren(QObject)
                ][:30]
            )
        menu = _menus(scene)[0]

        # Emitting the action signal runs the declarative handler first (it destroys the
        # menu), then MenuContent's auto-bound closure calls close().
        # 触发动作信号会先跑声明式处理器（销毁菜单），再跑 MenuContent 自动连接的闭包
        # 去调 close()。
        assert QMetaObject.invokeMethod(_action(menu, ACTION_TEXT), "triggered")
        _pump(200)

        # The action itself must still take effect; silence must not come from doing
        # nothing. 动作本身必须照常生效，不能以「什么都不做」换安静。
        assert scene.property("handled") == 1
        assert _menus(scene) == []

        dangling = [
            warning
            for warning in warnings
            if "invalid context" in warning or "is not a function" in warning
        ]
        assert not dangling, dangling
    finally:
        _dispose_scene(qapp, engine, component, scene)
