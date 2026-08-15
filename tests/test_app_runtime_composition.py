# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""App auto-update composition contracts. App 自动更新装配合同。"""

from types import SimpleNamespace


class _Context:
    def __init__(self, calls):
        self._calls = calls

    def setContextProperty(self, name, value):
        self._calls.append(("context", name, value))


class _Engine:
    def __init__(self, calls):
        self._calls = calls
        self._context = _Context(calls)

    def rootContext(self):
        self._calls.append("rootContext")
        return self._context


class _Updater:
    instances = []

    def __init__(self, *args, **kwargs):
        self.calls = [("init", args, kwargs)]
        self.__class__.instances.append(self)

    def set_require_artifact_digest(self, enabled):
        self.calls.append(("set_require_artifact_digest", enabled))


def test_enable_auto_update_preserves_runtime_composition_contract(monkeypatch):
    from prismqml.python.core import Updater as original_updater
    from prismqml.python.window.app import App
    import prismqml.python.core as core

    calls = []
    _Updater.instances = []
    monkeypatch.setattr(core, "Updater", _Updater)
    owner = SimpleNamespace(_engine=_Engine(calls), _updater=None)

    result = App.enable_auto_update(
        owner,
        "OWNER/REPO",
        "v1.2.3",
        "Setup",
        install_strategy="dual_slot",
    )

    assert original_updater is not _Updater
    assert len(_Updater.instances) == 1
    updater = _Updater.instances[0]
    assert result is updater
    assert owner._updater is updater
    assert updater.calls == [
        (
            "init",
            ("OWNER/REPO", "v1.2.3", "Setup", None),
            {"install_strategy": "dual_slot"},
        ),
        ("set_require_artifact_digest", True),
    ]
    assert calls == ["rootContext", ("context", "appUpdater", updater)]


def test_enable_auto_update_rejects_unready_engine_without_creating_updater(
    monkeypatch,
):
    from prismqml.python.window.app import App
    import prismqml.python.core.logger as logger

    warnings = []
    monkeypatch.setattr(logger, "warning", warnings.append)
    owner = SimpleNamespace(_engine=None, _updater=None)

    assert (
        App.enable_auto_update(owner, "OWNER/REPO", "v1.2.3")
        is None
    )
    assert owner._updater is None
    assert warnings == [
        "App enable_auto_update: 引擎未就绪，无法启用自动更新"
    ]
