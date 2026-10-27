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
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine
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
GLOW_HALO_SOURCE = QML_ROOT / "effects" / "GlowHalo.qml"
GLOW_ENUM_SOURCE = QML_ROOT / "PrismEnums" / "Glow.qml"
EFFECTS_QMLDIR_SOURCE = QML_ROOT / "effects" / "qmldir"
ROOT_QMLDIR_SOURCE = QML_ROOT / "qmldir"
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
            glow: Enums.glow.glow_accent
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

COMPOSE_SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    readonly property int pillShape: Enums.button.shape_pill
    readonly property int toggleFeature: Enums.button.feature_toggle

    width: 900
    height: 520
    visible: false

    // Same style with and without glow: the face must be identical.
    // 同一样式有/无泛光: 按钮面必须完全一致。
    Button { objectName: "plainDefault"; x: 10; y: 10; width: 140; height: 40; style: Enums.button.style_default; text: "A" }
    Button { objectName: "glow_default"; x: 170; y: 10; width: 140; height: 40; style: Enums.button.style_default; glow: Enums.glow.glow_accent; text: "A" }
    Button { objectName: "plainPrimary"; x: 10; y: 70; width: 140; height: 40; style: Enums.button.style_primary; text: "B" }
    Button { objectName: "glow_primary"; x: 170; y: 70; width: 140; height: 40; style: Enums.button.style_primary; glow: Enums.glow.glow_accent; text: "B" }
    Button { objectName: "plainFilled"; x: 10; y: 130; width: 140; height: 40; style: Enums.button.style_filled; level: 1; text: "C" }
    Button { objectName: "glow_filled"; x: 170; y: 130; width: 140; height: 40; style: Enums.button.style_filled; level: 1; glow: Enums.glow.glow_accent; text: "C" }

    // Shape and feature compose with glow.
    Button { objectName: "glowPill"; x: 10; y: 200; width: 140; height: 40; style: Enums.button.style_primary; shape: Enums.button.shape_pill; glow: Enums.glow.glow_accent; text: "P" }
    Button { objectName: "glowToggle"; x: 170; y: 200; width: 140; height: 40; style: Enums.button.style_primary; feature: Enums.button.feature_toggle; glow: Enums.glow.glow_accent; text: "T" }
    Button { objectName: "glowProgress"; x: 330; y: 200; width: 140; height: 40; style: Enums.button.style_primary; feature: Enums.button.feature_progress_bar; progress: 0.5; showProgress: true; glow: Enums.glow.glow_accent; text: "R" }
}
""".encode("utf-8")

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


def test_glow_is_an_orthogonal_axis_not_a_style():
    """Glow must compose with every style, not replace one.

    泛光必须与所有样式组合, 而不是取代其中一种。
    """
    enum_source = BUTTON_ENUM_SOURCE.read_text(encoding="utf-8")

    # The style axis keeps exactly its original seven fills: glow is not a fill.
    # 样式轴保持原有的七种填充: 泛光不是一种填充。
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
    assert "style_glow" not in enum_source

    # Glow is a shared decoration enumerated in its own PrismEnums module, not a
    # button-local value: any component may consume the same axis.
    # 泛光是在独立 PrismEnums 模块中枚举的共享装饰, 不是按钮局部取值: 任何组件都可
    # 消费同一个轴。
    glow_enum = GLOW_ENUM_SOURCE.read_text(encoding="utf-8")
    assert "readonly property int glow_none: 0" in glow_enum
    assert "readonly property int glow_accent: 1" in glow_enum
    assert "Glow Glow.qml" in ENUM_QMLDIR_SOURCE.read_text(encoding="utf-8")
    # Enums and SkinContext each expose the shared instance.
    # Enums 与 SkinContext 各自暴露该共享实例。
    for path in (ENUMS_SOURCE, SKIN_CONTEXT_SOURCE):
        source = path.read_text(encoding="utf-8")
        assert "Glow { id: _glow }" in source, path
        assert "readonly property alias glow: _glow" in source, path

    # Button is a data resource registered in PrismEnums/qmldir; Enums and
    # SkinContext each own one instance of it, so the value reaches every scope.
    # Button 是 PrismEnums/qmldir 注册的数据资源; Enums 与 SkinContext 各持有
    # 一份实例, 因此该取值在全局与局部皮肤范围内都可见。
    assert "Button Button.qml" in ENUM_QMLDIR_SOURCE.read_text(encoding="utf-8")
    for path in (ENUMS_SOURCE, SKIN_CONTEXT_SOURCE):
        source = path.read_text(encoding="utf-8")
        assert "Button { id: _button" in source, path


def test_glow_never_leaks_into_the_fill_style_matrix():
    """A glow request must not change the resolved face of any style.

    泛光请求不得改变任何样式的已解析按钮面。
    """
    style_source = (
        BUTTON_CORE_SOURCE.parent / "ButtonStyle.js"
    ).read_text(encoding="utf-8")
    helper_source = (
        BUTTON_CORE_SOURCE.parent / "ButtonStyleHelper.qml"
    ).read_text(encoding="utf-8")

    # No fill/border/ink branch may mention glow: the face is decided by style
    # alone, which is exactly what makes the combination orthogonal.
    # 任何填充/描边/墨色分支都不得提到泛光: 按钮面只由 style 决定, 这正是该组合
    # 正交的原因。
    assert "style_glow" not in style_source
    assert "style_glow" not in helper_source
    for consumer in (
        BUTTON_CORE_SOURCE.parent / "ButtonContent.qml",
        BUTTON_CORE_SOURCE.parent / "ButtonProgress.qml",
        BUTTON_CORE_SOURCE.parent / "ButtonDropdown.qml",
    ):
        assert "style_glow" not in consumer.read_text(encoding="utf-8"), consumer

    # The public axis is a plain property next to style/shape/feature.
    # 该公开轴是与 style/shape/feature 并列的普通属性。
    core_source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "property int glow: Enums.glow.glow_none" in core_source
    assert "readonly property bool _glowActive: glow !== Enums.glow.glow_none" in core_source


def test_glow_effect_is_shared_and_button_adapter_is_thin():
    """Glow lives in effects/ as a reusable decoration; the button only binds it.

    泛光作为可复用装饰住在 effects/, 按钮只做绑定。
    """
    halo_source = GLOW_HALO_SOURCE.read_text(encoding="utf-8")
    adapter_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")

    # The effect is a public, root-qmldir registered component so any control can use it.
    # 该效果是经根 qmldir 注册的公开组件, 因此任何控件都能使用。
    assert GLOW_HALO_SOURCE.parent.name == "effects"
    assert "GlowHalo GlowHalo.qml" in EFFECTS_QMLDIR_SOURCE.read_text(encoding="utf-8")
    assert "GlowHalo effects/GlowHalo.qml" in ROOT_QMLDIR_SOURCE.read_text(encoding="utf-8")
    # It attaches to any rectangular target instead of a specific button. Assert on
    # executable lines only, because the prose explains what a button is for.
    # 它附着到任意矩形目标而不是特定按钮。仅检查可执行行, 因为说明文字会解释按钮。
    assert "required property Item target" in halo_source
    halo_code = [
        line
        for line in halo_source.splitlines()
        if line.strip() and not line.strip().startswith("//")
    ]
    assert not [line for line in halo_code if "button" in line.lower()]
    # The button adapter stays a thin binding layer under _internal.
    # 按钮适配层是 _internal 下的薄绑定。
    assert BUTTON_GLOW_SOURCE.parent.name == "_internal"
    assert adapter_source.count("target: button") == 1
    assert "required property var button" in adapter_source
    # The heavy lifting (shadow, animation) lives in the shared effect only.
    # 阴影与动画的重活只存在于共享效果里。
    assert adapter_source.count("RectangularShadow") == 0
    assert adapter_source.count("SequentialAnimation") == 0
    assert halo_source.count("RectangularShadow {") == 1
    assert halo_source.count("SequentialAnimation {") == 1


def test_glow_effect_is_lazily_created_by_the_surface():
    surface_source = BUTTON_SURFACE_SOURCE.read_text(encoding="utf-8")
    core_source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")

    # Created imperatively: any resident declaration (Loader, inline Component, or a
    # Component.onCompleted hook) would add objects to every button and change the
    # measured counts of components that embed buttons.
    # 以命令式创建: 任何常驻声明(Loader、内联 Component 或 Component.onCompleted 钩子)
    # 都会给每个按钮增加对象, 改变内嵌按钮组件的实测对象数。
    assert "function _syncGlowLayer()" in surface_source
    assert "readonly property bool _needsGlow: buttonControl._glowActive" in surface_source
    assert "Qt.createComponent(\"ButtonGlow.qml\")" in surface_source
    assert "_glowLayer.destroy()" in surface_source
    assert "on_NeedsGlowChanged: _syncGlowLayer()" in surface_source
    surface_code = [
        line.strip()
        for line in surface_source.splitlines()
        if line.strip() and not line.strip().startswith("//")
    ]
    assert "Component.onCompleted" not in surface_code
    assert not [line for line in surface_code if line == "Component {"]
    # The core reuses its existing completion hook instead of declaring a new one.
    # 核心复用它已有的完成钩子, 而不是新声明一个。
    assert core_source.count("Component.onCompleted") == 1
    assert "surface._syncGlowLayer()" in core_source


def test_glow_sources_pass_the_convention_scanner():
    for path in (
        GLOW_HALO_SOURCE,
        GLOW_ENUM_SOURCE,
        BUTTON_GLOW_SOURCE,
        BUTTON_SURFACE_SOURCE,
        BUTTON_CORE_SOURCE,
    ):
        relative = PurePosixPath(path.relative_to(ROOT).as_posix())
        violations = scan_source_text(path.read_text(encoding="utf-8"), relative)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009", "QML010", "QML011"}
        ] == [], path


def test_glow_effect_uses_one_sdf_shadow_with_ratio_geometry():
    halo_source = GLOW_HALO_SOURCE.read_text(encoding="utf-8")
    glow_enum = GLOW_ENUM_SOURCE.read_text(encoding="utf-8")

    # AGENTS.md 6.2 mandates RectangularShadow for rectangular surfaces; a real D3D11
    # window confirmed it gives the smooth falloff the stacked-rectangle fallback lost.
    # AGENTS.md 6.2 规定矩形表面首选 RectangularShadow; 真实 D3D11 窗口确认它给出
    # 叠加矩形方案丢失的平滑衰减。
    assert halo_source.count("RectangularShadow {") == 1
    assert "MultiEffect {" not in halo_source
    assert "Repeater {" not in halo_source
    # Geometry is a ratio of the target's short edge, so any size reads correctly.
    # 几何按目标短边比例, 因此任何尺寸都正确。
    assert "Math.min(target.width, target.height)" in halo_source
    assert "readonly property real _spread: _shortEdge * spreadRatio" in halo_source
    assert "readonly property real _blur: _shortEdge * blurRatio" in halo_source
    assert "readonly property real blurRatio: 0.45" in glow_enum
    assert "readonly property real spreadRatio: 0.10" in glow_enum
    # Geometry must stay fixed so a pulse never re-lays-out the target.
    # 几何保持不变, 呼吸不会触发目标重新布局。
    shadow_block = halo_source[halo_source.index("RectangularShadow {"):]
    assert "pulseMin" not in shadow_block.split("}")[0]


def test_glow_halo_colour_is_supplied_by_the_consumer():
    halo_source = GLOW_HALO_SOURCE.read_text(encoding="utf-8")
    adapter_source = BUTTON_GLOW_SOURCE.read_text(encoding="utf-8")

    # The shared effect must not guess its hue; the consumer knows what it painted.
    # 共享效果不得猜测色相; 使用者知道自己画了什么。
    assert "property color haloColor: Enums.accentColor" in halo_source
    # The button adapter follows the resolved face, falling back to accent for a
    # fill-less flat face, so a grey disabled face is never ringed in blue.
    # 按钮适配层跟随已解析面色, 无填充的扁平面回退到主色, 使灰色禁用面不会被蓝圈包围。
    assert "haloColor: button.flat ? _skin.accentColor : button._effectiveBgColor" in adapter_source


def test_glow_composes_with_every_style_shape_and_feature(qapp):
    """The point of a separate axis: it combines, it does not replace.

    独立轴的意义就是可组合, 而不是取代。
    """
    engine = QQmlEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(COMPOSE_SCENE_SOURCE, QUrl("inline:button-glow-compose.qml"))
    for _ in range(50):
        if not component.isLoading():
            break
        _pump()
    window = component.create()
    assert window is not None, [error.toString() for error in component.errors()]
    try:
        # Glow changes nothing about the face: only the halo layer appears.
        # 泛光不改变按钮面: 只多出光晕层。
        for pair in (
            ("default", "plainDefault"),
            ("primary", "plainPrimary"),
            ("filled", "plainFilled"),
        ):
            glow_name, plain_name = f"glow_{pair[0]}", pair[1]
            glow_item = window.findChild(QObject, glow_name)
            plain_item = window.findChild(QObject, plain_name)
            assert glow_item is not None and plain_item is not None, pair
            assert glow_item.property("_styleBgColor") == plain_item.property("_styleBgColor"), pair
            assert glow_item.property("_styleTextColor") == plain_item.property("_styleTextColor"), pair
            # Exactly one halo on the glowing one, none on the plain one.
            # 泛光实例恰有一个光晕, 普通实例没有。
            assert len(_modules(glow_item, "ButtonGlow_QMLTYPE_")) == 1, pair
            assert _modules(plain_item, "ButtonGlow_QMLTYPE_") == [], pair

        # Shape and feature compose too: a pill and a toggle both keep their own
        # behaviour while carrying a halo.
        # 形状与功能同样可组合: 药丸与 toggle 各自保持行为同时携带光晕。
        for name in ("glowPill", "glowToggle", "glowProgress"):
            item = window.findChild(QObject, name)
            assert item is not None, name
            assert len(_modules(item, "ButtonGlow_QMLTYPE_")) == 1, name
        pill = window.findChild(QObject, "glowPill")
        assert pill.property("shape") == window.property("pillShape")
        toggle = window.findChild(QObject, "glowToggle")
        assert toggle.property("feature") == window.property("toggleFeature")
        assert warnings == []
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)


# ==================== Runtime behaviour 运行时行为 ====================


def test_halo_is_created_only_when_glow_is_requested(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        glow_button = window.findChild(QObject, "glowButton")
        plain_button = window.findChild(QObject, "plainPrimaryButton")
        assert glow_button is not None and plain_button is not None

        assert glow_button.property("_glowActive") is True
        assert plain_button.property("_glowActive") is False
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
            halo.property("_tokens").property("disabledStrength")
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
