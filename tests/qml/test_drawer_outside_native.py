# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Outside Drawer native-window contracts. 外侧抽屉原生窗口合同。"""

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text

from prismqml.python.core._window_follower import (
    _WindowRect,
    _follower_rect_for_extent,
)
from prismqml.python.core.window_helper import (
    WINDOW_EDGE_BOTTOM,
    WINDOW_EDGE_LEFT,
    WINDOW_EDGE_RIGHT,
    WINDOW_EDGE_TOP,
)


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
    # The shadow silhouette is the panel rectangle grown outwards by `blur`: the effect
    # spreads its blur into AND out of the rectangle it is given, so a silhouette equal
    # to the panel hides the outer half of the band on every side and the dark band
    # starts short of the panel edge — the reported clipped shadow.
    # 阴影轮廓是面板矩形朝外各扩 `blur`: 该效果的模糊会同时向轮廓内外铺开, 轮廓等于面板
    # 会让每条边的外半边像带不可见, 暗带起点落在面板边缘内侧 —— 即所报告的阴影被裁剪。
    assert "x: outsideDrawerWindow.panelOffsetX - blur" in helper_source
    assert "y: outsideDrawerWindow.panelOffsetY - blur" in helper_source
    assert "width: outsideDrawerWindow.panelWidth + 2 * blur" in helper_source
    assert "height: outsideDrawerWindow.panelHeight + 2 * blur" in helper_source
    assert "anchors.fill: outsideDrawerViewport" not in helper_source
    assert "blur: Enums.shadow.windowOutside.blur" in helper_source
    assert "color: Enums.shadow.windowOutside.color" in helper_source
    assert "offset.x: 0" in helper_source
    assert "offset.y: Enums.shadow.windowOutside.offset" in helper_source
    assert "visible: control._outsideShadowActive && !Enums.isVintageTicket" in helper_source
    # Panel and shadow share one silhouette at full strength, so the bands run into the
    # seam and continue the host window's own shadow band on the other side. No fade,
    # retract or per-corner override is allowed back in.
    assert "radius: control._effectiveRadius" in helper_source
    assert "radius: outsideDrawerPanel.radius" in helper_source
    for name in (
        "topLeftRadius:",
        "topRightRadius:",
        "bottomLeftRadius:",
        "bottomRightRadius:",
    ):
        assert name not in helper_source
    assert "seamFade" not in helper_source
    assert "readonly property real retract:" not in helper_source
    assert "anchors.leftMargin" not in helper_source


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
    # The panel keeps its requested extent. The HWND grows by `spread` away from the host
    # edge and by `spread` on both sides across it, exactly like
    # _follower_rect_for_extent resolves the follower RECT; the panel's seam-facing edge
    # therefore lands flush on the host edge (no gap, no drawer shadow on the host).
    # 面板保持请求尺寸。HWND 朝外长 `spread`, 跨接缝方向两侧各长 `spread`, 与
    # _follower_rect_for_extent 解析的附属 RECT 完全一致; 面板朝接缝的边因此与宿主边缘齐平
    # (无缝隙, 抽屉阴影也不压宿主)。
    assert "readonly property real panelWidth: control.isHorizontal" in helper_source
    assert (
        "width: control.isHorizontal ? panelWidth + spread : panelWidth + 2 * spread"
        in helper_source
    )
    assert (
        "height: control.isHorizontal ? panelHeight + 2 * spread : panelHeight + spread"
        in helper_source
    )


def test_outside_window_size_matches_the_native_follower_rect():
    """QML 窗口尺寸必须与 Python 解析出的原生附属窗口 RECT 一致。

    The native geometry commit owns the real size, so a QML size that disagrees with
    _follower_rect_for_extent silently breaks the `width - clipExtent` reveal (a left
    drawer would reveal one `spread` off its seam). The two must stay the same formula.
    真实尺寸由原生几何提交决定, 因此与 _follower_rect_for_extent 不一致的 QML 尺寸会静默
    破坏按 `width - clipExtent` 计算的显露 (左侧抽屉会偏离接缝一个 `spread`)。两者必须同式。
    """
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert (
        "width: control.isHorizontal ? panelWidth + spread : panelWidth + 2 * spread"
        in helper_source
    )
    assert (
        "height: control.isHorizontal ? panelHeight + 2 * spread : panelHeight + spread"
        in helper_source
    )

    def qml_window_size(is_horizontal, panel_width, panel_height, spread):
        # Mirror of the two expressions above. 上面两个表达式的镜像。
        width = panel_width + spread if is_horizontal else panel_width + 2 * spread
        height = panel_height + 2 * spread if is_horizontal else panel_height + spread
        return width, height

    host = _WindowRect(100, 120, 900, 720)
    host_width = host.right - host.left
    host_height = host.bottom - host.top
    drawer_extent = 320
    spread = 60
    extent = drawer_extent + spread

    for edge, is_horizontal in (
        (WINDOW_EDGE_LEFT, True),
        (WINDOW_EDGE_RIGHT, True),
        (WINDOW_EDGE_TOP, False),
        (WINDOW_EDGE_BOTTOM, False),
    ):
        left, top, right, bottom = _follower_rect_for_extent(
            host, extent, edge, spread
        )
        native_size = (right - left, bottom - top)
        panel_width = drawer_extent if is_horizontal else host_width
        panel_height = host_height if is_horizontal else drawer_extent
        assert qml_window_size(
            is_horizontal, panel_width, panel_height, spread
        ) == native_size, edge


def test_drawer_source_guards_native_window_during_destruction():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "readonly property var _outsideDrawerWindow: outsideDrawerWindowLoader.item" in source
    assert "id: outsideDrawerWindowLoader" in source
    assert "active: control._isOutside" in source
    assert "asynchronous: false" in source
    assert "if (_outsideDrawerWindow" in source
    assert "|| !_outsideDrawerWindow" in source
    assert "width: outsideDrawerWindow.panelWidth + 2 * blur" in helper_source
    assert "height: outsideDrawerWindow.panelHeight + 2 * blur" in helper_source
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

    # The viewport hugs the host edge via `panelOffsetX`; the panel offset carries the
    # vertical `spread` room the shadow needs on both sides of the panel.
    # 视口通过 panelOffsetX 贴住宿主边; 面板偏移同时承载阴影在面板两侧所需的纵向 spread 空间。
    assert "? (control.position === Enums.position.left ? width - clipExtent" in source
    assert ": (control.position === Enums.position.top ? height - clipExtent" in source
    assert "x: outsideDrawerWindow.viewportX" in source
    assert "y: outsideDrawerWindow.viewportY" in source
    assert "width: control.isHorizontal ? outsideDrawerWindow.clipExtent" in source
    assert "height: control.isHorizontal ? outsideDrawerWindow.panelHeight" in source
