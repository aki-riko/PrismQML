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


def test_drawer_source_follows_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []


def test_drawer_source_uses_clipped_native_window_following():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "Qt.NoFluentShadowWindowHint" not in source
    assert "Qt.NoDropShadowWindowHint" not in source
    assert "_outsideShadowExtent" not in source
    assert 'objectName: "outsideDrawerShadow"' not in source
    assert "ShadowManager.enableShadowForWindow(_outsideDrawerWindow)" in source
    assert "MicaManager.setWindowCorner(_outsideDrawerWindow, true)" in source
    assert "id: outsideOpeningTimer" not in source
    assert "id: outsideVisibilityTimer" not in source
    assert "Behavior on width" not in source
    assert "Behavior on height" not in source
    assert 'id: outsideGeometryAnimation' in source
    assert 'property: "_outsideExtent"' in source
    assert 'objectName: "outsideDrawerViewport"' in source
    assert "clip: true" in source
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


def test_drawer_source_keeps_native_window_behind_host_without_overlap():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "transientParent: null" in source
    assert "outsideDrawerWindow.requestActivate()" not in source
    assert "_outsideSeamOverlap" not in source
    assert "? Enums.radius.large" in source
    assert "topLeftRadius:" in source
    assert "topRightRadius:" in source
    assert "bottomLeftRadius:" in source
    assert "bottomRightRadius:" in source


def test_drawer_source_guards_native_window_during_destruction():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "readonly property var _outsideDrawerWindow: outsideDrawerWindowLoader.item" in source
    assert "id: outsideDrawerWindowLoader" in source
    assert "active: control._isOutside" in source
    assert "asynchronous: false" in source
    assert "if (_outsideDrawerWindow" in source
    assert "|| !_outsideDrawerWindow" in source
    assert "width: outsideDrawerWindow.width" in source
    assert "height: outsideDrawerWindow.height" in source
    assert "x: -outsideDrawerViewport.x" in source
    assert "y: -outsideDrawerViewport.y" in source


def test_drawer_stages_host_signal_connections_until_component_completion():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "property var _hostSignalTarget: null" in source
    assert "control._hostSignalTarget = Qt.binding(function()" in source
    assert "return control._hostWindow" in source
    assert "target: control._hostSignalTarget" in source
    assert "target: control._hostWindow" not in source


def test_drawer_source_reveals_from_the_corresponding_edge():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "x: control.position === Enums.position.left" in source
    assert "? outsideDrawerWindow.width - width : 0" in source
    assert "y: control.position === Enums.position.top" in source
    assert "? outsideDrawerWindow.height - height : 0" in source
