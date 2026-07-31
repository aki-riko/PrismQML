# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery notification showcase regressions. Gallery 通知展示回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
FEEDBACK_PAGE_SOURCE = ROOT / "examples" / "pages" / "FeedbackPage.qml"
SHOWCASE_SOURCE = (
    ROOT
    / "examples"
    / "pages"
    / "_internal"
    / "FeedbackNotificationShowcase.qml"
)

SEVERITIES = ("Info", "Success", "Warning", "Error", "Processing")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_showcase():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(SHOWCASE_SOURCE)))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    root.setWidth(900)
    _pump(100)
    return engine, component, root


def test_gallery_showcases_persistent_info_bars_and_toasts(qapp):
    engine, component, root = _create_showcase()
    try:
        for severity in SEVERITIES:
            info_bar = root.findChild(QQuickItem, f"galleryInfoBar{severity}")
            toast = root.findChild(QQuickItem, f"galleryToast{severity}")

            assert info_bar is not None
            assert toast is not None
            assert info_bar.property("duration") == -1
            assert toast.property("duration") == -1
            assert info_bar.width() == 320
            assert toast.width() == 320
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_gallery_feedback_page_uses_shared_notification_showcase():
    page_source = FEEDBACK_PAGE_SOURCE.read_text(encoding="utf-8")
    showcase_source = SHOWCASE_SOURCE.read_text(encoding="utf-8")

    assert 'import "_internal"' in page_source
    assert "FeedbackNotificationShowcase {}" in page_source
    assert showcase_source.count("InfoBar {") == len(SEVERITIES)
    assert showcase_source.count("Toast {") == len(SEVERITIES)
    assert showcase_source.count("duration: Enums.duration.persistent") == (
        len(SEVERITIES) * 2
    )
    assert showcase_source.count("visible: true") == len(SEVERITIES)
    assert "duration: Enums.duration.notification" not in showcase_source
    assert "width: 320" not in showcase_source


def test_gallery_notification_showcase_follows_qml_conventions():
    source = SHOWCASE_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(SHOWCASE_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)

    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML011"}
    ] == []
