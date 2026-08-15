# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowIcon SVG provider path transport regressions. SVG 路径传输回归。"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QSize,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickImageProvider

from prismqml.python.core._icon_path import resolve_provider_path
from prismqml import register_types
from prismqml.python.providers.svg_provider import SvgImageProvider


ROOT = Path(__file__).resolve().parents[2]
WINDOW_ICON = ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowIcon.qml"
SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">
<rect width="8" height="8" fill="#d02040"/>
</svg>
"""


class _CapturingProvider(QQuickImageProvider):
    """Capture the real QML provider id with a stable image. 捕获真实 provider id。"""

    def __init__(self, records: list[str]):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._records = records

    def requestImage(self, provider_id, size, requested_size):
        """Record one asynchronous provider request. 记录异步请求。"""
        self._records.append(provider_id)
        image = QImage(2, 2, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        return image


def _wait_component(component: QQmlComponent) -> None:
    """Wait for direct-file QML compilation. 等待 QML 编译。"""
    if component.status() != QQmlComponent.Status.Loading:
        return
    loop = QEventLoop()
    component.statusChanged.connect(lambda _status: loop.quit())
    QTimer.singleShot(3000, loop.quit)
    loop.exec()


def _source_for(path: Path, source_kind: str) -> str:
    """Build raw path or fully encoded file URL input. 构造两类真实输入。"""
    if source_kind == "raw_path":
        return str(path)
    return QUrl.fromLocalFile(str(path)).toString(QUrl.FullyEncoded)


def _dispose_scene(qapp, engine, component, root, provider) -> None:
    """Dispose QML objects in dependency order. 按依赖顺序销毁 QML 对象。"""
    root.setProperty("source", "")
    qapp.processEvents()
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    assert not shiboken6.isValid(provider)


def _window_icon_request(qapp, source: str) -> tuple[str, str]:
    """Run WindowIcon with synchronous child Images. 执行真实 WindowIcon 传输。"""
    records: list[str] = []
    engine = QQmlApplicationEngine()
    register_types(engine)
    capture_provider = _CapturingProvider(records)
    engine.addImageProvider("svg", capture_provider)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(WINDOW_ICON)))
    _wait_component(component)
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    root = component.create()
    assert root is not None
    try:
        for child in root.findChildren(QObject):
            if child.metaObject().indexOfProperty("asynchronous") >= 0:
                child.setProperty("asynchronous", False)
        root.setProperty("colored", True)
        root.setProperty("source", source)
        qapp.processEvents()
        assert records
        return root.property("_svgSource"), records[-1]
    finally:
        _dispose_scene(qapp, engine, component, root, capture_provider)


@pytest.mark.parametrize("source_kind", ["raw_path", "file_url"])
def test_window_icon_renders_reserved_character_svg(
    qapp,
    tmp_path: Path,
    source_kind: str,
) -> None:
    """WindowIcon must render a real path after one URL decode. 只解码一次。"""
    svg_path = tmp_path / "图 标#百分%23.svg"
    svg_path.write_text(SVG_CONTENT, encoding="utf-8")
    source = _source_for(svg_path, source_kind)
    svg_source, provider_id = _window_icon_request(qapp, source)
    assert "%23" in provider_id and "%2523" in provider_id
    if source_kind == "file_url":
        assert svg_source.startswith("image://svg/file:///")
    else:
        expected = quote(source.replace("\\", "/"), safe="")
        assert svg_source == "image://svg/" + expected
    rendered = SvgImageProvider().requestImage(
        provider_id, QSize(), QSize(16, 16)
    )
    assert not rendered.isNull()


def test_window_icon_provider_id_encodes_literal_pipe(qapp, tmp_path: Path) -> None:
    """QML must preserve a literal pipe as one encoded provider layer. 保留竖线。"""
    icon_path = tmp_path / "A|B.svg"
    source = str(icon_path).replace("\\", "/")
    svg_source, provider_id = _window_icon_request(qapp, source)
    encoded_source = quote(source, safe="")
    assert svg_source == "image://svg/" + encoded_source
    assert provider_id == encoded_source
    assert resolve_provider_path(provider_id).replace("\\", "/") == source
