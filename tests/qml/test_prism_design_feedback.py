# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design semantic feedback skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _alpha(qcolor):
    return round(qcolor.alphaF() * 255)


def _assert_info_bar(item, background, border, shadow_alpha):
    assert item.property("_infoBarRadius") == 10
    assert item.property("_infoBarBorderWidth") == 1
    assert _rgb(item.property("_infoBarBackground")) == background
    assert _rgb(item.property("_infoBarBorderColor")) == border
    assert item.property("_infoBarShadowBlur") == 8
    assert item.property("_infoBarShadowOffset") == 2
    assert _alpha(item.property("_infoBarShadowColor")) == shadow_alpha


def _assert_toast(item, background, border, shadow_alpha):
    assert item.property("_toastRadius") == 10
    assert item.property("_toastColorBarRadius") == 10
    assert item.property("_toastBorderWidth") == 1
    assert _rgb(item.property("_toastBackground")) == background
    assert _rgb(item.property("_toastBorderColor")) == border
    assert item.property("_toastShadowBlur") == 8
    assert item.property("_toastShadowOffset") == 2
    assert _alpha(item.property("_toastShadowColor")) == shadow_alpha


def _assert_desktop_notification(item, background, border, message, shadow_alpha):
    assert item.property("_notificationRadius") == 10
    assert item.property("_notificationIconRadius") == 6
    assert item.property("_notificationBorderWidth") == 1
    assert _rgb(item.property("_notificationBackground")) == background
    assert _rgb(item.property("_notificationBorderColor")) == border
    assert _rgb(item.property("_notificationMessageColor")) == message
    assert item.property("_notificationShadowBlur") == 16
    assert item.property("_notificationShadowOffset") == 4
    assert _alpha(item.property("_notificationShadowColor")) == shadow_alpha


def _assert_progress(item, progress, track, text):
    assert _rgb(item.property("_progressColor")) == progress
    assert _rgb(item.property("_trackColor")) == track
    assert _rgb(item.property("_filledTextColor")) == text


def _assert_direct_progress_bar(item, progress, track):
    assert _rgb(item.property("progressColor")) == progress
    assert _rgb(item.property("trackColor")) == track


def _assert_direct_progress_ring(item, progress, track):
    assert item.property("strokeWidth") == 5
    assert _rgb(item.property("progressColor")) == progress
    assert _rgb(item.property("backgroundColor")) == track


def _assert_skeleton(item, base, shimmer):
    assert item.property("_radius") == 6
    assert _rgb(item.property("baseColor")) == base
    assert _rgb(item.property("shimmerColor")) == shimmer


def _assert_tag(item, background, text):
    assert item.property("_tagRadius") == 6
    assert _rgb(item.property("_tagBackground")) == background
    assert _rgb(item.property("currentColor")) == text


def _assert_tip_popup(item, background, border):
    assert item.property("_tipRadius") == 10
    assert item.property("_tipBorderWidth") == 1
    assert _rgb(item.property("_tipBackground")) == background
    assert _rgb(item.property("_tipBorderColor")) == border


def _assert_hint_icon(item, color):
    assert item.property("iconSize") == 14
    assert item.property("toolTipShowDelay") == 100
    assert _rgb(item.property("color")) == color


def test_prism_design_feedback_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
InfoBar {
    title: "Warning"
    content: "Semantic message"
    severity: "warning"
    duration: 0
}
"""))
        info_bar = keep[-1][1]
        _assert_info_bar(info_bar, (255, 244, 206), (217, 227, 236), 31)

        keep.append(_build(engine, b"""
import PrismQML
Toast {
    title: "Saved"
    message: "Build completed"
    severity: "success"
    duration: 0
}
"""))
        toast = keep[-1][1]
        _assert_toast(toast, (248, 251, 255), (231, 238, 245), 31)
        assert _rgb(toast.property("severityColor")) == (15, 123, 15)

        keep.append(_build(engine, b"""
import PrismQML
DesktopNotification {
    title: "Deploy"
    message: "Production updated"
    severity: "error"
    duration: 0
}
"""))
        notification = keep[-1][1]
        _assert_desktop_notification(
            notification,
            (248, 251, 255),
            (217, 227, 236),
            (95, 111, 128),
            36,
        )

        keep.append(_build(engine, b"""
import PrismQML
Progress {
    type: Enums.progress.type_bar_filled
    width: 200
    height: 24
    value: 72
}
"""))
        progress = keep[-1][1]
        qapp.processEvents()
        _assert_progress(progress, (47, 111, 237), (234, 241, 247), (255, 255, 255))

        keep.append(_build(engine, b"""
import PrismQML
Progress {
    type: Enums.progress.type_bar_filled
    width: 200
    height: 24
    value: 24
}
"""))
        low_progress = keep[-1][1]
        qapp.processEvents()
        _assert_progress(low_progress, (47, 111, 237), (234, 241, 247), (23, 32, 42))

        keep.append(_build(engine, b"""
import PrismQML
ProgressBar {
    width: 200
    value: 48
}
"""))
        progress_bar = keep[-1][1]
        _assert_direct_progress_bar(progress_bar, (47, 111, 237), (234, 241, 247))

        keep.append(_build(engine, b"""
import PrismQML
ProgressRing {
    value: 48
}
"""))
        progress_ring = keep[-1][1]
        _assert_direct_progress_ring(progress_ring, (47, 111, 237), (234, 241, 247))

        keep.append(_build(engine, b"""
import PrismQML
TipPopup {
    title: "Layer"
    content: "Overlay feedback"
}
"""))
        tip_popup = keep[-1][1]
        _assert_tip_popup(tip_popup, (248, 251, 255), (217, 227, 236))

        keep.append(_build(engine, b"""
import PrismQML
HintIcon {
    toolTipText: "Why this matters"
}
"""))
        hint_icon = keep[-1][1]
        _assert_hint_icon(hint_icon, (131, 146, 164))

        keep.append(_build(engine, b"""
import PrismQML
EmptyDataState {
    title: "No records"
    image: "MailInboxDismiss"
}
"""))
        empty_data = keep[-1][1]
        assert empty_data.property("title") == "No records"
        assert empty_data.property("imageWidth") == 128
        assert empty_data.property("imageHeight") == 128

        keep.append(_build(engine, b"""
import PrismQML
Skeleton {
    width: 120
    height: 24
}
"""))
        skeleton = keep[-1][1]
        _assert_skeleton(skeleton, (231, 238, 245), (238, 245, 255))

        keep.append(_build(engine, b"""
import PrismQML
Tag {
    text: "Ready"
    status: Enums.statusLevel.success
}
"""))
        tag = keep[-1][1]
        _assert_tag(tag, (223, 246, 221), (15, 123, 15))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
InfoBar {
    title: "Warning"
    content: "Semantic message"
    severity: "warning"
    duration: 0
}
"""))
        dark_info_bar = keep[-1][1]
        _assert_info_bar(dark_info_bar, (48, 36, 0), (48, 58, 70), 46)

        keep.append(_build(engine, b"""
import PrismQML
Toast {
    title: "Saved"
    message: "Build completed"
    severity: "success"
    duration: 0
}
"""))
        dark_toast = keep[-1][1]
        _assert_toast(dark_toast, (36, 43, 52), (38, 48, 58), 46)
        assert _rgb(dark_toast.property("severityColor")) == (108, 203, 95)

        keep.append(_build(engine, b"""
import PrismQML
DesktopNotification {
    title: "Deploy"
    message: "Production updated"
    severity: "error"
    duration: 0
}
"""))
        dark_notification = keep[-1][1]
        _assert_desktop_notification(
            dark_notification,
            (36, 43, 52),
            (48, 58, 70),
            (166, 177, 191),
            54,
        )

        keep.append(_build(engine, b"""
import PrismQML
Progress {
    type: Enums.progress.type_bar_filled
    width: 200
    height: 24
    value: 72
}
"""))
        dark_progress = keep[-1][1]
        qapp.processEvents()
        _assert_progress(dark_progress, (122, 167, 255), (21, 26, 32), (15, 23, 42))

        keep.append(_build(engine, b"""
import PrismQML
ProgressBar {
    width: 200
    value: 48
}
"""))
        dark_progress_bar = keep[-1][1]
        _assert_direct_progress_bar(dark_progress_bar, (122, 167, 255), (21, 26, 32))

        keep.append(_build(engine, b"""
import PrismQML
ProgressRing {
    value: 48
}
"""))
        dark_progress_ring = keep[-1][1]
        _assert_direct_progress_ring(dark_progress_ring, (122, 167, 255), (21, 26, 32))

        keep.append(_build(engine, b"""
import PrismQML
TipPopup {
    title: "Layer"
    content: "Overlay feedback"
}
"""))
        dark_tip_popup = keep[-1][1]
        _assert_tip_popup(dark_tip_popup, (36, 43, 52), (48, 58, 70))

        keep.append(_build(engine, b"""
import PrismQML
HintIcon {
    toolTipText: "Why this matters"
}
"""))
        dark_hint_icon = keep[-1][1]
        _assert_hint_icon(dark_hint_icon, (118, 131, 148))

        keep.append(_build(engine, b"""
import PrismQML
EmptyDataState {
    title: "No records"
    image: "MailInboxDismiss"
}
"""))
        dark_empty_data = keep[-1][1]
        assert dark_empty_data.property("title") == "No records"
        assert dark_empty_data.property("imageWidth") == 128
        assert dark_empty_data.property("imageHeight") == 128

        keep.append(_build(engine, b"""
import PrismQML
Skeleton {
    width: 120
    height: 24
}
"""))
        dark_skeleton = keep[-1][1]
        _assert_skeleton(dark_skeleton, (38, 48, 58), (38, 48, 58))

        keep.append(_build(engine, b"""
import PrismQML
Tag {
    text: "Ready"
    status: Enums.statusLevel.success
}
"""))
        dark_tag = keep[-1][1]
        _assert_tag(dark_tag, (27, 51, 24), (108, 203, 95))
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
