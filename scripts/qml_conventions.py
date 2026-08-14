# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public QML convention scanner API. QML 规范扫描器公开接口。"""

if __package__:
    from ._qml_lint.qml_conventions import (
        Violation,
        scan_changed,
        scan_repository,
        scan_source_text,
        scan_text,
    )
else:
    from _qml_lint.qml_conventions import (
        Violation,
        scan_changed,
        scan_repository,
        scan_source_text,
        scan_text,
    )


__all__ = (
    "Violation",
    "scan_changed",
    "scan_repository",
    "scan_source_text",
    "scan_text",
)
