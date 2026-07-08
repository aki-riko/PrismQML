# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Generated QML cache helpers 生成 QML 缓存辅助函数。"""

import hashlib
from pathlib import Path

from ..core.logger import debug


GENERATED_WINDOW_QML_CACHE_DIR = (
    Path.home() / ".prismqml" / "qml_cache" / "generated_windows"
)
GENERATED_SPLASH_QML_CACHE_DIR = (
    Path.home() / ".prismqml" / "qml_cache" / "generated_splash"
)


def write_generated_qml(
    source: str,
    cache_dir: Path,
    prefix: str,
    debug_tag: str,
) -> Path:
    """Write generated QML to a stable content-addressed file 写入稳定缓存文件。"""
    source_bytes = source.encode("utf-8")
    digest = hashlib.sha256(source_bytes).hexdigest()[:20]
    qml_file = cache_dir / f"{prefix}_{digest}.qml"

    cache_dir.mkdir(parents=True, exist_ok=True)
    if qml_file.exists():
        try:
            if qml_file.read_bytes() == source_bytes:
                return qml_file
        except OSError as exc:
            debug(f"{debug_tag} 读取生成 QML 缓存失败: {exc}")

    qml_file.write_bytes(source_bytes)
    return qml_file
