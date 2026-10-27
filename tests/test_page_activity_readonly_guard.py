# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""页面活动状态同步必须容忍只读属性（回归 2026-10-28 定位的切页卡死）。

背景：``StackedPageActivityController._setActivity`` 用 ``"pageActive" in page``
判断页面是否参与活动状态契约，但 **只读** 属性同样满足 ``in``，直接赋值会抛：

    TypeError: Cannot assign to read-only property "pageActive"

异常沿 ``sync()`` → ``_updateVisibility()`` → ``cancelPendingLazySwitch()``
冒泡，把「上一次切页未收尾就点下一页」的切换在 retarget 取消后中断，
``_displayIndex`` 永远停在旧页——用户点导航但内容区不变（实测 100% 复现）。

修复方式是在每次写入外层加 try/catch（只读属性写入失败即跳过）。

本测试对 **源代码** 做契约断言，不依赖 QML 运行时脚手架，因此稳定可用：
1. ``_setActivity`` 必须通过 ``_writeActivity`` 写入，而不是裸赋值；
2. ``_writeActivity`` 必须包含 try/catch（否则只读属性照样抛出）；
3. 可写属性的写入路径仍然存在（不改变原有行为）。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "_internal"
    / "StackedPageActivityController.qml"
)


def _source() -> str:
    return CONTROLLER.read_text(encoding="utf-8")


def test_controller_file_exists() -> None:
    """脚手架前提：控制器文件路径必须存在（防止改名后测试静默失效）。"""
    assert CONTROLLER.is_file(), f"找不到 {CONTROLLER}"


def test_set_activity_uses_guarded_writer() -> None:
    """_setActivity 不得对 page 裸赋值，必须走带 try/catch 的写入函数。"""
    source = _source()
    match = re.search(
        r"function _setActivity\(page, active\)\s*\{(?P<body>.*?)\n    \}",
        source,
        re.S,
    )
    assert match is not None, "_setActivity 未找到"
    body = match.group("body")

    bare_assign = re.search(r"\bpage\.(schedulerActive|pageActive)\s*=", body)
    assert bare_assign is None, (
        "只读属性直接赋值会抛 TypeError 并令切页卡死，"
        f"必须改为受保护写入；仍发现: {bare_assign.group(0) if bare_assign else ''}"
    )
    assert "_writeActivity" in body, "_setActivity 必须通过 _writeActivity 写入"


def test_write_activity_swallows_readonly_error() -> None:
    """_writeActivity 必须用 try/catch 吞掉只读属性写入错误。"""
    source = _source()
    match = re.search(
        r"function _writeActivity\(page, name, active\)\s*\{(?P<body>.*?)\n    \}",
        source,
        re.S,
    )
    assert match is not None, "_writeActivity 未找到"
    body = match.group("body")

    assert "try" in body, "_writeActivity 必须用 try 包裹赋值"
    assert "catch" in body, "_writeActivity 必须用 catch 吞掉只读属性错误"
    assert re.search(r"page\[name\]\s*=", body), (
        "_writeActivity 必须通过 page[name] 写入（支持两个活动属性名）"
    )


def test_writable_path_preserved() -> None:
    """不得为了修缺陷而取消可写属性的写入（原有行为必须保留）。"""
    source = _source()
    assert '_writeActivity(page, "schedulerActive", active)' in source
    assert '_writeActivity(page, "pageActive", active)' in source
