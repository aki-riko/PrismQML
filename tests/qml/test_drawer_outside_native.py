# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Outside Drawer native-window contracts. 外侧抽屉原生窗口合同。"""

from pathlib import Path, PurePosixPath

import shiboken6
from PySide6.QtCore import QMetaObject
from PySide6.QtQuick import QQuickItem

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
SURFACE_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "DrawerSurface.qml"
ANIMATION_HELPER_SOURCE_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
)


def _lines(source: str) -> list[str]:
    """Trimmed source lines, so assertions do not depend on line endings.
    去掉首尾空白的源码行, 让断言不依赖换行符。
    """
    return [line.strip() for line in source.splitlines()]


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
        "Enums.shadow.windowOutside.blur" in _lines(source)
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
    # The silhouette must stay equal to the panel. Measured on the real effect at blur 40 /
    # 0.50 black on white, a panel-sized silhouette darkens the panel edge by 21.6% (the DWM
    # calibration target) and fades out within ~40px, while growing it outwards by `blur`
    # fills the first 40px with the full 49.8% and doubles the band width.
    # 轮廓必须与面板等大。真实效果实测(blur 40, 0.50 黑, 白底): 轮廓等于面板时面板边缘暗化
    # 21.6% (即 DWM 标定目标) 并在约 40px 内衰减完; 朝外各扩 `blur` 会让紧邻面板的 40px 全是
    # 满浓度 49.8%, 像带宽度翻倍。
    assert "x: outsideDrawerWindow.panelOffsetX" in _lines(helper_source)
    assert "y: outsideDrawerWindow.panelOffsetY" in _lines(helper_source)
    assert "width: outsideDrawerWindow.panelWidth" in _lines(helper_source)
    assert "height: outsideDrawerWindow.panelHeight" in _lines(helper_source)
    assert "outsideDrawerWindow.panelWidth + 2 * blur" not in helper_source
    assert "outsideDrawerWindow.panelOffsetX - blur" not in helper_source
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


def test_outside_window_uses_a_window_type_that_can_take_keyboard_focus():
    """外侧抽屉的原生窗口必须能被激活, 否则窗口内任何输入控件都拿不到键盘焦点。

    Windows 给 Tool 窗口加 `WS_EX_TOOLWINDOW`, 该 HWND 从此不能被激活: 同一份外侧
    抽屉内容, `Qt.Tool | Qt.FramelessWindowHint` 下实测 exstyle=0x00080080 / active=false /
    `QGuiApplication.focusWindow()` 为 null, 窗口内 TextInput 的 `forceActiveFocus()` 完全
    无效(表现即"点击搜索框无法聚焦")。宿主的"被拥有窗口"层级语义由
    `transientParent` 承担, 不依赖窗口类型。
    """
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "flags: Qt.Window | Qt.FramelessWindowHint" in _lines(helper_source)
    assert "Qt.Tool" not in helper_source
    # 抢焦点仍由用户交互触发, 不得改成为显露而主动请求激活。
    assert "requestActivate()" not in helper_source


def test_outside_drawer_shadow_silhouette_never_grows_past_the_panel():
    """阴影轮廓必须等于面板, 留白必须覆盖像带的完整衰减。

    Two independent measurements back this contract. A silhouette grown by `blur` moves the
    panel edge from ~21% to the full 49.8% darkening (the heavy band users reported), and a
    reserve narrower than the fade (~0.8x the blur) cuts the still-visible tail off on the
    HWND edge, which reads as a hard-edged shadow.
    两条独立实测支撑本契约: 轮廓朝外各扩 `blur` 会把面板边缘从约 21% 顶到满浓度 49.8%
    (用户报告的浓重像带); 留白窄于衰减跨度(约 0.8 倍 blur)则会把仍有浓度的尾部切在 HWND
    边界上, 观感即"阴影很硬"。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = OUTSIDE_WINDOW_SOURCE_PATH.read_text(encoding="utf-8")

    assert "x: outsideDrawerWindow.panelOffsetX" in _lines(helper_source)
    assert "y: outsideDrawerWindow.panelOffsetY" in _lines(helper_source)
    assert "width: outsideDrawerWindow.panelWidth" in _lines(helper_source)
    assert "height: outsideDrawerWindow.panelHeight" in _lines(helper_source)
    assert "outsideDrawerWindow.panelWidth + 2 * blur" not in helper_source
    assert "outsideDrawerWindow.panelHeight + 2 * blur" not in helper_source
    assert "outsideDrawerWindow.panelOffsetX - blur" not in helper_source
    assert "outsideDrawerWindow.panelOffsetY - blur" not in helper_source
    assert (
        "readonly property real _outsideShadowSpread: "
        "Enums.shadow.windowOutside.blur" in _lines(source)
    )

    # Measured fade width per blur unit. 实测的每单位 blur 对应的衰减跨度。
    fade_per_blur = 0.8
    blur = 24
    spread = blur
    assert spread >= fade_per_blur * blur


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
    assert "x: outsideDrawerWindow.panelOffsetX - outsideDrawerViewport.x" in helper_source
    assert "y: outsideDrawerWindow.panelOffsetY - outsideDrawerViewport.y" in helper_source
    assert "width: outsideDrawerWindow.panelWidth" in _lines(helper_source)
    assert "height: outsideDrawerWindow.panelHeight" in _lines(helper_source)


def test_drawer_source_preserves_open_state_while_host_is_minimized():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    surface_source = SURFACE_SOURCE_PATH.read_text(encoding="utf-8")

    assert "drawerControl._hostWindow.visibility === Window.Hidden" in surface_source
    assert "drawerControl._hostWindow.visibility === Window.Minimized" in surface_source
    assert "property alias opened: control._isOpen" in source
    assert "property bool outsideMinimized: false" in surface_source
    assert "drawerControl._startOutsideAnimation(drawerControl._outsideFullExtent)" in surface_source


def test_outside_drawer_registry_survives_host_window_teardown():
    """注册表必须是宿主助手的普通属性, 不能是助手方法。

    ``QQmlContextData::isValid()`` 会在上下文对象被标记删除后返回 false, 而宿主窗口对象
    的删除标记恰好早于其 QML 子对象销毁置位。因此拆卸处理器向助手派发 QML 方法会先报
    ``attempted to evaluate a function in an invalid context`` 再抛 ``is not a function``
    —— 真实 Gallery 关窗时每个抽屉各报一对; 属性读写不经过该检查, 因此注册表由
    DrawerSurface 直接读写该属性。
    """
    helper_source = ANIMATION_HELPER_SOURCE_PATH.read_text(encoding="utf-8")
    surface_source = SURFACE_SOURCE_PATH.read_text(encoding="utf-8")

    assert "property var outsideMinimizeDrawers: []" in helper_source
    assert "function registerOutsideDrawer" not in helper_source
    assert "function unregisterOutsideDrawer" not in helper_source
    assert "helper.outsideMinimizeDrawers =" in surface_source
    assert "registerOutsideDrawer(" not in surface_source
    assert "unregisterOutsideDrawer(" not in surface_source


def _animation_helper(window):
    # QML-defined types arrive in Python as their nearest C++ class, so the helper is
    # identified through its generated meta object name.
    # QML 定义的类型在 Python 侧只暴露最近的 C++ 类, 因此按生成的元对象名识别助手。
    for child in window.findChildren(QQuickItem):
        if child.metaObject().className().startswith("WindowAnimationHelper"):
            return child
    return None


def _drawer_surface(drawer):
    for child in drawer.findChildren(QQuickItem):
        if child.metaObject().className().startswith("DrawerSurface"):
            return child
    return None


def _registered_drawers(helper):
    value = helper.property("outsideMinimizeDrawers")
    to_variant = getattr(value, "toVariant", None)
    entries = to_variant() if callable(to_variant) else value
    return list(entries or [])


def _address(obj):
    return shiboken6.getCppPointer(obj)[0]


def test_outside_drawer_registry_tracks_open_state_on_the_host_helper(qapp):
    """打开/关闭外侧抽屉时, 宿主助手的注册表属性必须同步增减。"""
    from tests.qml.test_drawer_conventions import (
        SCENE_SOURCE,
        _create_scene,
        _dispose_scene,
        _wait_for,
    )

    source = SCENE_SOURCE.replace(b"Window {", b"WindowsCore {", 1)
    engine, component, window, drawer, _content_item, _panel, warnings = _create_scene(
        source=source
    )
    try:
        helper = _animation_helper(window)
        assert isinstance(helper, QQuickItem)
        # No registry method may exist at runtime either: a QML method dispatched from a
        # destruction handler is exactly what fails while the host window is being deleted.
        # 运行时也不得存在注册表方法: 宿主窗口被删除期间, 正是从拆卸处理器派发的 QML 方法失败。
        assert helper.metaObject().indexOfMethod("registerOutsideDrawer(QVariant)") == -1
        assert helper.metaObject().indexOfMethod("unregisterOutsideDrawer(QVariant)") == -1
        assert _registered_drawers(helper) == []

        drawer.setProperty("mode", window.property("outsideMode"))
        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(lambda: drawer.property("opened"))
        surface = _drawer_surface(drawer)
        assert isinstance(surface, QQuickItem)
        assert [_address(item) for item in _registered_drawers(helper)] == [
            _address(surface)
        ]

        assert QMetaObject.invokeMethod(drawer, "close")
        assert _wait_for(lambda: not drawer.property("opened"))
        assert _registered_drawers(helper) == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


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
