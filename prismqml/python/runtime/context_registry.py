# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared QML context and provider registration primitives. 共享 QML 注册原语。"""

_CONTEXT_REGISTRATION_LEVEL_ATTR = "_prismqml_context_registration_level"
_REGISTERED_IMAGE_PROVIDERS_ATTR = "_prismqml_registered_image_providers"

WINDOW_CONTEXT_REGISTRATION = 1
FULL_CONTEXT_REGISTRATION = 2


def register_context_property(context, name: str, value) -> None:
    """Register one QML context property. 注册一个 QML context 属性。"""
    context.setContextProperty(name, value)


def context_registration_level(engine) -> int:
    """Return the highest context registration level on an engine. 获取引擎注册级别。"""
    return int(getattr(engine, _CONTEXT_REGISTRATION_LEVEL_ATTR, 0))


def mark_context_registration(engine, level: int) -> None:
    """Record a completed context registration level. 记录已完成的注册级别。"""
    current = context_registration_level(engine)
    if level > current:
        setattr(engine, _CONTEXT_REGISTRATION_LEVEL_ATTR, level)


def register_image_provider_once(engine, name: str, factory) -> bool:
    """Register one provider once per engine. 每个引擎只注册一次 provider。"""
    registered = set(
        getattr(engine, _REGISTERED_IMAGE_PROVIDERS_ATTR, ())
    )
    if name in registered:
        return False

    provider = factory()
    engine.addImageProvider(name, provider)
    registered.add(name)
    setattr(engine, _REGISTERED_IMAGE_PROVIDERS_ATTR, tuple(sorted(registered)))
    return True
