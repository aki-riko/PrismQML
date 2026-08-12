# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML theme entrypoint and global Label enum regressions. QML 主题入口与 Label 全局枚举回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    Property,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine, QQmlExpression

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
LABEL_SOURCE = ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Label" / "Label.qml"
ENUMS_SOURCE = ROOT / "prismqml" / "PrismQML" / "Enums.qml"
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
DATA_CONTROLS = ROOT / "prismqml" / "PrismQML" / "controls" / "data"
DATA_CONTROLS_URL = QUrl.fromLocalFile(str(DATA_CONTROLS)).toString()
COLOR_PICKER_INTERNAL = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "inputs"
    / "ColorPicker"
    / "_internal"
)
COLOR_PICKER_INTERNAL_URL = QUrl.fromLocalFile(str(COLOR_PICKER_INTERNAL)).toString()


class _FakeMicaManager(QObject):
    def __init__(self):
        super().__init__()
        self.calls: list[tuple[bool, bool]] = []

    @Property(bool, constant=True)
    def isMicaSupported(self) -> bool:
        return True

    @Slot(QObject, bool, bool, result=bool)
    def setMicaEffect(self, _window: QObject, enabled: bool, dark: bool) -> bool:
        self.calls.append((enabled, dark))
        return True


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose_qml(engine, component, instance) -> None:
    """Synchronously drain deferred QML deletion. 同步冲刷 QML 延迟删除。"""
    if instance is not None:
        instance.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _create(engine: QQmlApplicationEngine, source: bytes):
    component = QQmlComponent(engine)
    component.setData(source, QUrl("inline:p6b-theme-entrypoints.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _evaluate(instance: QObject, expression_source: str):
    expression = QQmlExpression(
        QQmlEngine.contextForObject(instance), instance, expression_source
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    return result


def test_label_first_load_uses_global_enum_values(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        component, instance = _create(
            engine,
            b"""import PrismQML
Label {
    property var enumValues: [
        Enums.label.type_body,
        Enums.label.type_body_strong,
        Enums.label.type_body_small,
        Enums.label.type_caption,
        Enums.label.type_subtitle,
        Enums.label.type_title,
        Enums.label.type_title_large,
        Enums.label.type_display,
        Enums.label.type_hyperlink
    ]
}
""",
        )
        enum_values = instance.property("enumValues")
        if hasattr(enum_values, "toVariant"):
            enum_values = enum_values.toVariant()
        assert list(enum_values) == list(range(9))
        assert instance.property("type") == 0
        assert instance.property("underlineOnHover") is False
        hyperlink_loader = next(
            child
            for child in instance.childItems()
            if "QQuickLoader" in child.metaObject().className()
        )

        for label_type in range(9):
            assert instance.setProperty("type", label_type)
            assert instance.property("type") == label_type
            assert instance.property("_fontSize") > 0
            hyperlink = label_type == 8
            assert instance.property("font").underline() is hyperlink
            assert hyperlink_loader.property("active") is hyperlink
            assert (hyperlink_loader.property("item") is not None) is hyperlink

        assert instance.setProperty("underlineOnHover", True)
        assert instance.property("font").underline() is False

        assert "_type_" not in LABEL_SOURCE.read_text(encoding="utf-8")
    finally:
        _dispose_qml(engine, component, instance)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)


def test_font_consumers_use_global_theme_font(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        source = f"""import QtQuick
import PrismQML
import "{DATA_CONTROLS_URL}" as DataControls
Item {{
    width: 800
    height: 600
    Button {{
        objectName: "defaultButton"
        text: "Default"
    }}
    Button {{
        objectName: "dropdownButton"
        feature: Enums.button.feature_dropdown
        menuItems: ["One"]
    }}
    LineEdit {{ id: normalInput; inputType: Enums.input.type_normal }}
    LineEdit {{ id: passwordInput; inputType: Enums.input.type_password }}
    LineEdit {{ id: searchInput; inputType: Enums.input.type_search }}
    LineEdit {{ id: labelInput; inputType: Enums.input.type_label; label: "Label" }}
    LineEdit {{ id: tagInput; inputType: Enums.input.type_tag }}
    TextEdit {{ id: textEditor }}
    SpinBox {{ id: spinBox }}
    DataControls.PaintedRow {{ objectName: "paintedRow"; columns: []; rowData: ({{}}) }}
    property string expectedFontFamily: Enums.fontFamily
    property string expectedCanvasFontFamily: Enums.canvasFontFamily
    property bool fontsMatch:
        normalInput.textInput && normalInput.textInput.font.family === Enums.fontFamily &&
        passwordInput.textInput && passwordInput.textInput.font.family === Enums.fontFamily &&
        searchInput.textInput && searchInput.textInput.font.family === Enums.fontFamily &&
        labelInput.textInput && labelInput.textInput.font.family === Enums.fontFamily &&
        tagInput.textInput && tagInput.textInput.font.family === Enums.fontFamily &&
        textEditor.focusTarget && textEditor.focusTarget.font.family === Enums.fontFamily &&
        spinBox.focusTarget && spinBox.focusTarget.font.family === Enums.fontFamily
}}
"""
        component, instance = _create(engine, source.encode("utf-8"))
        _pump(10)
        assert instance.property("fontsMatch") is True

        children = instance.findChildren(QObject)
        assert any(child.property("text") == "Default" for child in children)

        dropdown_features = [
            child
            for child in children
            if child.metaObject().indexOfProperty("_menuContentRequested") >= 0
        ]
        assert len(dropdown_features) == 1
        assert QMetaObject.invokeMethod(dropdown_features[0], "prewarmMenu")
        _pump(10)
        children = instance.findChildren(QObject)

        text_metrics = [
            child
            for child in children
            if "TextMetrics" in child.metaObject().className()
        ]
        assert text_metrics
        assert any(
            metrics.property("font").family()
            == instance.property("expectedFontFamily")
            for metrics in text_metrics
        )

        font_specs = [
            child.property("fontSpec")
            for child in children
            if child.metaObject().indexOfProperty("fontSpec") >= 0
        ]
        assert (
            "12pt " + instance.property("expectedCanvasFontFamily")
        ) in font_specs
    finally:
        _dispose_qml(engine, component, instance)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)


def test_monospace_consumers_use_global_theme_font(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        source = f"""import QtQuick
import PrismQML
import "{COLOR_PICKER_INTERNAL_URL}" as ColorPickerInternal
Item {{
    CodeBlock {{ code: "monospace-probe" }}
    ColorPickerInternal.ColorPickerInputs {{}}
    ColorPickerInternal.ColorPickerDropdown {{}}
    property string expectedFontMonospace: Enums.fontMonospace
    property bool fontMatchesManager:
        Enums.fontMonospace === ThemeManager.fontMonospace
}}
"""
        component, instance = _create(engine, source.encode("utf-8"))
        _pump(10)
        assert instance.property("fontMatchesManager") is True

        expected = instance.property("expectedFontMonospace")
        font_families = [
            child.property("font").family()
            for child in instance.findChildren(QObject)
            if child.metaObject().indexOfProperty("font") >= 0
        ]
        assert font_families.count(expected) >= 4, font_families

        assert "iconFontFamily" not in ENUMS_SOURCE.read_text(encoding="utf-8")
        assert "monospaceFontFamily" not in METRICS_SOURCE.read_text(encoding="utf-8")
    finally:
        _dispose_qml(engine, component, instance)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)


def test_outlined_skin_runtime_switch_disables_mica(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    fake_mica = _FakeMicaManager()
    engine.rootContext().setContextProperty("MicaManager", fake_mica)
    component = instance = None
    try:
        component, instance = _create(
            engine,
            b"""import PrismQML
NavigationWindowCore {
    visible: false
    micaEnabled: true
    shadowMode: Enums.windowShadow.mode_none
}
""",
        )
        _evaluate(instance, "_nativeHookReady = false")
        fake_mica.calls.clear()
        _evaluate(instance, "nativeHookReady()")
        _pump(1)
        assert instance.property("_nativeHookReady") is True
        assert fake_mica.calls[-1] == (True, False)
        assert instance.property("_micaBackdropReady") is False
        _pump(100)
        assert instance.property("_micaBackdropReady") is True

        setSkin(Skin.NEOBRUTALISM)
        _pump(1)
        assert instance.property("_micaActive") is False
        assert fake_mica.calls[-1] == (False, False)
        assert instance.property("_micaBackdropReady") is False

        setSkin(Skin.VINTAGE_TICKET)
        _pump(1)
        assert instance.property("_micaActive") is False
        assert fake_mica.calls[-1] == (False, False)
        assert instance.property("_micaBackdropReady") is False

        setSkin(Skin.FLUENT)
        _pump(1)
        assert instance.property("_micaActive") is True
        assert fake_mica.calls[-1] == (True, False)
        _pump(100)
        assert instance.property("_micaBackdropReady") is True
    finally:
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        _dispose_qml(engine, component, instance)
