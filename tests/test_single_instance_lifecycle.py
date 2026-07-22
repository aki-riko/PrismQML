# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SingleInstance IPC lifecycle regressions. 单实例 IPC 生命周期回归。"""

import ast
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtTest import QSignalSpy

import prismqml.python.core.single_instance as single_instance_module
from prismqml.python.core.single_instance import SingleInstance


SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "prismqml"
    / "python"
    / "core"
    / "single_instance.py"
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _new_instance() -> SingleInstance:
    app_id = f"PrismQML.SingleInstanceTest.{uuid4().hex}"
    instance = SingleInstance(app_id)
    assert instance.try_lock()
    return instance


def _connect(instance: SingleInstance) -> QLocalSocket:
    client = QLocalSocket()
    client.connectToServer(instance._server_name())
    assert client.waitForConnected(1000)
    return client


def _cleanup(instance: SingleInstance, client: QLocalSocket) -> None:
    client.abort()
    for connection in list(getattr(instance, "_conns", [])):
        connection.abort()
        connection.deleteLater()
    if hasattr(instance, "_conns"):
        instance._conns.clear()
    instance.unlock()
    _pump(1)


def test_activate_payload_emits_once_returns_ack_and_releases_connection(qapp):
    instance = _new_instance()
    client = _connect(instance)
    spy = QSignalSpy(instance.activateRequested)
    try:
        assert client.write(b"activate") == len(b"activate")
        client.flush()
        _pump(50)
        reply = bytes(client.readAll())
        assert spy.count() == 1
        assert reply.startswith(b"ok")
        assert getattr(instance, "_conns", []) == []
    finally:
        _cleanup(instance, client)


def test_no_payload_disconnect_releases_server_connection(qapp):
    instance = _new_instance()
    client = _connect(instance)
    try:
        client.disconnectFromServer()
        if client.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            client.waitForDisconnected(1000)
        _pump(50)
        assert getattr(instance, "_conns", []) == []
    finally:
        _cleanup(instance, client)


def test_unlock_aborts_and_releases_active_connections(qapp):
    instance = _new_instance()
    client = _connect(instance)
    try:
        _pump(20)
        assert len(getattr(instance, "_conns", [])) == 1
        instance.unlock()
        _pump(20)
        assert getattr(instance, "_conns", []) == []
        assert client.state() == QLocalSocket.LocalSocketState.UnconnectedState
    finally:
        _cleanup(instance, client)


class _SignalStub:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self):
        for callback in tuple(self.callbacks):
            callback()


def test_primary_lock_releases_resources_before_application_teardown(monkeypatch):
    about_to_quit = _SignalStub()
    app = SimpleNamespace(aboutToQuit=about_to_quit)
    monkeypatch.setattr(
        single_instance_module.QCoreApplication,
        "instance",
        staticmethod(lambda: app),
    )
    instance = SingleInstance(f"PrismQML.QuitCleanupTest.{uuid4().hex}")
    instance._start_server = lambda: None

    assert instance._claim_primary()
    assert instance._is_locked
    assert len(about_to_quit.callbacks) == 1

    about_to_quit.emit()

    assert not instance._is_locked
    assert instance._server is None


def test_connection_lifecycle_methods_stay_small_and_delegated():
    tree = ast.parse(
        SOURCE_PATH.read_text(encoding="utf-8"),
        filename=str(SOURCE_PATH),
        feature_version=(3, 9),
    )
    target_names = {
        "_retain_connection",
        "_release_connection",
        "_read_connection_message",
        "_send_ack",
        "_disconnect_connection",
        "_consume_connection",
        "_on_new_connection",
        "_close_connections",
    }
    single_instance = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SingleInstance"
    )
    methods = {
        node.name: node for node in single_instance.body if isinstance(node, ast.FunctionDef)
    }
    assert target_names <= set(methods)
    assert all(
        methods[name].end_lineno - methods[name].lineno + 1 <= 30
        for name in target_names
    )
