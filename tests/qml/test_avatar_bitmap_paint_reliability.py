# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Avatar bitmap paint reliability regressions. 头像位图绘制可靠性回归。

The retired Canvas avatar repainted only from ``onStatusChanged(Ready)`` and
from size changes. When the host was still hidden and unsized while the bitmap
became ready, and the host was then revealed with a real size in the same
event-loop turn, that paint request was dropped and the avatar stayed blank
forever -- measured on the old implementation as a centre pixel equal to the
window background. These regressions grab real pixels, so they fail on that
behaviour and pass on the plain ``Image`` + layer-mask implementation.
已退役的 Canvas 头像只在 ``onStatusChanged(Ready)`` 与尺寸变化时重绘。宿主仍
不可见且没有尺寸时位图就绪, 随后宿主在同一事件循环轮次里被揭幕并拿到真实尺寸,
该次重绘请求会被丢弃, 头像永久空白 —— 旧实现实测中心像素等于窗口背景色。以下
回归抓取真实像素, 在该行为下失败, 在普通 ``Image`` + 层遮罩实现下通过。
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QBuffer,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QIODevice,
    QObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QColor, QGuiApplication, QImage
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
    QQmlProperty,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
AVATAR_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Avatar"
    / "Avatar.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "avatar-bitmap-paint-reliability.qml")
)
# Solid bitmap colour; any resampling of a solid source keeps this exact value.
# 纯色位图颜色; 纯色源无论怎样重采样都保持该精确值。
BITMAP_RGB = (255, 0, 255)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    property string uri: ""
    property bool revealed: false
    property int directSize: 0
    property int hostSize: 0
    property bool hostVisible: false

    readonly property color accent: Enums.accentColor

    width: 300
    height: 120
    visible: true
    color: "#ffffff"

    // Bitmap avatar that is visible and sized from the start 起始即可见且有尺寸
    Avatar {
        objectName: "readyAvatar"
        x: 10
        y: 10
        size: 80
        text: "K"
        source: window.uri
    }

    // Bitmap avatar revealed later with a real size 稍后带真实尺寸揭幕
    Avatar {
        objectName: "revealAvatar"
        x: 110
        y: 10
        size: window.directSize
        text: "K"
        visible: window.revealed
        source: window.uri
    }

    // Bitmap avatar inside a lazily revealed host 懒加载宿主内的位图头像
    Item {
        id: host
        objectName: "host"
        x: 210
        y: 10
        width: window.hostSize
        height: window.hostSize
        visible: window.hostVisible

        Avatar {
            objectName: "hostedAvatar"
            anchors.fill: parent
            text: "K"
            source: window.uri
        }
    }
}
"""
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


def _bitmap_uri() -> str:
    """Return a solid magenta PNG data URI. 返回纯洋红 PNG data URI。"""
    image = QImage(64, 64, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(*BITMAP_RGB))
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(bytes(buffer.data())).decode()


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 3_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("Avatar frame did not stabilize within 800 ms")


def _grab_item(item: QQuickItem) -> QImage:
    """Grab one item, waiting for the asynchronous result. 抓取单个 item。"""
    result = item.grabToImage()
    ready = QSignalSpy(result.ready)
    image = result.image()
    if image.isNull():
        assert ready.wait(1_000), "grabToImage never completed"
        image = result.image()
    assert not image.isNull()
    return image


def _image_child(avatar: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in avatar.childItems()
        if item.metaObject().indexOfProperty("fillMode") >= 0
        and item.metaObject().indexOfProperty("source") >= 0
    ]
    assert len(matches) == 1, [
        item.metaObject().className() for item in avatar.childItems()
    ]
    return matches[0]


def _image_ready(image: QQuickItem) -> bool:
    expression = QQmlExpression(
        QQmlEngine.contextForObject(image), image, "status === Image.Ready"
    )
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return bool(result)


def _layer_enabled(image: QQuickItem) -> bool:
    prop = QQmlProperty(image, "layer.enabled")
    assert prop.isValid()
    return bool(prop.read())


def _text_fallback(avatar: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in avatar.findChildren(QObject)
        if item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == "K"
    ]
    assert len(matches) == 1, [
        item.metaObject().className() for item in matches
    ]
    return matches[0]


def _centre_rgb(image: QImage) -> tuple:
    colour = image.pixelColor(image.width() // 2, image.height() // 2)
    return (colour.red(), colour.green(), colour.blue())


def _window_centre_rgb(frame: QImage, item: QQuickItem) -> tuple:
    ratio = frame.width() / 300.0
    x = int(round((item.x() + item.width() / 2) * ratio))
    y = int(round((item.y() + item.height() / 2) * ratio))
    colour = frame.pixelColor(x, y)
    return (colour.red(), colour.green(), colour.blue())


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _qt_failures(messages) -> list[str]:
    return [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]


def _create_scene():
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    assert _wait_for(window.isExposed)
    _pump(60)
    return (
        engine,
        component,
        window,
        window.findChild(QQuickItem, "readyAvatar"),
        window.findChild(QQuickItem, "revealAvatar"),
        window.findChild(QQuickItem, "hostedAvatar"),
        warnings,
        messages,
        previous_handler,
    )


def _dispose_scene(qapp, engine, component, window, previous_handler) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    qInstallMessageHandler(previous_handler)


def _graphics_api(window: QQuickWindow) -> str:
    return window.rendererInterface().graphicsApi().name


def test_avatar_bitmap_renders_image_content_not_the_fallback(qapp):
    """A ready bitmap must reach the centre pixel, not the accent fallback.

    就绪位图必须落在中心像素上, 而不是强调色兜底。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        ready_avatar,
        _reveal_avatar,
        _hosted_avatar,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        assert ready_avatar is not None
        image = _image_child(ready_avatar)
        assert ready_avatar.property("source") == ""
        assert _layer_enabled(image) is False

        window.setProperty("uri", _bitmap_uri())
        assert _wait_for(lambda: _image_ready(image))
        assert window.property("accent") != QColor(*BITMAP_RGB)

        frame = _stable_window_image(window)
        assert _window_centre_rgb(frame, ready_avatar) == BITMAP_RGB
        assert _window_centre_rgb(frame, ready_avatar) != (
            window.property("accent").red(),
            window.property("accent").green(),
            window.property("accent").blue(),
        )

        # The item-level grab (the pixel source the reporter asked for) must
        # agree with the window grab. item 级抓图必须与窗口抓图一致。
        grabbed = _grab_item(ready_avatar)
        assert _centre_rgb(grabbed) == BITMAP_RGB

        # The text fallback branch must stay off while a bitmap is present.
        # 存在位图时文字兜底分支必须保持关闭。
        assert _text_fallback(ready_avatar).property("visible") is False

        # Shader backends mask the bitmap; the Software backend keeps it plain.
        # 着色器后端为位图挂遮罩; 软件后端保留普通绘制。
        if _graphics_api(window) == "Software":
            assert _layer_enabled(image) is False
        else:
            assert _layer_enabled(image) is True

        assert warnings == []
        assert _qt_failures(messages) == []
        assert _new_visible_windows(windows_before, window) == []
        print(
            "AVATAR_BITMAP_PAINT",
            f"api={_graphics_api(window)}",
            f"centre={_window_centre_rgb(frame, ready_avatar)}",
            f"item_centre={_centre_rgb(grabbed)}",
            f"layer={_layer_enabled(image)}",
        )
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)
        assert _new_visible_windows(windows_before) == []


def test_avatar_paints_after_hidden_zero_size_reveal(qapp):
    """Hidden + unsized while loading, then revealed with a size, must paint.

    加载期间不可见且没有尺寸, 随后带尺寸揭幕时必须绘制。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        _ready_avatar,
        reveal_avatar,
        hosted_avatar,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        assert reveal_avatar is not None and hosted_avatar is not None
        direct_image = _image_child(reveal_avatar)
        hosted_image = _image_child(hosted_avatar)

        window.setProperty("uri", _bitmap_uri())
        assert _wait_for(lambda: _image_ready(direct_image))
        assert _wait_for(lambda: _image_ready(hosted_image))
        assert reveal_avatar.width() == 0 and hosted_avatar.width() == 0
        assert reveal_avatar.isVisible() is False
        assert hosted_avatar.isVisible() is False

        # Same event-loop turn: size and visibility arrive together, exactly
        # like a lazily loaded page being revealed by one layout pass.
        # 同一事件循环轮次: 尺寸与可见性一起到达, 与懒加载页面一次布局揭幕一致。
        window.setProperty("directSize", 80)
        window.setProperty("revealed", True)
        window.setProperty("hostSize", 80)
        window.setProperty("hostVisible", True)

        frame = _stable_window_image(window)
        assert _window_centre_rgb(frame, reveal_avatar) == BITMAP_RGB, (
            "avatar stayed blank after being revealed with a size",
            _window_centre_rgb(frame, reveal_avatar),
        )
        assert _window_centre_rgb(frame, hosted_avatar) == BITMAP_RGB, (
            "hosted avatar stayed blank after its host was revealed",
            _window_centre_rgb(frame, hosted_avatar),
        )
        assert _centre_rgb(_grab_item(reveal_avatar)) == BITMAP_RGB
        assert _centre_rgb(_grab_item(hosted_avatar)) == BITMAP_RGB
        assert warnings == []
        assert _qt_failures(messages) == []
        assert _new_visible_windows(windows_before, window) == []
        print(
            "AVATAR_REVEAL_PAINT",
            f"api={_graphics_api(window)}",
            f"direct={_window_centre_rgb(frame, reveal_avatar)}",
            f"hosted={_window_centre_rgb(frame, hosted_avatar)}",
        )
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)
        assert _new_visible_windows(windows_before) == []


def test_avatar_paints_when_reveal_is_split_across_turns(qapp):
    """Visibility first, size in a later turn, must also paint.

    先可见、后一回合才有尺寸, 同样必须绘制。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        _ready_avatar,
        reveal_avatar,
        hosted_avatar,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        window.setProperty("uri", _bitmap_uri())
        assert _wait_for(lambda: _image_ready(_image_child(reveal_avatar)))
        assert _wait_for(lambda: _image_ready(_image_child(hosted_avatar)))

        window.setProperty("revealed", True)
        window.setProperty("hostVisible", True)
        _pump(60)
        window.setProperty("directSize", 80)
        window.setProperty("hostSize", 80)

        frame = _stable_window_image(window)
        assert _window_centre_rgb(frame, reveal_avatar) == BITMAP_RGB
        assert _window_centre_rgb(frame, hosted_avatar) == BITMAP_RGB
        assert warnings == []
        assert _qt_failures(messages) == []
        assert _new_visible_windows(windows_before, window) == []
        print(
            "AVATAR_SPLIT_REVEAL_PAINT",
            f"api={_graphics_api(window)}",
            f"direct={_window_centre_rgb(frame, reveal_avatar)}",
            f"hosted={_window_centre_rgb(frame, hosted_avatar)}",
        )
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)
        assert _new_visible_windows(windows_before) == []


def test_avatar_source_uses_plain_image_with_circle_layer_mask():
    """The retired repaint-triggered Canvas path must not come back.

    已退役的“靠信号触发重绘”的 Canvas 路径不得回流。
    """
    source = AVATAR_SOURCE.read_text(encoding="utf-8")
    code = "\n".join(line.split("//", 1)[0] for line in source.splitlines())
    compact = " ".join(code.split())

    # No Canvas, no manual paint triggers, no framebuffer render target.
    assert "Canvas {" not in code
    assert "requestPaint" not in code
    assert "renderTarget" not in code
    assert "renderStrategy" not in code
    assert "ctx.arc(" not in code

    # Plain Image with the circular layer mask at device resolution.
    assert "Image {" in code
    assert "fillMode: Image.PreserveAspectCrop" in compact
    assert (
        "layer.enabled: control._avatarMaskSupported && status === Image.Ready"
        in compact
    )
    assert "layer.effect: MultiEffect {" in compact
    assert "maskEnabled: true" in compact
    assert "maskThresholdMin: Enums.mask.thresholdMin" in compact
    assert "maskSpreadAtMin: Enums.mask.spreadFull" in compact
    assert "maskSource: ShaderEffectSource {" in compact
    assert "radius: avatarImage.width / 2" in compact
    assert "antialiasing: true" in compact

    # Public API and the fallback branches stay untouched.
    assert 'property string source: ""' in code
    assert 'property string text: ""' in code
    assert "property int size: 40" in code
    assert "function setRadius(r) {" in code
    assert "size = r * 2" in code
    assert "Enums.icon.person" in code
    assert "Enums.accentForeground" in code
    assert "Enums.accentColor" in code
    assert "Enums.hasOutlinedSurfaces" in code
    assert "visible: source === \"\" && text !== \"\"" in compact
    assert "visible: control.source === \"\" && control.text === \"\"" in compact
