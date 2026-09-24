# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Outside Drawer native-window contracts. 外侧抽屉原生窗口合同。"""

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Drawer"
    / "Drawer.qml"
)
OUTSIDE_WINDOW_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "DrawerOutsideWindow.qml"


def test_drawer_source_follows_conventions():
    for source_path in (SOURCE_PATH, OUTSIDE_WINDOW_SOURCE_PATH):
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []


def test_drawer_source_uses_clipped_native_window_following():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "Qt.NoFluentShadowWindowHint" in helper_source
    assert "Qt.NoDropShadowWindowHint" not in source
    assert "_outsideShadowExtent" in source
    assert 'objectName: "outsideDrawerShadow"' not in source
    assert "ShadowManager.enableShadowForWindow(_outsideDrawerWindow)" not in source
    assert "MicaManager.setWindowCorner(_outsideDrawerWindow, true)" in source
    assert "id: outsideOpeningTimer" not in source
    assert "id: outsideVisibilityTimer" not in source
    assert "Behavior on width" not in source
    assert "Behavior on height" not in source
    assert 'id: outsideGeometryAnimation' in source
    assert 'property: "_outsideExtent"' in source
    assert 'objectName: "outsideDrawerViewport"' in helper_source
    assert "clip: true" in helper_source
    assert "on_OutsideExtentChanged" not in source
    assert "control._syncOutsideWindowGeometry()" not in source
    assert source.count("WindowHelper.updateWindowFollowerGeometry(") == 1
    assert "WindowHelper.registerWindowFollower(" in source
    assert "WindowHelper.unregisterWindowFollower(_outsideDrawerWindow)" in source
    assert "ShadowManager.disableShadowForWindow(_outsideDrawerWindow)" in source
    assert "property var _outsideNativeShadowState: null" in source
    assert "if (_outsideNativeShadowState === enabled) return" in source
    assert "if (applied) _outsideNativeShadowState = enabled" in source
    assert "onItemChanged: control._outsideNativeShadowState = null" in source
    assert "Three outward shadow edges" in helper_source


def test_drawer_source_keeps_native_window_above_host_without_overlap():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "transientParent: control._hostWindow" in helper_source
    assert "outsideDrawerWindow.requestActivate()" not in helper_source
    assert "_outsideSeamOverlap" not in helper_source
    assert "control._outsideWindowExtent,\n            true)" in source
    assert "? Enums.radius.large" in source
    assert "topLeftRadius:" in helper_source
    assert "topRightRadius:" in helper_source
    assert "bottomLeftRadius:" in helper_source
    assert "bottomRightRadius:" in helper_source


def test_drawer_source_guards_native_window_during_destruction():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "readonly property var _outsideDrawerWindow: outsideDrawerWindowLoader.item" in source
    assert "id: outsideDrawerWindowLoader" in source
    assert "active: control._isOutside" in source
    assert "asynchronous: false" in source
    assert "if (_outsideDrawerWindow" in source
    assert "|| !_outsideDrawerWindow" in source
    assert "width: control.drawerWidth" in helper_source
    assert "height: control.drawerHeight" in helper_source
    assert "x: 0" in helper_source
    assert "y: 0" in helper_source


def test_drawer_source_preserves_open_state_while_host_is_minimized():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "control._hostWindow.visibility === Window.Hidden" in source
    assert "|| control._hostWindow.visibility === Window.Minimized" not in source
    assert "control._hostWindow.visibility !== Window.Minimized" in source


def test_drawer_stages_host_signal_connections_until_component_completion():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "property var _hostSignalTarget: null" in source
    assert "control._hostSignalTarget = Qt.binding(function()" in source
    assert "return control._hostWindow" in source
    assert "target: control._hostSignalTarget" in source
    assert "target: control._hostWindow" not in source


def test_drawer_source_reveals_from_the_corresponding_edge():
    source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "x: control.position === Enums.position.left" in source
    assert "? control._outsideShadowExtent : 0" in source
    assert "y: control.position === Enums.position.top" in source
    assert "? control._outsideShadowExtent : 0" in source
