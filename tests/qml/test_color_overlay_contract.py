# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ColorOverlay recolor contract regressions. ColorOverlay 着色契约回归。

ColorOverlay is the recolor path for every ``Icon``; ``IconRendererResources``
attaches it as ``layer.effect`` over the SVG source. A regression here silently
breaks icon tinting across the whole library, so the contract is pinned here.
ColorOverlay 是所有 ``Icon`` 的着色路径, ``IconRendererResources`` 将其作为
``layer.effect`` 挂在 SVG 源之上。此处回归会静默破坏全库图标着色, 故锁定契约。

Deliberately no pixel assertions. The ``offscreen`` QPA platform used by the
automated runner falls back to the Software scene graph backend (measured:
requested Direct3D11, actual ``GraphicsApi.Software``), and that backend does
not execute shader effects at all -- both a bare Qt ``MultiEffect`` and this
wrapper rasterize to zero pixels there while non-shader content renders fine.
Asserting tinted pixels would therefore fail in CI for reasons unrelated to
this component. Verify appearance on a real window instead.
刻意不做像素断言。自动化 runner 使用的 ``offscreen`` QPA 平台会回退到
Software 场景图后端(实测: 请求 Direct3D11, 实际 ``GraphicsApi.Software``),
该后端根本不执行着色器效果 —— 裸 Qt ``MultiEffect`` 与本封装在其下均栅格化
为 0 像素, 而非着色器内容正常渲染。断言着色像素会因与本组件无关的原因在 CI
失败。观感请在真实窗口上验证。
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
COLOR_OVERLAY_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "effects" / "ColorOverlay.qml"
)
ICON_RENDERER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "icons"
    / "IconRendererResources.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-overlay-contract.qml")
)
SCENE_SOURCE = """
import QtQuick
import PrismQML

Item {
    readonly property real overlayBrightness: overlay.brightness
    readonly property real overlayColorization: overlay.colorization
    readonly property color overlayColorizationColor: overlay.colorizationColor
    readonly property color overlayColor: overlay.color
    readonly property color themePrimary: Enums.textColor.primary

    // MultiEffect-only channels: presence proves the base type, and the
    // defaults prove the wrapper leaves unrelated channels untouched.
    // MultiEffect 独有通道: 存在性证明基类, 默认值证明封装未动其他通道。
    readonly property bool overlayBlurEnabled: overlay.blurEnabled
    readonly property real overlaySaturation: overlay.saturation
    readonly property bool overlayShadowEnabled: overlay.shadowEnabled

    // QQuickItemLayer has no Python converter, so surface it through QML.
    // QQuickItemLayer 无 Python 转换器, 故经 QML 暴露。
    readonly property bool layerHostLayerEnabled: layerHost.layer.enabled

    ColorOverlay {
        id: overlay
        objectName: "colorOverlay"
    }

    // The real consumption path: attached as layer.effect over a dark source,
    // exactly how IconRendererResources tints an SVG.
    // 真实消费路径: 作为 layer.effect 挂在深色源之上, 与图标着色方式一致。
    Rectangle {
        id: layerHost
        objectName: "layerHost"
        width: 20
        height: 20
        color: "#212121"
        layer.enabled: true
        layer.effect: ColorOverlay {
            objectName: "layerOverlay"
            color: "white"
        }
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root


def test_color_overlay_recolor_channels_stay_fully_saturated(qapp):
    """Full brightness + colorization is what lets a #212121 SVG reach any tint.

    满亮度加满着色才能把 #212121 的 SVG 推到任意目标色。
    """
    engine, component, root = _create_scene()
    try:
        assert root.property("overlayBrightness") == pytest.approx(1.0)
        assert root.property("overlayColorization") == pytest.approx(1.0)

        # Unrelated MultiEffect channels must stay at their defaults.
        # 无关的 MultiEffect 通道必须保持默认值。
        assert root.property("overlayBlurEnabled") is False
        assert root.property("overlayShadowEnabled") is False
        assert root.property("overlaySaturation") == pytest.approx(0.0)
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_color_overlay_color_drives_colorization_color(qapp):
    """``color`` must stay bound to ``colorizationColor``, not copied once.

    ``color`` 必须保持绑定到 ``colorizationColor``, 而非一次性拷贝。
    """
    engine, component, root = _create_scene()
    try:
        # Default follows the theme, not a hardcoded literal.
        # 默认跟随主题, 而非硬编码字面量。
        assert root.property("overlayColor") == root.property("themePrimary")
        assert root.property("overlayColorizationColor") == root.property(
            "themePrimary"
        )

        overlay = root.findChild(QQuickItem, "colorOverlay")
        assert overlay is not None
        assert overlay.setProperty("color", QColor("#FF00FF"))
        _pump()

        assert root.property("overlayColorizationColor") == QColor("#FF00FF")

        # A second change proves the binding survived the first write.
        # 二次修改证明绑定在首次写入后依然存活。
        assert overlay.setProperty("color", QColor("#00FF7F"))
        _pump()
        assert root.property("overlayColorizationColor") == QColor("#00FF7F")
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_color_overlay_layer_host_declares_effect_without_error(qapp):
    """The ``layer.effect`` scene must load clean; the effect object itself is
    not assertable offscreen.

    ``layer.effect`` 场景必须干净加载; 效果对象本身在离屏下不可断言。

    A layer effect is instantiated lazily by the layer's renderer. Under the
    Software backend the shader path never runs, so the effect object is never
    created and ``findChild`` returns None -- same root cause as the missing
    pixels. What is verifiable here is that declaring it raises no QML error.
    The wiring itself is pinned at source level in the consumer test below.
    层效果由层渲染器惰性实例化。Software 后端下着色器路径从不执行, 故效果对象
    从未创建, ``findChild`` 返回 None —— 与像素缺失同源。此处可验证的是声明它
    不产生 QML 错误。接线本身由下方消费方测试在源码级锁定。
    """
    engine, component, root = _create_scene()
    try:
        host = root.findChild(QQuickItem, "layerHost")
        assert host is not None
        assert root.property("layerHostLayerEnabled") is True
        assert not component.errors(), [
            error.toString() for error in component.errors()
        ]
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_color_overlay_source_keeps_multieffect_contract():
    """Source-level guards: MultiEffect root, no hardcoded colors.

    源码级门禁: MultiEffect 根, 无硬编码颜色。
    """
    source = COLOR_OVERLAY_SOURCE.read_text(encoding="utf-8")

    assert "MultiEffect {" in source
    assert "import QtQuick.Effects" in source
    assert "property color color: Enums.textColor.primary" in source
    assert "brightness: 1.0" in source
    assert "colorization: 1.0" in source
    assert "colorizationColor: root.color" in source

    # AGENTS.md 3.6: no hardcoded color literals in component code. Comments
    # may legitimately cite #212121 when explaining the recolor technique, so
    # strip comments before checking.
    # AGENTS.md 3.6: 组件代码禁止硬编码颜色字面量。注释在解释着色原理时可以合法
    # 引用 #212121, 故检查前先剥离注释。
    code_only = "\n".join(
        line.split("//", 1)[0] for line in source.splitlines()
    )
    assert "#" not in code_only


def test_icon_renderer_still_routes_svg_through_color_overlay():
    """Pins the consumer wiring so the recolor path cannot silently detach.

    锁定消费方接线, 使着色路径不会静默脱开。
    """
    source = ICON_RENDERER_SOURCE.read_text(encoding="utf-8")

    assert "layer.effect: ColorOverlay {" in source
    assert "color: imageIcon.parent.iconControl.color" in source
    # Recolor must be gated on a ready image, otherwise it tints nothing.
    # 着色必须以图片就绪为前提, 否则无内容可着色。
    assert "layer.enabled: imageIcon.status === Image.Ready" in source
