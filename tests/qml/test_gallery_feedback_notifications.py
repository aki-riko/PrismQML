# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery notification showcase regressions. Gallery 通知展示回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)

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
PROGRESS_SHOWCASE_SOURCE = (
    ROOT
    / "examples"
    / "pages"
    / "_internal"
    / "FeedbackProgressShowcase.qml"
)
MENU_SHOWCASE_SOURCE = (
    ROOT
    / "examples"
    / "pages"
    / "_internal"
    / "FeedbackNotificationMenuShowcase.qml"
)

SEVERITIES = ("Info", "Success", "Warning", "Error", "Processing")
PROGRESS_MODES = (
    "ProgressBar",
    "IndeterminateBar",
    "ProgressRing",
    "IndeterminateRing",
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _evaluate(scope, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(scope), scope, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return result[0] if isinstance(result, tuple) else result


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


def _create_feedback_page():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(
        engine, QUrl.fromLocalFile(str(FEEDBACK_PAGE_SOURCE))
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    root.setWidth(1200)
    root.setHeight(800)
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


def test_gallery_progress_showcases_share_static_and_popup_layout():
    page_source = FEEDBACK_PAGE_SOURCE.read_text(encoding="utf-8")
    progress_source = PROGRESS_SHOWCASE_SOURCE.read_text(encoding="utf-8")

    assert "FeedbackProgressShowcase {" in page_source
    assert "notificationParent: root" in page_source
    assert progress_source.count("// Static showcase 静态展示") == 2
    assert progress_source.count("// Popup showcase 弹出演示") == 2
    assert progress_source.count("ComponentCard {") == len(PROGRESS_MODES) * 2
    assert progress_source.count("InfoBar {") == len(PROGRESS_MODES)
    assert progress_source.count("Toast {") == len(PROGRESS_MODES)
    assert progress_source.count("duration: Enums.duration.persistent") == (
        len(PROGRESS_MODES) * 2
    )
    assert progress_source.count("width: Enums.demoMetrics.feedbackNotificationWidth") == (
        len(PROGRESS_MODES) * 2
    )
    assert progress_source.count("visible: true") == len(PROGRESS_MODES)
    assert "width: 280" not in progress_source


def test_gallery_progress_static_previews_are_persistent(qapp):
    engine, component, root = _create_feedback_page()
    try:
        for mode in PROGRESS_MODES:
            info_bar = root.findChild(QQuickItem, f"galleryProgressInfoBar{mode}")
            toast = root.findChild(QQuickItem, f"galleryProgressToast{mode}")

            assert info_bar is not None
            assert toast is not None
            assert info_bar.property("duration") == -1
            assert toast.property("duration") == -1
            assert info_bar.width() == 320
            assert toast.width() == 320
            assert info_bar.isVisible()
            assert toast.isVisible()
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_gallery_notification_menu_routes_all_surfaces():
    page_source = FEEDBACK_PAGE_SOURCE.read_text(encoding="utf-8")
    menu_source = MENU_SHOWCASE_SOURCE.read_text(encoding="utf-8")

    assert "FeedbackNotificationMenuShowcase {" in page_source
    assert "notificationParent: root" in page_source
    assert "feature: Enums.button.feature_dropdown" in menu_source
    assert menu_source.count("addSubmenu(") == 2
    assert menu_source.count("addSubmenuActions(") == 6
    assert 'root._positionActions("toast", "in_app")' in menu_source
    assert 'root._positionActions("toast", "outside")' in menu_source
    assert 'root._positionActions("toast", "desktop")' in menu_source
    assert 'root._positionActions("infobar", "in_app")' in menu_source
    assert 'root._positionActions("infobar", "outside")' in menu_source
    assert 'root._positionActions("infobar", "desktop")' in menu_source

    for position_name in (
        "posTopLeft",
        "posTop",
        "posTopRight",
        "posLeft",
        "posCenter",
        "posRight",
        "posBottomLeft",
        "posBottom",
        "posBottomRight",
    ):
        assert f'"position": Enums.notification.{position_name}' in menu_source

    assert 'surface === "outside"' in menu_source
    assert "!Enums.notification.isWindowOutsidePosition(" in menu_source
    assert 'kind + "." + surface + "." + option.position' in menu_source
    assert "var position = Number(parts[2])" in menu_source

    assert menu_source.count("Enums.notification.mode_window_outside") == 2
    assert menu_source.count("Enums.notification.mode_in_app") == 2
    assert "NotificationManager.toast.info(" in menu_source
    assert "NotificationManager.infoBar.info(" in menu_source
    assert "NotificationManager.desktop.info(" in menu_source
    assert "NotificationManager.desktop.infoBar(" in menu_source
    assert 'title: "NotificationManager.infoBar"' not in page_source
    assert 'title: "NotificationManager.toast"' not in page_source


def test_gallery_notification_menu_has_no_untranslated_visible_labels():
    menu_source = MENU_SHOWCASE_SOURCE.read_text(encoding="utf-8")

    for literal in (
        'addSubmenu("Toast"',
        'addSubmenu("InfoBar"',
        'addAction("Window outside"',
        'addAction("Desktop"',
        'text: "NotificationManager"',
    ):
        assert literal not in menu_source

    for translation_key in (
        "gallery_7d40e038e4694fcc",
        "gallery_a598c8a19da5da6a",
        "gallery_8c2a398b8ff2e713",
        "gallery_921acd914acd6c57",
        "gallery_e70b45ef67e88235",
        "gallery_a84df74251f7f8da",
        "gallery_f48d334495f6e4f4",
        "gallery_14eeea875dc5c658",
        "gallery_c4162f1fe3ee4751",
        "gallery_ca75b858e7559fa3",
    ):
        assert f'"{translation_key}"' in menu_source


def test_gallery_notification_position_counts_follow_notification_contract(qapp):
    engine, component, root = _create_feedback_page()
    try:
        showcase = root.findChild(
            QQuickItem, "galleryNotificationMenuShowcase"
        )
        assert showcase is not None
        for kind in ("toast", "infobar"):
            assert _evaluate(
                showcase, f'_positionActions("{kind}", "in_app").length'
            ) == 9
            assert _evaluate(
                showcase, f'_positionActions("{kind}", "desktop").length'
            ) == 9
            assert _evaluate(
                showcase, f'_positionActions("{kind}", "outside").length'
            ) == 8
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_gallery_desktop_toast_options_use_separate_example_card():
    page_source = FEEDBACK_PAGE_SOURCE.read_text(encoding="utf-8")
    options_title = 'title: "NotificationManager.desktop (Toast options)"'
    assert options_title in page_source

    options_card = page_source.split(options_title, 1)[1].split(
        "// InfoBar进度模式", 1
    )[0]

    assert 'text: "Success + options"' in options_card
    assert '"customContent": desktopToastAction' in options_card
    assert '"screen": root.Window.window.screen' in options_card


def test_gallery_feedback_page_loads_with_current_edge_positions(qapp):
    engine, component, root = _create_feedback_page()
    try:
        assert root.width() == 1200
        assert root.height() == 800
        assert root.findChild(QQuickItem, "galleryNotificationModeButton") is not None
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_gallery_notification_showcases_follow_qml_conventions():
    for source_path in (
        SHOWCASE_SOURCE,
        PROGRESS_SHOWCASE_SOURCE,
        MENU_SHOWCASE_SOURCE,
    ):
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)

        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009", "QML011"}
        ] == []
