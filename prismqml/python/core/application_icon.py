# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Application icon build helpers. 应用图标构建辅助。"""

from __future__ import annotations

from pathlib import Path
import struct
import sys
from typing import List, Union

from PySide6.QtCore import QBuffer, QIODevice, QSize, Qt
from PySide6.QtGui import QImage, QPainter


PathSource = Union[str, Path]
_WINDOWS_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _load_application_icon(source: PathSource) -> tuple[Path, QImage]:
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"application icon not found: {source_path}")
    image = QImage(str(source_path))
    if image.isNull():
        raise ValueError(f"application icon is not a readable image: {source_path}")
    return source_path, image


def _render_square_png(source: QImage, size: int) -> bytes:
    scaled = source.scaled(
        QSize(size, size),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QImage(size, size, QImage.Format.Format_ARGB32)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.drawImage((size - scaled.width()) // 2, (size - scaled.height()) // 2, scaled)
    painter.end()

    buffer = QBuffer()
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError("failed to allocate application icon buffer")
    if not canvas.save(buffer, "PNG"):
        raise RuntimeError(f"failed to encode application icon at {size}x{size}")
    return bytes(buffer.data())


def _write_ico(output_path: Path, images: list[tuple[int, bytes]]) -> None:
    offset = 6 + 16 * len(images)
    entries = []
    payloads = []
    for size, payload in images:
        dimension = 0 if size == 256 else size
        entries.append(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        payloads.append(payload)
        offset += len(payload)
    output_path.write_bytes(
        struct.pack("<HHH", 0, 1, len(images))
        + b"".join(entries)
        + b"".join(payloads)
    )


def prepare_windows_icon(source: PathSource, output: PathSource) -> Path:
    """Derive a deterministic multi-size ICO from one image. 从单一图片生成多尺寸 ICO。"""
    _, image = _load_application_icon(source)
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    images = [(size, _render_square_png(image, size)) for size in _WINDOWS_ICON_SIZES]
    _write_ico(output_path, images)
    return output_path


def nuitka_icon_options(
    source: PathSource,
    output_dir: PathSource,
    *,
    platform_name: str = sys.platform,
) -> List[str]:
    """Return the verified Nuitka icon option for one platform. 返回对应平台的 Nuitka 图标参数。"""
    source_path, _ = _load_application_icon(source)
    if platform_name == "win32":
        output_path = Path(output_dir) / "app_icon.ico"
        icon_path = prepare_windows_icon(source_path, output_path)
        return [f"--windows-icon-from-ico={icon_path}"]
    if platform_name == "darwin":
        return [f"--macos-app-icon={source_path}"]
    if platform_name.startswith("linux"):
        return [f"--linux-icon={source_path}"]
    raise ValueError(f"unsupported Nuitka icon platform: {platform_name}")
