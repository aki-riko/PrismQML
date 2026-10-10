# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Right-to-left detection and layout mirroring. 从右到左判定与布局镜像。

Fluent mirrors the whole layout for RTL scripts. The decision is derived from the
resolved translation language, and windows forward it through Qt's
``LayoutMirroring`` attached property.
从右到左文字会镜像整个布局。该判定由解析后的翻译语言派生，窗口通过 Qt 的
``LayoutMirroring`` 附加属性转发。
"""

from PySide6.QtQml import QQmlApplicationEngine

from prismqml import register_types


def _create(engine, source: bytes):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtQuick import QQuickItem

    component = QQmlComponent(engine)
    component.setData(source, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    instance = component.create()
    assert isinstance(instance, QQuickItem), errors
    return component, instance


def test_rtl_languages_are_declared_and_cover_arabic(qapp):
    """The RTL list must contain every shipped right-to-left catalogue."""
    from pathlib import Path

    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    property var rtl: Translator.rtlLanguages
    property bool arabicIsRtl: Translator.rtlLanguages.indexOf("ar") >= 0
}
""",
    )
    try:
        rtl = instance.property("rtl")
        if hasattr(rtl, "toVariant"):
            rtl = rtl.toVariant()
        assert "ar" in list(rtl)
        assert instance.property("arabicIsRtl") is True
        # Arabic ships a catalogue, so the mirroring decision must cover it.
        # 阿拉伯语已随包发布词表，因此镜像判定必须覆盖它。
        i18n = Path(__file__).resolve().parents[2] / "prismqml" / "PrismQML" / "i18n"
        assert (i18n / "ar.json").is_file()
    finally:
        instance.deleteLater()


def test_enums_exposes_the_right_to_left_flag(qapp):
    """Enums.isRtl forwards the resolved language decision."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    property bool rtl: Enums.isRtl
    property bool translatorRtl: Translator.isRightToLeft
}
""",
    )
    try:
        assert instance.property("rtl") == instance.property("translatorRtl")
    finally:
        instance.deleteLater()


def test_layout_mirroring_is_available_to_qml(qapp):
    """Qt's LayoutMirroring attached property must exist for windows to forward."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true
    property bool mirrored: LayoutMirroring.enabled
    property bool inherited: LayoutMirroring.childrenInherit
}
""",
    )
    try:
        assert instance.property("mirrored") is True
        assert instance.property("inherited") is True
    finally:
        instance.deleteLater()


def test_language_classifier_covers_rtl_and_ltr_codes(qapp):
    """The classifier answers for any code without touching the active language."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    property bool ar: Translator.isRtlLanguage("ar")
    property bool he: Translator.isRtlLanguage("he")
    property bool en: Translator.isRtlLanguage("en")
    property bool zh: Translator.isRtlLanguage("zh_CN")
    property bool blank: Translator.isRtlLanguage("")
    property bool missing: Translator.isRtlLanguage(undefined)
}
""",
    )
    try:
        assert instance.property("ar") is True
        assert instance.property("he") is True
        assert instance.property("en") is False
        assert instance.property("zh") is False
        assert instance.property("blank") is False
        assert instance.property("missing") is False
    finally:
        instance.deleteLater()


def test_active_flag_matches_the_classifier(qapp):
    """The singleton flag must equal the classifier applied to its own language."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    readonly property bool rtl: Translator.isRightToLeft
    readonly property bool expected:
        Translator.isRtlLanguage(Translator._resolvedLanguage)
}
""",
    )
    try:
        assert instance.property("rtl") == instance.property("expected")
    finally:
        instance.deleteLater()


def test_public_language_property_switches_the_flag(qapp):
    """Setting the public language to Arabic flips the flag through real loading."""
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(
        engine,
        b"""import QtQuick
import PrismQML
Item {
    readonly property bool rtl: Translator.isRightToLeft
    function selectLanguage(code) { Translator.language = code }
}
""",
    )
    try:
        from PySide6.QtCore import QCoreApplication, QMetaObject, Q_ARG

        assert instance.property("rtl") is False
        # The QML function takes a QVariant, so the argument carries no extra type.
        # 该 QML 函数形参为 QVariant，因此实参不附带额外类型。
        QMetaObject.invokeMethod(
            instance, "selectLanguage", Q_ARG("QVariant", "ar")
        )
        # The catalogue loads over XMLHttpRequest, so the switch settles later.
        # 词表经 XMLHttpRequest 加载，因此切换在稍后落定。
        for _ in range(60):
            QCoreApplication.processEvents()
        assert instance.property("rtl") is True
    finally:
        instance.deleteLater()
