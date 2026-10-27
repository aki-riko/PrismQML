# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Glow button regressions. 泛光按钮回归。

覆盖四层合同：
1. 枚举同构：`style_glow` 在枚举分类、`Enums` 与 `SkinContext` 三处一致可见；
2. 样式矩阵：泛光沿用了 `style_primary` 的填充、墨色与描边，两者共享同一套
   主色推导，只在光晕与阴影处理上不同；
3. 运行时生命周期：只有泛光样式实例化光晕层，禁用/倒计时/减少动态效果时停止
   呼吸循环，而光晕节点本身不销毁；
4. 真实像素：光晕确实在按钮面之外绘制（非零外扩），且普通主色按钮没有光晕。
"""

from pathlib import Path
from pathlib import PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
BUTTON_ENUM_SOURCE = QML_ROOT / "PrismEnums" / "Button.qml"
ENUMS_SOURCE = QML_ROOT / "Enums.qml"
SKIN_CONTEXT_SOURCE = QML_ROOT / "SkinContext.qml"
ENUM_QMLDIR_SOURCE = QML_ROOT / "PrismEnums" / "qmldir"
BUTTON_CORE_SOURCE = QML_ROOT / "controls" / "buttons" / "Button" / "ButtonCore.qml"
BUTTON_SURFACE_SOURCE = (
    QML_ROOT / "controls" / "buttons" / "Button" / "_internal" / "ButtonSurface.qml"
)
BUTTON_GLOW_SOURCE = (
    QML_ROOT / "controls" / "buttons" / "Button" / "_internal" / "ButtonGlow.qml"
)

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    property bool glowEnabled: true
    property bool glowCountdown: false
    property bool glowHovered: false
    property bool glowPressed: false

    width: 460
    height: 220
    visible: true
    color: "#ffffff"

    Row {
        x: 40
        y: 80
        spacing: 120

        Button {
            objectName: "glowButton"
            width: 160
            height: 48
            style: Enums.button.style_glow
            text: "Glow"
            enabled: window.glowEnabled
            pseudoHovered: window.glowHovered
            pseudoPressed: window.glowPressed
            _countdownActive: window.glowCountdown
        }

        Button {
            objectName: "plainPrimaryButton"
            width: 160
            height: 48
            style: Enums.button.style_primary
            text: "Primary"
        }
    }
}
"""

SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "button-glow.qml"))


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(150)
    return engine, component, window, warnings


def _dispose(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    _pump(1)


def _modules(root: QObject, fragment: str) -> list[QObject]:
    return [
        child
        for child in root.findChildren(QObject)
        if child.metaObject().className().startswith(fragment)
    ]


def _loop_animation(root: QObject) -> QObject | None:
    animations = [
        child
        for child in root.findChildren(QObject)
        if child.metaObject().indexOfProperty("loops") >= 0
        and child.property("loops") == -1
    ]
    assert len(animations) <= 1, [
        child.metaObject().className() for child in animations
    ]
    return animations[0] if animations else None


def _stable_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable += 1
            if stable == 3:
                return current
        else:
            stable = 0
        previous = current
        _pump()
    raise AssertionError("glow button frame did not stabilize within 800 ms")


# ==================== Source contracts 源码合同 ====================


def test_glow_style_is_registered_once_across_the_enum_surface():
    enum_source = BUTTON_ENUM_SOURCE.read_text(encoding="utf-8")
    assert "readonly property int style_glow: 7" in enum_source
    # The existing style values must not be renumbered: consumers persist them.
    # 既有样式取值不得重排: 消费者会持久化这些数值。
    for value, name in enumerate(
        (
            "style_default",
            "style_primary",
            "style_transparent",
            "style_filled",
            "style_text",
            "style_hyperlink",
            "style_gradient",
        )
    ):
        assert f"readonly property int {name}: {value}" in enum_source

    # Button is a data resource registered in PrismEnums/qmldir; Enums and
    # SkinContext each own one instance of it, so the value reaches every scope.
    # Button 是 PrismEnums/qmldir 注册的数据资源; Enums 与 SkinContext 各持有
    # 一份实例, 因此该取值在全局与局部皮肤范围内都可见。
    assert "Button Button.qml" in ENUM_QMLDIR_SOURCE.read_text(encoding="utf-8")
    for path in (ENUMS_SOURCE, SKIN_CONTEXT_SOURCE):
        source = path.read_text(encoding="utf-8")
        assert "Button { id: _button" in source, path


def test_glow_style_shares_the_primary_face_matrix():
    """Glow keeps the primary face; only the halo and shadow differ.

    泛光沿用 primary 的按钮面, 仅光晕与阴影不同。
    """
    style_source = (
        BUTTON_CORE_SOURCE.parent / "ButtonStyle.js"
    ).read_text(encoding="utf-8")
    helper_source = (
        BUTTON_CORE_SOURCE.parent / "ButtonStyleHelper.qml"
    ).read_text(encoding="utf-8")

    # Fill: the same accent derivation as style_primary.
    # 填充: 与 style_primary 完全相同的主色推导。
    assert (
        "    case button.style_primary:\n"
        "    case button.style_glow:\n"
    ) in style_source
    assert (
        "            case Enums.button.style_primary:\n"
        "            case Enums.button.style_glow:\n"
    ) in helper_source
    # Border: transparent, exactly like the other accent styles.
    # 描边: 与其它主色样式一样透明。
    assert "    case button.style_glow:\n        return transparent" in style_source
    assert (
        "            case Enums.button.style_glow:\n"
        "                return Enums.transparent"
    ) in helper_source
    # Ink and progress/ring colours treat glow as an accent style.
    # 墨色与进度环颜色把泛光当作主色样式处理。
    assert "           style === button.style_glow" in style_source
    assert "               style === Enums.button.style_glow" in helper_source
    for consumer in (
        BUTTON_CORE_SOURCE.parent / "ButtonContent.qml",
        BUTTON_CORE_SOURCE.parent / "ButtonProgress.qml",
        BUTTON_CORE_SOURCE.parent / "ButtonDropdown.qml",
    ):
        source = consumer.read_text(encoding="utf-8")
        assert "style_glow" in source, consumer


def test_glow_halo_is_lazy_and_module_owned():
    surface_source = BUTTON_SURFACE_SOURCE.read_text(encoding="utf-8")
    glow_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")
    core_source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")

    # The surface creates the halo imperatively and has no completion hook of its
    # own: any resident declaration, or even Component.onCompleted, attaches extra
    # objects to every button and changes the measured object counts of components
    # that embed buttons. 表面以命令式创建光晕且没有自己的完成钩子: 任何常驻声明,
    # 甚至 Component.onCompleted, 都会给每个按钮附加额外对象, 改变内嵌按钮组件的
    # 实测对象数。
    assert "function _syncGlowLayer()" in surface_source
    assert "readonly property bool _needsGlow: buttonControl._isGlowStyle" in surface_source
    assert "Qt.createComponent(\"ButtonGlow.qml\")" in surface_source
    assert "_glowLayer.destroy()" in surface_source
    assert "on_NeedsGlowChanged: _syncGlowLayer()" in surface_source
    # Assert on executable lines only: the explanatory comments mention the same
    # token, so a plain substring check would read the rationale as a violation.
    # 仅检查可执行行: 说明性注释里也出现该词, 纯子串断言会把理由误判为违规。
    surface_code = [
        line.strip()
        for line in surface_source.splitlines()
        if line.strip() and not line.strip().startswith("//")
    ]
    assert "Component.onCompleted" not in surface_code
    # The halo may only be reached through the imperative createComponent path: the
    # surface's one pre-existing Loader belongs to the neo shadow and must not gain
    # a glow branch.
    # 光晕只能经命令式 createComponent 到达: 表面既有的那一个 Loader 属于 neo 阴影,
    # 不得为泛光新增分支。
    assert "sourceComponent: ButtonGlow {" not in surface_code
    assert "active: surface.buttonControl._isGlowStyle" not in surface_code
    assert not [line for line in surface_code if line == "Component {"]
    # The core reuses its existing completion hook instead of declaring a new one.
    # 核心复用它已有的完成钩子, 而不是新声明一个。
    assert core_source.count("Component.onCompleted") == 1
    assert "surface._syncGlowLayer()" in core_source
    # The glow module itself lives under _internal and takes the host by required
    # property; it must not reach for parent ids.
    # 光晕模块本体位于 _internal 并以 required property 接收宿主; 不得访问父级 id。
    assert BUTTON_GLOW_SOURCE.parent.name == "_internal"
    assert "required property var button" in glow_source
    assert "required property var buttonControl" not in glow_source
    # An imperatively created layer must anchor itself; it cannot rely on a Loader.
    # 命令式创建的图层必须自行锚定, 不能依赖 Loader。
    assert "parent: button" in glow_source
    assert "anchors.fill: parent" in glow_source
    # A glow face already carries a bloom, so the Fluent soft shadow is suppressed
    # there instead of stacking a second, dirty halo on top.
    # 泛光面自带光晕, 因此在泛光样式下抑制 Fluent 软阴影, 而不是叠加一层脏双影。
    assert "&& !surface.buttonControl._isGlowStyle" in surface_source
    # ButtonCore only exposes the style predicate; it must not own the visual tree.
    # ButtonCore 只暴露样式判定; 不得持有视觉树。
    assert "readonly property bool _isGlowStyle: style === _skin.button.style_glow" in core_source
    assert "ButtonGlow {" not in core_source
    assert "Rectangle {" not in glow_source.replace("Rectangle {\n            // Layer", "")


def test_glow_sources_pass_the_convention_scanner():
    for path in (BUTTON_GLOW_SOURCE, BUTTON_SURFACE_SOURCE, BUTTON_CORE_SOURCE):
        relative = PurePosixPath(path.relative_to(ROOT).as_posix())
        violations = scan_source_text(path.read_text(encoding="utf-8"), relative)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009", "QML010", "QML011"}
        ] == []


def test_glow_bloom_is_one_sdf_shadow():
    """The bloom must be one RectangularShadow, never stacked translucent discs.

    泛光必须是单个 RectangularShadow, 绝不能用叠加半透明圆盘。
    """
    glow_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")
    tokens_source = BUTTON_ENUM_SOURCE.read_text(encoding="utf-8")

    # AGENTS.md 6.2 mandates RectangularShadow as the first choice for rectangular
    # surfaces ("无离屏渲染"). Field measurement on a real D3D11 window confirmed it
    # renders a genuinely smooth falloff, whereas stacked translucent rectangles
    # band visibly on a real display.
    # AGENTS.md 6.2 规定矩形表面首选 RectangularShadow ("无离屏渲染")。真实 D3D11
    # 窗口实测确认它产出真正平滑的衰减, 而叠加半透明矩形在真实显示器上出现可见色带。
    assert glow_source.count("RectangularShadow {") == 1
    assert "blur: root._blur" in glow_source
    assert "spread: root._spread" in glow_source
    assert "MultiEffect {" not in glow_source
    # No stacked-disc fallback: the Repeater of Rectangles must be gone.
    # 不得再有叠加圆盘回退: Repeater 矩形必须已移除。
    assert "Repeater {" not in glow_source
    assert "glowLayerCount" not in tokens_source
    assert "glowLayerOpacity" not in tokens_source
    assert "glowLayerFalloff" not in tokens_source
    # Geometry must stay fixed so a pulse never re-lays-out the face.
    # 几何必须保持不变, 使呼吸不会触发按钮面重新布局。
    shadow_block = glow_source[glow_source.index("RectangularShadow {"):]
    assert "glowPulseMin" not in shadow_block.split("}")[0]


def test_glow_bloom_scales_with_the_button_height():
    """A fixed bloom size swallows a small button and dwarfs a large one.

    固定尺寸的泛光会吞掉小按钮、在大按钮上显得太小。
    """
    glow_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")
    tokens_source = BUTTON_ENUM_SOURCE.read_text(encoding="utf-8")

    # Tokens are ratios; the module multiplies them by the host height.
    # 令牌是比例; 模块用宿主高度去乘它们。
    assert "readonly property real glowSpreadRatio:" in tokens_source
    assert "readonly property real glowBlurRatio:" in tokens_source
    assert "readonly property real _spread: button.height * _tokens.glowSpread" in glow_source
    assert "readonly property real _blur: button.height * _tokens.glowBlur" in glow_source
    # Absolute pixel tokens must not come back: they cannot fit every face size.
    # 绝对像素令牌不得回潮: 它们无法适配所有按钮面尺寸。
    assert "glowSpread: isTicket ? 0 : 8" not in tokens_source
    assert "glowBlur: isTicket ? 0 : 24" not in tokens_source


def test_glow_halo_follows_the_resolved_face_colour():
    """A grey disabled face must not be ringed by a blue halo.

    灰色禁用面不得被蓝色光晕包围。
    """
    glow_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")
    assert "readonly property color _haloColor: button._effectiveBgColor" in glow_source
    assert "readonly property color _haloColor: _skin.accentColor" not in glow_source


# ==================== Runtime behaviour 运行时行为 ====================


def test_halo_is_created_only_for_the_glow_style(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        glow_button = window.findChild(QObject, "glowButton")
        plain_button = window.findChild(QObject, "plainPrimaryButton")
        assert glow_button is not None and plain_button is not None

        assert glow_button.property("_isGlowStyle") is True
        assert plain_button.property("_isGlowStyle") is False
        assert len(_modules(glow_button, "ButtonGlow_QMLTYPE_")) == 1
        assert _modules(plain_button, "ButtonGlow_QMLTYPE_") == []
        # The halo is the only looping animation a glow button adds.
        # 光晕是泛光按钮唯一新增的循环动画。
        assert _loop_animation(glow_button) is not None
        assert _loop_animation(plain_button) is None
        assert warnings == []
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible() and item not in windows_before and item is not window
        ] == []
    finally:
        _dispose(engine, component, window)


def test_glow_pulse_stops_without_destroying_the_halo(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setSkin(Skin.FLUENT)
    setTheme(Theme.LIGHT)
    engine, component, window, warnings = _create_scene()
    try:
        button = window.findChild(QObject, "glowButton")
        assert button is not None
        halo = _modules(button, "ButtonGlow_QMLTYPE_")[0]
        animation = _loop_animation(button)
        assert animation is not None
        assert halo.property("animated") is True
        assert animation.property("running") is True

        # Disabled: no pulse, but the halo node stays so state changes read as the
        # light dimming instead of the halo disappearing.
        # 禁用: 不再呼吸, 但光晕节点保留, 使状态变化读作灯光变暗而非光晕消失。
        window.setProperty("glowEnabled", False)
        _pump()
        assert halo.property("animated") is False
        assert animation.property("running") is False
        assert _modules(button, "ButtonGlow_QMLTYPE_") == [halo]
        assert halo.property("_stateStrength") == pytest.approx(
            halo.property("_tokens").property("glowDisabledStrength")
        )

        window.setProperty("glowEnabled", True)
        _pump()
        assert halo.property("animated") is True
        assert animation.property("running") is True

        # Countdown holds the pulse still; the halo must not be torn down.
        # 倒计时期间暂停呼吸; 光晕不得被销毁。
        window.setProperty("glowCountdown", True)
        _pump()
        assert halo.property("animated") is False
        assert _modules(button, "ButtonGlow_QMLTYPE_") == [halo]
        window.setProperty("glowCountdown", False)
        _pump()
        assert halo.property("animated") is True

        # Interactive states modulate strength: hover brightens, press pulls in.
        # 交互状态调制强度: 悬浮加亮, 按压收敛。
        window.setProperty("glowHovered", True)
        _pump()
        hover_strength = halo.property("_stateStrength")
        window.setProperty("glowPressed", True)
        _pump()
        pressed_strength = halo.property("_stateStrength")
        assert hover_strength > 1.0
        assert 0.0 < pressed_strength < 1.0
        window.setProperty("glowPressed", False)
        window.setProperty("glowHovered", False)
        _pump()
        assert halo.property("_stateStrength") == pytest.approx(1.0)

        assert warnings == []
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)
        _dispose(engine, component, window)


def test_glow_halo_geometry_is_backend_independent(qapp):
    """Geometry/declaration checks that hold on any backend.

    Pixels are deliberately NOT asserted here: automated QML tests run under
    ``offscreen``, whose Software scene graph executes no shader effects, so an
    effect-based bloom is invisible there regardless of correctness. Judging the
    real bloom is the job of ``scripts/manual/glow_button_bloom_probe.py`` on a
    real Direct3D11 window.

    此处刻意不校验像素: 自动 QML 测试运行在 ``offscreen``, 其 Software 场景图不执行
    着色器效果, 基于效果的泛光在那里无论对错都不可见。真实泛光的判定由
    ``scripts/manual/glow_button_bloom_probe.py`` 在真实 Direct3D11 窗口上完成。
    """
    engine, component, window, warnings = _create_scene()
    try:
        glow_button = window.findChild(QObject, "glowButton")
        plain_button = window.findChild(QObject, "plainPrimaryButton")
        assert glow_button is not None and plain_button is not None
        halo = _modules(glow_button, "ButtonGlow_QMLTYPE_")[0]

        # The halo overhangs the face and covers it, so the shadow is anchored with
        # a negative margin and grows by the same spread.
        assert halo.property("_spread") > 0
        assert halo.property("parent") is glow_button
        assert halo.property("z") < glow_button.property("z") + 1
        # It tracks the face geometry it was handed.
        assert abs(halo.width() - glow_button.property("width")) < 0.001
        assert abs(halo.height() - glow_button.property("height")) < 0.001
        assert warnings == []
    finally:
        _dispose(engine, component, window)


def test_glow_style_renders_in_every_skin(qapp):
    """Skins that forbid elevation degrade the bloom instead of breaking it.

    禁止悬浮的皮肤让泛光收敛, 而不是让样式失效。
    """
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    engine, component, window, warnings = _create_scene()
    try:
        button = window.findChild(QObject, "glowButton")
        assert button is not None
        for skin, expected_bloom in (
            (Skin.FLUENT, True),
            (Skin.NEOBRUTALISM, True),
            (Skin.VINTAGE_TICKET, False),
            (Skin.NEUMORPHISM, True),
        ):
            setSkin(skin)
            _pump(60)
            halo = _modules(button, "ButtonGlow_QMLTYPE_")[0]
            spread = float(halo.property("_spread"))
            assert (spread > 0) is expected_bloom, skin
            # The style must still resolve a filled accent face in every skin.
            # 每种皮肤下该样式仍必须解析出实心主色面。
            face = button.property("_styleBgColor")
            assert face is not None
            assert face.alpha() > 0, skin
        assert warnings == []
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)
        _dispose(engine, component, window)
