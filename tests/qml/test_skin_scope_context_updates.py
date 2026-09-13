# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""局部皮肤在祖先重挂载和上下文桥切换后的真实 QML 回归。"""

import pytest

from test_skin_scope import ROOT, _build, _find, engine  # noqa: F401


CONSUMERS = (
    "Fluent.Button",
    "Fluent.Label",
    "Fluent.MenuDelegate",
    "Fluent.TicketPaper",
    "Internal.ContentFrame",
)
SCENE = """
import QtQuick
import PrismQML as Fluent
import "__INTERNAL__" as Internal

Item {
    width: 400; height: 300
    property string childSkin: consumer.effectiveSkinContext.skin
    property var fluentContext: fluent.context
    property var ticketContext: ticket.context
    Fluent.SkinScope {
        id: fluent
        skin: "fluent"
        Item { objectName: "outside"; width: 200; height: 100 }
    }
    Fluent.SkinScope {
        id: ticket
        skin: "vintage_ticket"
        Fluent.Widget {
            objectName: "bridge"
            width: 200; height: 100
            __CONSUMER__ {
                id: consumer
                width: 80; height: 30
                __REQUIRED__
            }
        }
    }
}
"""


def _scene(consumer):
    required = (
        "backgroundColor: Fluent.Enums.cardColor; cornerRadius: Fluent.Enums.radius.large"
        if consumer == "Internal.ContentFrame" else ""
    )
    return (SCENE.replace("__INTERNAL__", (ROOT / "prismqml/PrismQML/_internal").as_uri())
            .replace("__CONSUMER__", consumer).replace("__REQUIRED__", required))


@pytest.fixture(autouse=True)
def _check_qml_warnings(engine):
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    yield
    assert warnings == []


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_descendant_follows_ancestor_reparenting(engine, consumer):
    component, root = _build(engine, _scene(consumer))
    bridge = _find(root, "bridge")
    original_parent = bridge.property("parent")
    assert root.property("childSkin") == "vintage_ticket"
    assert bridge.setProperty("parent", _find(root, "outside"))
    assert root.property("childSkin") == "fluent"
    assert bridge.setProperty("parent", original_parent)
    assert root.property("childSkin") == "vintage_ticket"


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_descendant_follows_explicit_bridge_replacement(engine, consumer):
    component, root = _build(engine, _scene(consumer))
    bridge = _find(root, "bridge")
    assert root.property("childSkin") == "vintage_ticket"
    assert bridge.setProperty("skinContext", root.property("fluentContext"))
    assert root.property("childSkin") == "fluent"
    assert bridge.setProperty("skinContext", root.property("ticketContext"))
    assert root.property("childSkin") == "vintage_ticket"
    assert bridge.setProperty("skinContext", root.property("fluentContext"))
    assert bridge.setProperty("skinContext", None)
    assert root.property("childSkin") == "vintage_ticket"
