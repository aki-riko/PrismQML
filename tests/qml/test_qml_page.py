# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QMLPage public loading-page regressions. QMLPage 公开加载页回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]

QML_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int lazyRingStyle: Enums.progress.indeterminate_style_fixed_arc
    readonly property int lazyRingSize: Enums.controlSize.navBarHeight
    readonly property int lazyRingSpinDuration: Enums.duration.scroll
    readonly property int finishDuration: Enums.duration.fast
    readonly property int normalDuration: Enums.duration.normal
    width: 640
    height: 480

    function dropExitCallback() { page._completeFinish() }

    QMLPage {
        id: page
        objectName: "qmlPage"
        anchors.fill: parent
        text: "Loading page"
        backgroundColor: Enums.transparent
    }
}
"""

# Skeleton display style. The style is an explicit public property, so the same
# page component must serve both display forms.
# 骨架展示形式。展示形式是显式公开属性，因此同一个页面组件必须服务两种形态。
SKELETON_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    property int skeletonStyle: Enums.lazyLoadingStyle.style_skeleton
    property int ringStyle: Enums.lazyLoadingStyle.style_ring
    property int minRows: Enums.skeletonMetrics.pageRowMinCount
    property int maxRows: Enums.skeletonMetrics.pageRowMaxCount
    width: 640
    height: 480

    QMLPage {
        id: page
        objectName: "qmlPage"
        anchors.fill: parent
        text: "Loading page"
        backgroundColor: Enums.transparent
        style: skeletonStyle
    }
}
"""


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    """Every visual descendant, in tree order. 全部可视后代，按树序。

    Repeater delegates are visual children of the Repeater's parent but carry a
    different QObject parent, so findChildren cannot see them.
    Repeater 委托是 Repeater 父项的可视子项，但其 QObject 父级不同，findChildren 看不到。
    """
    descendants: list[QQuickItem] = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def test_qml_page_is_public_and_preserves_lazy_progress(qapp):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:qml-page-test.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        content = root.findChild(QQuickItem, "qmlPageContent")
        ring = root.findChild(QQuickItem, "qmlPageProgressRing")
        label = root.findChild(QQuickItem, "qmlPageLabel")
        assert page is not None
        assert content is not None
        assert ring is not None
        assert label is not None
        assert page.property("text") == "Loading page"
        assert page.property("running") is True
        assert ring.property("indeterminate") is True
        assert ring.property("indeterminateStyle") == root.property("lazyRingStyle")
        assert ring.property("spinDuration") == root.property("lazyRingSpinDuration")
        assert ring.width() == root.property("lazyRingSize")
        assert ring.height() == root.property("lazyRingSize")
        assert ring.x() + ring.width() / 2 == pytest.approx(
            content.width() / 2, abs=0.5
        )
        assert label.x() + label.width() / 2 == pytest.approx(
            content.width() / 2, abs=0.5
        )
        assert label.y() > ring.y() + ring.height()

        page.setProperty("running", False)
        assert ring.property("indeterminate") is False
        assert ring.property("paused") is True
    finally:
        root.deleteLater()
        engine.deleteLater()


def test_qml_page_only_manages_the_wait_indicator(qapp):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:qml-page-exit-test.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        content = root.findChild(QQuickItem, "qmlPageContent")
        ring = root.findChild(QQuickItem, "qmlPageProgressRing")
        assert page is not None and content is not None and ring is not None
        assert root.findChild(QQuickItem, "qmlPageCircleTransition") is None
        assert root.findChild(QQuickItem, "qmlPageCircleFrame") is None

        finished = []
        page.finished.connect(lambda: finished.append(True))
        assert QMetaObject.invokeMethod(page, "finish")
        assert page.property("finishing") is True
        assert page.property("running") is False
        _pump(root.property("finishDuration") // 2)
        assert 0 < content.property("opacity") < 1
        assert content.property("scale") < 1
        assert _wait_until(lambda: page.property("visible") is False)
        assert finished == [True]
        assert page.property("running") is False
        assert ring.property("paused") is True

        assert QMetaObject.invokeMethod(page, "finish")
        assert finished == [True]

        assert QMetaObject.invokeMethod(page, "start")
        assert page.property("visible") is True
        assert page.property("running") is True
        assert ring.property("indeterminate") is True
        assert content.property("opacity") == pytest.approx(1)
        assert content.property("scale") == pytest.approx(1)

        _pump(100)
        assert 0.96 <= ring.property("scale") <= 1.04

        assert QMetaObject.invokeMethod(page, "finish")
        assert page.property("finishing") is True
        assert _wait_until(lambda: finished == [True, True])
        assert page.property("visible") is False
    finally:
        root.deleteLater()
        engine.deleteLater()


def test_qml_page_exit_watchdog_finishes_a_dropped_exit_callback(qapp):
    """退场回调未落地时, 看门狗必须完成同一次退场。

    The exit animation callback can be dropped when the host window is hidden
    mid-startup or the scene graph is torn down; without a watchdog the wait
    indicator would stay parked on screen. The watchdog is idempotent, so it
    must not emit a second finished() or restart a hidden page.
    宿主机启动期把窗口藏起来或场景图被拆时退场动画回调会丢失; 没有看门狗, 等待
    指示会永久停在屏幕上。看门狗是幂等的, 不得发出第二个 finished(), 也不得
    重启已隐藏的页面。
    """
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(QML_SOURCE, QUrl("inline:qml-page-watchdog-test.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        content = root.findChild(QQuickItem, "qmlPageContent")
        guard = root.findChild(QObject, "qmlPageFinishGuard")
        assert page is not None and content is not None
        assert guard is not None, "QMLPage must own its exit watchdog"
        assert guard.property("interval") == (
            root.property("finishDuration") + root.property("normalDuration")
        )
        assert guard.property("repeat") is False

        finished = []
        page.finished.connect(lambda: finished.append(True))
        assert QMetaObject.invokeMethod(page, "finish")
        assert page.property("finishing") is True
        # Simulate the dropped animation callback: complete the exit directly.
        # 模拟退场回调丢失: 直接完成退场。
        assert QMetaObject.invokeMethod(root, "dropExitCallback")
        assert page.property("visible") is False
        assert page.property("finishing") is False
        assert finished == [True]
        assert content.property("opacity") == pytest.approx(1)

        # The watchdog must not fire a second, spurious completion.
        # 看门狗不得再触发第二次虚假收尾。
        _pump(root.property("finishDuration") + root.property("normalDuration") + 60)
        assert finished == [True]
        assert page.property("visible") is False
    finally:
        root.deleteLater()
        engine.deleteLater()


def test_qml_page_skeleton_style_is_opt_in_and_lazy(qapp):
    """骨架展示形式必须显式开启，并通过惰性 Loader 承载。

    默认 ring 路径的对象数、布局与时序不得改变：骨架 Loader 在 ring 模式下不激活，
    因此不会创建任何 Skeleton 对象。
    """
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SKELETON_SOURCE, QUrl("inline:qml-page-skeleton-test.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()

    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        page = root.findChild(QQuickItem, "qmlPage")
        assert page is not None
        loader = page.findChild(QObject, "qmlPageSkeletonLoader")
        assert loader is not None, "QMLPage must own a lazy skeleton Loader"
        assert page.property("style") == root.property("skeletonStyle")

        blocks = [
            child
            for child in _visual_descendants(page)
            if child.metaObject().className().startswith("Skeleton")
        ]
        rows = [block for block in blocks if block.objectName() == "qmlPageSkeletonRow"]
        assert loader.property("active") is True
        assert rows
        assert len(blocks) == len(rows) + 2
        assert root.property("minRows") <= len(rows) <= root.property("maxRows")

        # The ring branch is still present but must not animate in this mode.
        # 环形分支仍然存在，但在本模式下不得动画。
        assert page.findChild(QQuickItem, "qmlPageContent") is not None
        ring = page.findChild(QQuickItem, "qmlPageProgressRing")
        assert ring is not None
        assert ring.property("paused") is True

        # Switching back to the default style tears the skeleton objects down.
        # 切回默认形式必须销毁骨架对象。
        root.setProperty("skeletonStyle", root.property("ringStyle"))
        _pump()
        assert loader.property("active") is False
        assert loader.property("item") is None
        assert [
            child
            for child in _visual_descendants(page)
            if child.metaObject().className().startswith("Skeleton")
        ] == []
        assert ring.property("paused") is False
    finally:
        root.deleteLater()
        engine.deleteLater()
