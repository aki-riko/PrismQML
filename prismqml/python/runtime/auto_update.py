# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Application auto-update composition. 应用自动更新运行时装配。"""

from .context_registry import register_context_property


def enable_auto_update(
    owner,
    repo: str,
    current_version: str,
    asset_keyword: str = "Setup",
    *,
    install_strategy: str = "in_place",
):
    """Create, retain, and expose the application updater. 创建、持有并暴露应用更新器。"""
    from ..core import Updater

    if owner._engine is None:
        from ..core.logger import warning

        warning("App enable_auto_update: 引擎未就绪，无法启用自动更新")
        return None

    owner._updater = Updater(
        repo,
        current_version,
        asset_keyword,
        None,
        install_strategy=install_strategy,
    )
    owner._updater.set_require_artifact_digest(True)
    register_context_property(
        owner._engine.rootContext(), "appUpdater", owner._updater
    )
    return owner._updater
