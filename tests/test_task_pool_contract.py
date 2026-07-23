# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Managed task-pool contract regressions. 受管任务线程池契约回归。"""

import pytest
from PySide6.QtCore import QThreadPool

from prismqml import PoolTaskOptions


def test_raw_qthread_pool_is_rejected_for_safe_clear_contract(qapp) -> None:
    """Raw pools cannot provide clear settlement. 原生线程池不满足清理结算契约。"""
    with pytest.raises(TypeError, match="TaskThreadPool"):
        PoolTaskOptions(pool=QThreadPool())


def test_global_task_pool_is_shared_by_public_imports(qapp) -> None:
    """The managed default pool has one public identity. 默认受管池保持单一公开身份。"""
    import prismqml
    from prismqml.python import core

    assert prismqml.global_task_pool is core.global_task_pool
