# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Cross-component runtime i18n contracts. 跨组件运行时翻译合同。"""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests/qml/project-i18n-runtime.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property string initialTranslation: Translator.tr("checking_for_updates")
    readonly property string loginTitle: login.title
    readonly property string calendarPlaceholder: calendar.placeholderText
    readonly property string calendarWeekday: calendar.weekDays[0]
    readonly property string treeSearchPlaceholder: tree.searchPlaceholder
    readonly property string stateTitle: state._defaultTitle
    readonly property string offlineTitle: offline._defaultTitle
    readonly property string offlineRetry: offline._defaultRetryText
    readonly property string strongestPassword: strength.strengthTexts[4]
    readonly property string watermarkText: watermark.text
    readonly property string confirmTitle: confirm.title
    readonly property string confirmCancel: confirm.cancelText
    readonly property string confirmAction: confirm._autoConfirmText
    readonly property string messageCancel: message.cancelText
    readonly property string updateConfirm: updateDialog.confirmText
    readonly property string colorTheme: colorPicker.themeColorsText

    function useEnglish() { Translator.setLanguage(Enums.lang.en) }
    function useSimplifiedChinese() { Translator.setLanguage(Enums.lang.zh_CN) }

    LoginWindow {
        id: login
        visible: false
        matrixEnabled: false
        oauthProviders: []
    }

    CalendarPicker { id: calendar; visible: false; type: Enums.calendarPicker.type_range }
    ComboBoxTree { id: tree; visible: false }
    StateWidget { id: state; visible: false; stateType: Enums.state.type_no_internet }
    OfflineState { id: offline; visible: false }
    PasswordStrengthIndicator { id: strength; visible: false }
    Watermark { id: watermark; visible: false }
    ConfirmDialog { id: confirm; visible: false; level: Enums.statusLevel.warning }
    MessageBox { id: message; visible: false }
    UpdateDialog { id: updateDialog; visible: false }
    ColorPicker { id: colorPicker; visible: false }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1800) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def test_public_component_defaults_follow_runtime_language(qapp):
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
    try:
        assert root.property("initialTranslation") != "checking_for_updates"
        assert QMetaObject.invokeMethod(root, "useEnglish")
        assert _wait_for(lambda: root.property("loginTitle") == "Welcome Back")
        assert root.property("calendarPlaceholder") == "Select date range"
        assert root.property("calendarWeekday") == "Sun"
        assert root.property("treeSearchPlaceholder") == "Enter keyword..."
        assert root.property("stateTitle") == "No Internet Connection"
        assert root.property("offlineTitle") == "No Internet Connection"
        assert root.property("offlineRetry") == "Retry"
        assert root.property("strongestPassword") == "Very Strong"
        assert root.property("watermarkText") == "Watermark"
        assert root.property("confirmTitle") == "Confirm Action"
        assert root.property("confirmCancel") == "Cancel"
        assert root.property("confirmAction") == "Confirm"
        assert root.property("messageCancel") == "Cancel"
        assert root.property("updateConfirm") == "Download and Install"
        assert root.property("colorTheme") == "Theme Colors"

        assert QMetaObject.invokeMethod(root, "useSimplifiedChinese")
        assert _wait_for(lambda: root.property("loginTitle") == "欢迎回来")
        assert root.property("calendarPlaceholder") == "选择日期范围"
        assert root.property("calendarWeekday") == "日"
        assert root.property("treeSearchPlaceholder") == "请输入关键字..."
        assert root.property("stateTitle") == "网络连接已断开"
        assert root.property("offlineTitle") == "网络连接已断开"
        assert root.property("offlineRetry") == "重试"
        assert root.property("strongestPassword") == "非常强"
        assert root.property("watermarkText") == "水印"
        assert root.property("confirmTitle") == "确认操作"
        assert root.property("confirmCancel") == "取消"
        assert root.property("confirmAction") == "确认"
        assert root.property("messageCancel") == "取消"
        assert root.property("updateConfirm") == "下载并安装"
        assert root.property("colorTheme") == "主题色"
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()
