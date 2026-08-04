# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Icon file URL resolution regressions. 图标文件 URL 解析回归。"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QResource, QSize, QUrl
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap, Qt
from PySide6.QtSvg import QSvgRenderer

from prismqml.python.core._taskbar_svg_icon import _TaskbarSvgIconEngine
from prismqml.python.core.window_helper import WindowHelper, _ICON_SIZES
from prismqml.python.window.system_tray import SystemTrayIcon
from prismqml.python.window.window_core import WindowCore


_GALLERY_RCC = Path(__file__).parents[1] / "examples" / "resources" / "gallery.rcc"


def _normalized(path: str) -> str:
    """Normalize separators without changing URL-decoded characters. 归一化分隔符。"""
    return path.replace("\\", "/")


def _encoded_file_url(path: Path) -> str:
    """Build the same fully encoded URL that QML receives. 构造 QML 实际 URL。"""
    return bytes(QUrl.fromLocalFile(str(path)).toEncoded()).decode("ascii")


def _write_real_icon(path: Path) -> None:
    """Write a real bitmap used by every public icon path. 写入真实图标。"""
    image = QImage(8, 8, QImage.Format.Format_ARGB32)
    image.fill(QColor("#d02040"))
    assert image.save(str(path))


def _write_real_svg(path: Path, color: str = "#d02040") -> None:
    """Write a real scalable icon. 写入真实可缩放图标。"""
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" '
        f'viewBox="0 0 32 32"><rect width="32" height="32" fill="{color}"/></svg>',
        encoding="utf-8",
    )


def _render_eager_svg_icon(path: Path) -> QIcon:
    """Build the former eager taskbar icon as a pixel oracle. 构造原预渲染图标作为像素基准。"""
    renderer = QSvgRenderer(str(path))
    assert renderer.isValid()
    icon = QIcon()
    for size in _ICON_SIZES:
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        assert painter.isActive()
        try:
            renderer.render(painter)
        finally:
            painter.end()
        icon.addPixmap(pixmap)
    return icon


def _load_icon(entrypoint: str, qapp, source: str) -> QIcon:
    """Load through one public Python entrypoint. 经一个公开入口加载。"""
    if entrypoint == "WindowHelper":
        WindowHelper().setAppIcon(source)
        return qapp.windowIcon()
    if entrypoint == "WindowCore":
        WindowCore._setAppIcon(None, source)
        return qapp.windowIcon()
    tray = SystemTrayIcon()
    try:
        tray.setIcon(source)
        return tray.icon()
    finally:
        tray.deleteLater()
        qapp.processEvents()


@pytest.mark.parametrize(
    "source",
    [
        "file:///C:/Icons/A%20B/%23mark%25.png",
        "file://server/share/A%20B/%23mark.png",
        "file:///home/user/A%20B/%23mark%25%3F.svg",
    ],
)
def test_window_helper_decodes_file_urls(source: str) -> None:
    """file URLs must follow QUrl.toLocalFile on every platform. 遵循 Qt 合同。"""
    assert WindowHelper._resolveIconPath(source) == QUrl(source).toLocalFile()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("qrc:/icons/A%20B.svg", ":/icons/A B.svg"),
        ("qrc:///icons/A%20B.svg", ":/icons/A B.svg"),
        (":/icons/A B.svg", ":/icons/A B.svg"),
    ],
)
def test_window_helper_normalizes_resource_urls(source: str, expected: str) -> None:
    """qrc variants must resolve to one QFile resource path. qrc 归一为资源路径。"""
    assert WindowHelper._resolveIconPath(source) == expected


@pytest.mark.parametrize(
    "entrypoint",
    ["WindowHelper", "WindowCore", "SystemTrayIcon"],
)
def test_encoded_real_icon_loads_through_python_entrypoint(
    entrypoint: str,
    qapp,
    tmp_path: Path,
) -> None:
    """Each Python entrypoint loads one real encoded path. 各入口加载真实路径。"""
    icon_path = tmp_path / "图 标#百分%.png"
    _write_real_icon(icon_path)
    source = _encoded_file_url(icon_path)
    assert QUrl(source).toLocalFile() == _normalized(str(icon_path))
    assert not QIcon(str(icon_path)).isNull()
    assert QIcon(source).isNull()

    original_icon = qapp.windowIcon()
    before_widgets = set(qapp.topLevelWidgets())
    try:
        qapp.setWindowIcon(QIcon())
        assert not _load_icon(entrypoint, qapp, source).isNull()
        assert set(qapp.topLevelWidgets()) == before_widgets
    finally:
        qapp.setWindowIcon(original_icon)


def test_window_helper_renders_every_svg_size(tmp_path: Path) -> None:
    """Render every taskbar size from one real SVG. 从真实 SVG 渲染全部任务栏尺寸。"""
    icon_path = tmp_path / "app.svg"
    _write_real_svg(icon_path)

    rendered = WindowHelper._renderSvgIcon(str(icon_path))
    assert rendered is not None
    assert not rendered.isNull()
    assert rendered.availableSizes() == [QSize(size, size) for size in _ICON_SIZES]


@pytest.mark.parametrize(
    "requested_size",
    [
        QSize(16, 16),
        QSize(20, 20),
        QSize(24, 24),
        QSize(36, 36),
        QSize(48, 48),
        QSize(64, 64),
        QSize(96, 96),
        QSize(128, 128),
        QSize(192, 192),
        QSize(256, 256),
        QSize(300, 300),
        QSize(64, 24),
    ],
)
def test_window_helper_lazy_svg_keeps_eager_pixels(
    tmp_path: Path,
    requested_size: QSize,
) -> None:
    """Lazy rendering must preserve the former eager icon pixels. 惰性渲染保持原像素。"""
    icon_path = tmp_path / "pixel-oracle.svg"
    _write_real_svg(icon_path)
    expected = _render_eager_svg_icon(icon_path)
    actual = WindowHelper._renderSvgIcon(str(icon_path))

    assert actual is not None
    assert actual.actualSize(requested_size) == expected.actualSize(requested_size)
    assert actual.pixmap(requested_size).toImage() == expected.pixmap(
        requested_size
    ).toImage()


def test_taskbar_svg_engine_defers_and_reuses_source_renders(tmp_path: Path) -> None:
    """Creation must render nothing and repeated requests reuse one source. 创建零渲染且复用源图。"""
    icon_path = tmp_path / "lazy-cache.svg"
    _write_real_svg(icon_path)
    engine = _TaskbarSvgIconEngine(str(icon_path), _ICON_SIZES)
    icon = QIcon(engine)

    assert engine._source_icons == {}
    first_image = icon.pixmap(QSize(20, 20)).toImage()
    assert set(engine._source_icons) == {24}
    assert icon.pixmap(QSize(20, 20)).toImage() == first_image
    assert set(engine._source_icons) == {24}

    icon.pixmap(QSize(36, 36))
    assert set(engine._source_icons) == {24, 48}


@pytest.mark.parametrize("entrypoint", ["WindowHelper", "WindowCore"])
def test_window_entrypoints_publish_real_svg(
    entrypoint: str,
    qapp,
    tmp_path: Path,
) -> None:
    """Both window APIs must publish the same SVG pixels. 两个窗口入口发布相同像素。"""
    icon_path = tmp_path / f"{entrypoint}.svg"
    _write_real_svg(icon_path)
    original_icon = qapp.windowIcon()
    try:
        qapp.setWindowIcon(QIcon())
        published = _load_icon(entrypoint, qapp, str(icon_path))
        assert not published.isNull()
        assert published.pixmap(QSize(64, 64)).toImage().pixelColor(32, 32) == QColor(
            "#d02040"
        )
    finally:
        qapp.setWindowIcon(original_icon)


def test_window_helper_reuses_unchanged_svg_render(
    qapp,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The native-ready reapply must reuse identical SVG pixels. 原生就绪重设复用相同SVG。"""
    icon_path = tmp_path / "cached.svg"
    _write_real_svg(icon_path)
    helper = WindowHelper()
    render_spy = Mock(wraps=helper._renderSvgIcon)
    monkeypatch.setattr(helper, "_renderSvgIcon", render_spy)
    original_icon = qapp.windowIcon()
    try:
        helper.setAppIcon(str(icon_path))
        first_icon = qapp.windowIcon()
        helper.setAppIcon(str(icon_path))
        second_icon = qapp.windowIcon()

        render_spy.assert_called_once_with(str(icon_path))
        assert not first_icon.isNull()
        assert second_icon.cacheKey() == first_icon.cacheKey()
        assert second_icon.pixmap(QSize(64, 64)).toImage() == first_icon.pixmap(
            QSize(64, 64)
        ).toImage()
    finally:
        qapp.setWindowIcon(original_icon)


def test_window_helper_reuses_unchanged_qrc_svg_render(qapp, monkeypatch) -> None:
    """Packaged QRC icons must retain exact pixels while reusing renders. QRC复用渲染。"""
    assert QResource.registerResource(str(_GALLERY_RCC))
    helper = WindowHelper()
    helper._cached_svg_icon_path = ""
    helper._cached_svg_icon_signature = None
    helper._cached_svg_icon = None
    render_spy = Mock(wraps=helper._renderSvgIcon)
    monkeypatch.setattr(helper, "_renderSvgIcon", render_spy)
    original_icon = qapp.windowIcon()
    try:
        helper.setAppIcon("qrc:/app_icon.svg")
        first_image = qapp.windowIcon().pixmap(QSize(64, 64)).toImage()
        helper.setAppIcon("qrc:/app_icon.svg")

        render_spy.assert_called_once_with(":/app_icon.svg")
        assert qapp.windowIcon().pixmap(QSize(64, 64)).toImage() == first_image
    finally:
        qapp.setWindowIcon(original_icon)
        assert QResource.unregisterResource(str(_GALLERY_RCC))


def test_window_helper_refreshes_changed_svg(
    qapp,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A changed file must invalidate cached SVG pixels. 文件变化必须使SVG缓存失效。"""
    icon_path = tmp_path / "changing.svg"
    _write_real_svg(icon_path)
    helper = WindowHelper()
    render_spy = Mock(wraps=helper._renderSvgIcon)
    monkeypatch.setattr(helper, "_renderSvgIcon", render_spy)
    original_icon = qapp.windowIcon()
    try:
        helper.setAppIcon(str(icon_path))
        before_stat = icon_path.stat()
        _write_real_svg(icon_path, "#20c050")
        os.utime(
            icon_path,
            ns=(before_stat.st_atime_ns, before_stat.st_mtime_ns + 1_000_000_000),
        )
        helper.setAppIcon(str(icon_path))

        assert render_spy.call_count == 2
        image = qapp.windowIcon().pixmap(QSize(64, 64)).toImage()
        assert image.pixelColor(32, 32) == QColor("#20c050")
    finally:
        qapp.setWindowIcon(original_icon)


def test_window_helper_keeps_icon_for_empty_and_missing_sources(
    qapp,
    tmp_path: Path,
) -> None:
    """Invalid inputs must not replace the current icon. 无效输入不得覆盖当前图标。"""
    icon_path = tmp_path / "current.png"
    _write_real_icon(icon_path)
    original_icon = qapp.windowIcon()
    try:
        current = QIcon(str(icon_path))
        qapp.setWindowIcon(current)
        WindowHelper().setAppIcon("")
        assert qapp.windowIcon().cacheKey() == current.cacheKey()
        WindowHelper().setAppIcon(str(tmp_path / "missing.png"))
        assert qapp.windowIcon().cacheKey() == current.cacheKey()
    finally:
        qapp.setWindowIcon(original_icon)
