# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared QML registration contracts. 共享 QML 注册合同。"""

import pytest

from prismqml.python.runtime import context_registry


class _Engine:
    def __init__(self):
        self.calls = []

    def addImageProvider(self, name, provider):
        self.calls.append((name, provider))


class _Context:
    def __init__(self):
        self.calls = []

    def setContextProperty(self, name, value):
        self.calls.append((name, value))


def test_context_properties_run_factories_in_registration_order():
    context = _Context()
    calls = []

    context_registry.register_context_properties(
        context,
        (
            ("first", lambda: calls.append("first") or 1),
            ("second", lambda: calls.append("second") or 2),
        ),
    )

    assert calls == ["first", "second"]
    assert context.calls == [("first", 1), ("second", 2)]


def test_context_registration_level_only_moves_forward():
    engine = _Engine()

    assert context_registry.context_registration_level(engine) == 0
    context_registry.mark_context_registration(
        engine, context_registry.FULL_CONTEXT_REGISTRATION
    )
    context_registry.mark_context_registration(
        engine, context_registry.WINDOW_CONTEXT_REGISTRATION
    )

    assert (
        context_registry.context_registration_level(engine)
        == context_registry.FULL_CONTEXT_REGISTRATION
    )


def test_image_provider_registration_is_idempotent():
    engine = _Engine()
    provider = object()
    calls = []

    assert (
        context_registry.register_image_provider_once(
            engine, "svg", lambda: calls.append("factory") or provider
        )
        is True
    )
    assert (
        context_registry.register_image_provider_once(
            engine, "svg", lambda: calls.append("duplicate")
        )
        is False
    )

    assert calls == ["factory"]
    assert engine.calls == [("svg", provider)]


def test_image_provider_registration_can_retry_after_add_failure():
    class _FailingEngine(_Engine):
        def __init__(self):
            super().__init__()
            self.fail = True

        def addImageProvider(self, name, provider):
            if self.fail:
                self.fail = False
                raise RuntimeError("provider add failed")
            super().addImageProvider(name, provider)

    engine = _FailingEngine()
    provider = object()

    with pytest.raises(RuntimeError, match="provider add failed"):
        context_registry.register_image_provider_once(
            engine, "svg", lambda: provider
        )

    assert context_registry.register_image_provider_once(
        engine, "svg", lambda: provider
    )
    assert engine.calls == [("svg", provider)]
