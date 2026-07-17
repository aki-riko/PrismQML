# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SingleInstance IPC lifecycle regressions. 单实例 IPC 生命周期回归。"""

from uuid import uuid4

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtTest import QSignalSpy

from prismqml.python.core.single_instance import SingleInstance


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


def test_no_payload_disconnect_reproduces_retained_connection(qapp):
    instance = _new_instance()
    client = _connect(instance)
    try:
        client.disconnectFromServer()
        if client.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            client.waitForDisconnected(1000)
        _pump(50)
        retained = getattr(instance, "_conns", [])
        assert len(retained) == 1
        assert retained[0].state() == QLocalSocket.LocalSocketState.UnconnectedState
        assert retained[0].bytesAvailable() == 0
    finally:
        _cleanup(instance, client)
