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

    assert "Qt.NoFluentShadowWindowHint" not in source
    assert "Qt.NoDropShadowWindowHint" not in source
    assert "ShadowManager.enableShadowForWindow" not in source
    assert "_outsideShadowExtent" not in source
    assert 'objectName: "outsideDrawerShadow"' not in source
    assert "ShadowManager.disableShadowForWindow(_outsideDrawerWindow)" in source
    assert "MicaManager.setWindowCorner(_outsideDrawerWindow, false)" in source
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
    assert "property bool _outsideNativeShadowCleared: false" in source
    assert "if (control._outsideNativeShadowCleared || !_outsideDrawerWindow" in source
    assert "onItemChanged: control._outsideNativeShadowCleared = false" in source


def test_outside_window_owns_its_outward_shadow():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    # The HWND reserves the window-outward shadow padding and paints that shadow itself.
    assert (
        "readonly property real _outsideShadowSpread: "
        "Enums.shadow.windowOutside.blur" in source
    )
    assert (
        "readonly property real _outsideWindowExtent: "
        "_outsideFullExtent + _outsideShadowSpread" in source
    )
    assert (
        "readonly property bool _outsideShadowActive: _outsidePrepared && _isOpen"
        in source
    )
    assert "RectangularShadow {" in helper_source
    assert "anchors.fill: outsideDrawerViewport" in helper_source
    assert "blur: Enums.shadow.windowOutside.blur" in helper_source
    assert "color: Enums.shadow.windowOutside.color" in helper_source
    assert "offset.x: 0" in helper_source
    assert "offset.y: Enums.shadow.windowOutside.offset" in helper_source
    assert "visible: control._outsideShadowActive && !Enums.isVintageTicket" in helper_source
    # The panel keeps a uniform radius; the shadow squares off the seam side so that no
    # shadow arc is painted inside the window along the host edge.
    assert "radius: control._effectiveRadius" in helper_source
    for name in (
        "topLeftRadius:",
        "topRightRadius:",
        "bottomLeftRadius:",
        "bottomRightRadius:",
    ):
        assert helper_source.count(name) == 1
    assert (
        helper_source.count("? outsideDrawerPanel.radius : Enums.radius.none") == 4
    )


def test_drawer_source_keeps_native_window_above_host_without_overlap():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "transientParent: control._hostWindow" in helper_source
    assert "outsideDrawerWindow.requestActivate()" not in helper_source
    assert "_outsideSeamOverlap" not in helper_source
    assert (
        "control._outsideWindowExtent,\n"
        "            true,\n"
        "            control._outsideShadowSpread)" in source
    )
    # The panel keeps its requested extent; only the HWND grows outwards.
    assert "readonly property real panelWidth: control.isHorizontal" in helper_source
    assert (
        "width: control.isHorizontal ? panelWidth + spread : panelWidth + 2 * spread"
        in helper_source
    )
    assert (
        "height: control.isHorizontal ? panelHeight + 2 * spread : panelHeight + spread"
        in helper_source
    )


def test_drawer_source_guards_native_window_during_destruction():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "readonly property var _outsideDrawerWindow: outsideDrawerWindowLoader.item" in source
    assert "id: outsideDrawerWindowLoader" in source
    assert "active: control._isOutside" in source
    assert "asynchronous: false" in source
    assert "if (_outsideDrawerWindow" in source
    assert "|| !_outsideDrawerWindow" in source
    assert "width: outsideDrawerWindow.panelWidth" in helper_source
    assert "height: outsideDrawerWindow.panelHeight" in helper_source
    assert "x: outsideDrawerWindow.panelOffsetX - outsideDrawerViewport.x" in helper_source
    assert "y: outsideDrawerWindow.panelOffsetY - outsideDrawerViewport.y" in helper_source


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

    assert "? panelOffsetX : (control.isHorizontal ? width - clipExtent : panelOffsetX)" in source
    assert "? panelOffsetY : height - clipExtent" in source
    assert "x: outsideDrawerWindow.viewportX" in source
    assert "y: outsideDrawerWindow.viewportY" in source
    assert "width: control.isHorizontal ? outsideDrawerWindow.clipExtent" in source
    assert "height: control.isHorizontal ? outsideDrawerWindow.panelHeight" in source
