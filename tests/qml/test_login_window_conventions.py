# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""LoginWindow form and signal contracts. 登录窗口表单与信号合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "auth" / "LoginWindow.qml"
)
CONTENT_PATH = SOURCE_PATH.parent / "_internal" / "LoginWindowContent.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "login-window-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

LoginWindow {
    objectName: "login"
    readonly property int loginMode: Enums.auth.mode_login
    readonly property int registerMode: Enums.auth.mode_register
    width: 640
    height: 520
    matrixEnabled: false
    Component.onCompleted: Translator.setLanguage(Enums.lang.en)
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _line_edit(root, placeholder: str):
    matches = [
        obj
        for obj in root.findChildren(QObject)
        if obj.metaObject().className().startswith("LineEditCore")
        and obj.property("placeholderText") == placeholder
    ]
    assert len(matches) == 1, [obj.metaObject().className() for obj in matches]
    return matches[0]


def _check_box(root, text: str):
    matches = [
        obj
        for obj in root.findChildren(QObject)
        if obj.metaObject().className().startswith("CheckBox")
        and obj.property("text") == text
    ]
    assert len(matches) == 1, [obj.metaObject().className() for obj in matches]
    return matches[0]


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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root, warnings


def _dispose_scene(engine, component, root) -> None:
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_login_window_submits_login_and_register_payloads(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    login_events = []
    register_events = []
    root.loginRequested.connect(lambda *args: login_events.append(args))
    root.registerRequested.connect(lambda *args: register_events.append(args))
    try:
        username = _line_edit(root, "Username or Email")
        password = _line_edit(root, "Password")
        remember = _check_box(root, "Remember me")
        username.setProperty("text", "alice")
        password.setProperty("text", "secret")
        remember.setProperty("checked", True)
        assert QMetaObject.invokeMethod(root, "_submitForm")
        assert login_events == [("alice", "secret", True)]

        root.setProperty("mode", root.property("registerMode"))
        assert _wait_for(
            lambda: root.property("mode") == root.property("registerMode")
        )
        assert not root.property("_isLogin")
        email = _line_edit(root, "Email")
        confirm = _line_edit(root, "Confirm Password")
        username.setProperty("text", "bob")
        email.setProperty("text", "bob@example.test")
        password.setProperty("text", "secret")
        confirm.setProperty("text", "mismatch")
        assert QMetaObject.invokeMethod(root, "_submitForm")
        assert register_events == []
        confirm.setProperty("text", "secret")
        assert QMetaObject.invokeMethod(root, "_submitForm")
        assert register_events == [("bob", "bob@example.test", "secret")]
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _dispose_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []


def test_login_window_clear_form_and_error(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        username = _line_edit(root, "Username or Email")
        password = _line_edit(root, "Password")
        remember = _check_box(root, "Remember me")
        username.setProperty("text", "alice")
        password.setProperty("text", "secret")
        remember.setProperty("checked", True)
        root.setProperty("errorMessage", "Denied")
        assert QMetaObject.invokeMethod(root, "clearForm")
        assert username.property("text") == ""
        assert password.property("text") == ""
        assert not remember.property("checked")
        assert root.property("errorMessage") == ""
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _dispose_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []


def test_login_window_prewarms_and_reuses_register_fields(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, warnings = _create_scene()
    try:
        email_loader = root.findChild(QObject, "loginEmailInputLoader")
        confirm_loader = root.findChild(
            QObject, "loginConfirmPasswordInputLoader"
        )
        strength_loader = root.findChild(QObject, "loginPasswordStrengthLoader")
        mode_toggle = root.findChild(QObject, "loginModeToggleArea")
        assert email_loader is not None
        assert confirm_loader is not None
        assert strength_loader is not None
        assert mode_toggle is not None
        remember = _check_box(root, "Remember me")
        remember.setProperty("checked", True)
        assert email_loader.property("item") is None
        assert confirm_loader.property("item") is None
        assert strength_loader.property("item") is None

        mode_toggle.entered.emit()
        assert _wait_for(lambda: email_loader.property("item") is not None)
        assert confirm_loader.property("item") is not None
        assert strength_loader.property("item") is not None
        email = _line_edit(root, "Email")
        confirm = _line_edit(root, "Confirm Password")
        assert email.property("visible") is False
        assert confirm.property("visible") is False

        email.setProperty("text", "alice@example.test")
        confirm.setProperty("text", "secret")
        root.setProperty("mode", root.property("registerMode"))
        assert _wait_for(lambda: not root.property("_isLogin"))
        assert email.property("visible") is True
        assert confirm.property("visible") is True

        root.setProperty("mode", root.property("loginMode"))
        assert _wait_for(lambda: root.property("_isLogin"))
        assert email_loader.property("item") is not None
        assert confirm_loader.property("item") is not None
        assert email.property("text") == "alice@example.test"
        assert confirm.property("text") == "secret"
        assert remember.property("checked") is True

        assert QMetaObject.invokeMethod(root, "clearForm")
        assert email.property("text") == ""
        assert confirm.property("text") == ""
        assert remember.property("checked") is False
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _dispose_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []


def test_login_window_source_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    content_source = CONTENT_PATH.read_text(encoding="utf-8")
    for source_path, candidate_source in (
        (SOURCE_PATH, source),
        (CONTENT_PATH, content_source),
    ):
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(candidate_source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
    assert 'objectName: "loginModeToggleArea"' in content_source
    assert "hoverEnabled: true" in content_source
    assert (
        "onEntered: control._prewarmAlternateModeContent()" in content_source
    )
