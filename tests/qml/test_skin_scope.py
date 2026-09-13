# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SkinScope 局部皮肤范围运行时契约。

覆盖计划阶段 2 的门禁:
  1. 没有范围时控件继续读全局 Enums
  2. 单层范围内子树解析到该范围的 SkinContext
  3. 嵌套: 内层 Fluent 不受外层票据影响
  4. 内层 skin: "" 跟随最近父范围, 不跳到全局
  5. 范围外的页面完全不受影响
  6. Loader 动态创建的子项能找到最近范围
  7. 重挂载出范围后回退全局, 再挂回去恢复局部
  8. 显式 skinContext 优先于自动查找
  9. 无效皮肤名不改全局、只产生一次告警并回退
 10. 局部 token 与全局 token 真的不同(而不是同一个对象换个名字)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import (  # noqa: E402
    QEventLoop,
    QTimer,
    QUrl,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402

from prismqml import getSkin, register_types  # noqa: E402


NESTED_SCENE = """
import QtQuick
import PrismQML as Fluent

Item {
    objectName: "sceneRoot"
    width: 400; height: 400

    property string outerCardSkin: outerCard.effectiveSkinContext.skin
    property string innerCardSkin: innerCard.effectiveSkinContext.skin
    property string followCardSkin: followCard.effectiveSkinContext.skin
    property string globalCardSkin: globalCard.effectiveSkinContext.skin
    property bool outerCardUsesScope: outerCard.effectiveSkinContext === outerScope.context
    property bool innerCardUsesScope: innerCard.effectiveSkinContext === innerScope.context
    // 空 skin 的内层范围继承父范围的皮肤名, 但持有自己的上下文对象。
    property bool followCardUsesItsOwn: followCard.effectiveSkinContext === followScope.context
    property bool globalCardUsesEnums: globalCard.effectiveSkinContext === Fluent.Enums
    property real outerCardRadius: outerCard.effectiveSkinContext.radius.card
    property real globalCardRadius: globalCard.effectiveSkinContext.radius.card

    Fluent.SkinScope {
        id: outerScope
        objectName: "outerScope"
        skin: "vintage_ticket"
        width: 300; height: 300

        Fluent.Card { id: outerCard; objectName: "outerCard"; width: 120; height: 40 }

        Fluent.SkinScope {
            id: innerScope
            objectName: "innerScope"
            skin: "fluent"
            width: 200; height: 100
            Fluent.Card { id: innerCard; objectName: "innerCard"; width: 100; height: 30 }
        }

        Fluent.SkinScope {
            id: followScope
            objectName: "followScope"
            skin: ""
            width: 200; height: 100
            Fluent.Card { id: followCard; objectName: "followCard"; width: 100; height: 30 }
        }
    }

    Fluent.Card { id: globalCard; objectName: "globalCard"; width: 120; height: 40 }
}
"""

DYNAMIC_SCENE = """
import QtQuick
import PrismQML as Fluent

Item {
    objectName: "sceneRoot"
    width: 400; height: 400

    property bool loadedUsesScope: loader.item
        ? loader.item.effectiveSkinContext === ticketScope.context : false
    property string loadedSkin: loader.item ? loader.item.effectiveSkinContext.skin : ""
    property bool detachedUsesEnums: loader.item
        ? loader.item.effectiveSkinContext === Fluent.Enums : false
    property string detachedSkin: loader.item ? loader.item.effectiveSkinContext.skin : ""

    Item { id: outsideHost; objectName: "outsideHost"; width: 100; height: 100 }

    Fluent.SkinScope {
        id: ticketScope
        objectName: "ticketScope"
        skin: "vintage_ticket"
        width: 300; height: 300

        Loader {
            id: loader
            objectName: "loader"
            active: false
            sourceComponent: cardComponent
        }
    }

    Component {
        id: cardComponent
        Fluent.Card { objectName: "loadedCard"; width: 80; height: 30 }
    }
}
"""

EXPLICIT_SCENE = """
import QtQuick
import PrismQML as Fluent

Item {
    objectName: "sceneRoot"
    width: 200; height: 200

    property string explicitSkin: explicitCard.effectiveSkinContext.skin
    property bool explicitUsesScope: explicitCard.effectiveSkinContext === outerScope.context
    property bool explicitChildUsesScope:
        explicitChild.effectiveSkinContext === outerScope.context

    Fluent.SkinScope {
        id: outerScope
        objectName: "outerScope"
        skin: "fluent"
        width: 150; height: 150
        Fluent.SkinScope {
            id: innerScope
            objectName: "innerScope"
            skin: "vintage_ticket"
            width: 100; height: 100
            Fluent.Card {
                id: explicitCard
                objectName: "explicitCard"
                skinContext: outerScope.context
                width: 60; height: 20

                Fluent.Button {
                    id: explicitChild
                    objectName: "explicitChild"
                    text: "Child"
                }
            }
        }
    }
}
"""

INVALID_SCENE = """
import QtQuick
import PrismQML as Fluent

Item {
    objectName: "sceneRoot"
    width: 200; height: 200

    property string resolvedSkin: badScope.resolvedSkin
    property string cardSkin: badCard.effectiveSkinContext.skin
    property bool cardUsesScope: badCard.effectiveSkinContext === badScope.context

    Fluent.SkinScope {
        id: badScope
        objectName: "badScope"
        skin: "not_a_skin"
        width: 150; height: 150
        Fluent.Card { id: badCard; objectName: "badCard"; width: 60; height: 20 }
    }
}
"""

IMPLICIT_SIZE_SCENE = """
import QtQuick
import PrismQML as Fluent

Item {
    width: 400
    height: 200

    property real scopeImplicitWidth: scope.implicitWidth
    property real scopeImplicitHeight: scope.implicitHeight

    Fluent.SkinScope {
        id: scope
        skin: "vintage_ticket"

        Fluent.Card {
            width: 180
            height: 72
        }
    }
}
"""


def _build(engine, qml: str):
    component = QQmlComponent(engine)
    component.setData(qml.encode("utf-8"), QUrl("inline:/skin-scope"))
    # Compilation is asynchronous; wait for Ready before creating.
    # 编译是异步的，创建前必须等到 Ready。
    if component.status() == QQmlComponent.Status.Loading:
        loop = QEventLoop()
        component.statusChanged.connect(lambda _status: loop.quit())
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
    if component.isError():
        raise AssertionError([e.toString() for e in component.errors()])
    obj = component.create(engine.rootContext())
    if obj is None:
        raise AssertionError([e.toString() for e in component.errors()])
    return component, obj


@pytest.fixture()
def engine(qapp):
    eng = QQmlApplicationEngine()
    eng.addImportPath(str(ROOT / "prismqml"))
    register_types(eng)
    yield eng
    eng.deleteLater()


def _find(obj, name):
    found = obj.findChild(object, name)
    assert found is not None, f"未找到对象: {name}"
    return found


def test_nested_scopes_resolve_to_nearest_context(engine):
    _, root = _build(engine, NESTED_SCENE)

    assert root.property("outerCardSkin") == "vintage_ticket"
    assert root.property("innerCardSkin") == "fluent"
    # 内层 skin: "" 跟随最近父范围(票据), 而不是直接跳回全局。
    assert root.property("followCardSkin") == "vintage_ticket"
    assert root.property("outerCardUsesScope") is True
    assert root.property("innerCardUsesScope") is True
    assert root.property("followCardUsesItsOwn") is True


def test_widgets_outside_any_scope_keep_global_enums(engine):
    _, root = _build(engine, NESTED_SCENE)

    assert root.property("globalCardUsesEnums") is True
    assert root.property("globalCardSkin") == getSkin().value


def test_local_tokens_really_differ_from_global(engine):
    _, root = _build(engine, NESTED_SCENE)

    # 票据皮肤的通用圆角为 0, Fluent 卡片圆角为 5。两者不能相等。
    assert root.property("outerCardRadius") == 0
    assert root.property("globalCardRadius") > 0


def test_loader_children_resolve_scope_and_follow_reparenting(engine):
    _, root = _build(engine, DYNAMIC_SCENE)

    loader = _find(root, "loader")
    loader.setProperty("active", True)
    assert root.property("loadedUsesScope") is True
    assert root.property("loadedSkin") == "vintage_ticket"

    # 移出范围后应回退到全局 Enums。
    outside = _find(root, "outsideHost")
    loaded = _find(root, "loadedCard")
    loaded.setProperty("parent", outside)
    assert root.property("detachedUsesEnums") is True
    assert root.property("detachedSkin") == getSkin().value

    # 再挂回范围内应重新解析到票据上下文。
    scope_content = _find(root, "_skinScopeContent")
    loaded.setProperty("parent", scope_content)
    assert root.property("detachedUsesEnums") is False
    assert root.property("detachedSkin") == "vintage_ticket"


def test_explicit_skin_context_wins_over_nearest_scope(engine):
    _, root = _build(engine, EXPLICIT_SCENE)

    # 卡片位于票据范围内, 但显式指定了外层 Fluent 范围。
    assert root.property("explicitSkin") == "fluent"
    assert root.property("explicitUsesScope") is True
    assert root.property("explicitChildUsesScope") is True


def test_invalid_skin_name_falls_back_and_warns_once(engine):
    # console.warn goes through the Qt message handler, not engine.warnings.
    # console.warn 走 Qt 消息处理器，不走 engine.warnings。
    messages: list[str] = []

    def _handler(mode, context, message):
        if mode == QtMsgType.QtWarningMsg:
            messages.append(message)

    previous = qInstallMessageHandler(_handler)
    try:
        _, root = _build(engine, INVALID_SCENE)
    finally:
        qInstallMessageHandler(previous)

    global_skin = getSkin().value
    assert root.property("resolvedSkin") == global_skin
    assert root.property("cardSkin") == global_skin
    assert root.property("cardUsesScope") is True
    # 全局皮肤没有被写坏。
    assert getSkin().value == global_skin

    matching = [m for m in messages if "not_a_skin" in m]
    assert len(matching) == 1, f"应只告警一次, 实际: {matching}"


def test_scope_reports_its_content_implicit_size(engine):
    _, root = _build(engine, IMPLICIT_SIZE_SCENE)

    assert root.property("scopeImplicitWidth") == 180
    assert root.property("scopeImplicitHeight") == 72
