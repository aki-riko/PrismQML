# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""单实例检查组件 - Windows使用Named Mutex，其他平台使用QSharedMemory

使用方式:
    from prismqml.python.core import SingleInstance

    # 方式1: 上下文管理器
    with SingleInstance("MyApp") as instance:
        if not instance.is_running:
            # 启动应用
            app.exec()

    # 方式2: 手动管理
    instance = SingleInstance("MyApp")
    if instance.try_lock():
        # 启动应用
        app.exec()
        instance.unlock()
    else:
        # Application already running 应用已在运行
        pass
"""

import platform
import sys
from typing import Optional, Callable

from PySide6.QtCore import QCoreApplication, QObject, QTimer, Signal

from .logger import getLogger

logger = getLogger()

# IPC 协议常量 IPC protocol constants
_ACTIVATE_MESSAGE = b"activate"  # 第二实例 -> 主实例:请求激活窗口
_ACK_MESSAGE = b"ok"             # 主实例 -> 第二实例:存活确认 ack
# 连接/读写等待超时(ms)。IPC 均为本地环回,正常应在毫秒级完成。
_IPC_TIMEOUT_MS = 500
# 等主实例回 ack 的超时(ms)。取值需大于活实例处理一次连接的耗时,
# 但又要短到用户可接受(超时后即接管启动)。1s 在实测中足以区分活实例与僵尸,
# 且远大于活实例正常回 ack 所需的几毫秒,不会误判慢启动的活实例。
_ACK_TIMEOUT_MS = 1000

# 平台检测
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    ERROR_ALREADY_EXISTS = 183

    # Define CreateMutexW
    kernel32.CreateMutexW.argtypes = [
        wintypes.LPVOID,  # lpMutexAttributes
        wintypes.BOOL,  # bInitialOwner
        wintypes.LPCWSTR,  # lpName
    ]
    kernel32.CreateMutexW.restype = wintypes.HANDLE

    # Define CloseHandle
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

if not IS_WINDOWS:
    from PySide6.QtCore import QSharedMemory, QSystemSemaphore


class SingleInstance(QObject):
    """单实例检查器 - 确保应用只运行一个实例

    除锁检测外,内置基于 QLocalServer/QLocalSocket 的轻量 IPC:
    - 主实例 try_lock() 成功后自动监听一个本地命名管道;
    - 第二实例 try_lock() 失败时,会向主实例发送一条 "activate" 消息后退出;
    - 主实例收到后发出 activateRequested 信号,应用可借此把主窗口提到前台
      (像 VSCode/Chrome 再次点击图标的体验)。

    Attributes:
        app_id: 应用唯一标识符
    """

    # 第二实例请求激活主窗口时发出(在主实例进程内)
    activateRequested = Signal()

    def __init__(self, app_id: str, on_second_instance: Optional[Callable] = None):
        """初始化单实例检查器

        Args:
            app_id: 应用唯一标识符，建议使用反向域名格式如 "com.example.myapp"
            on_second_instance: 当检测到第二个实例时的回调函数(在第二实例进程内调用)
        """
        super().__init__()
        self._app_id = app_id
        self._on_second_instance = on_second_instance
        self._is_locked = False

        # Windows特定属性
        self._mutex_handle = None

        # 非Windows特定属性
        self._shared_memory = None
        self._semaphore = None

        # IPC(跨平台,基于本地套接字)
        self._server = None
        self._quit_cleanup_registered = False

        if not IS_WINDOWS:
            self._shared_memory = QSharedMemory(app_id)
            self._semaphore = QSystemSemaphore(f"{app_id}_sem", 1)
            # 尝试修复崩溃残留
            self._fix_crash_residue()

    def _fix_crash_residue(self):
        """修复崩溃后残留的共享内存（仅非Windows平台可能需要）"""
        if IS_WINDOWS:
            return

        self._semaphore.acquire()
        try:
            if self._shared_memory.attach():
                self._shared_memory.detach()
        finally:
            self._semaphore.release()

    def _claim_primary(self) -> bool:
        """Commit primary ownership and start IPC. 提交主实例所有权并启动 IPC。"""
        self._is_locked = True
        self._register_quit_cleanup()
        self._start_server()
        return True

    def _register_quit_cleanup(self) -> None:
        """Release Qt resources before application teardown. 在应用析构前释放 Qt 资源。"""
        if self._quit_cleanup_registered:
            return
        app = QCoreApplication.instance()
        if app is None:
            return
        app.aboutToQuit.connect(self.unlock)
        self._quit_cleanup_registered = True

    def _notify_second_instance(self):
        """Invoke the optional second-instance callback. 调用可选的第二实例回调。"""
        if self._on_second_instance:
            self._on_second_instance()

    def _handle_existing_windows_mutex(self) -> bool:
        """Distinguish a live Windows primary from a stale mutex. 区分存活主实例与陈旧互斥体。"""
        if self._notify_primary():
            if self._mutex_handle:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None
            self._notify_second_instance()
            return False
        logger.warning("[SingleInstance] 检测到陈旧锁(主实例无响应),接管启动")
        return self._claim_primary()

    def _try_lock_windows(self) -> bool:
        """Try the Windows named-mutex path. 尝试 Windows 命名互斥体路径。"""
        mutex_name = f"Local\\{self._app_id}"
        self._mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            return self._handle_existing_windows_mutex()
        if self._mutex_handle:
            return self._claim_primary()
        return False

    def _handle_existing_shared_memory(self) -> bool:
        """Distinguish a live primary from stale shared memory. 区分存活主实例与陈旧共享内存。"""
        if self._notify_primary():
            self._shared_memory.detach()
            self._notify_second_instance()
            return False
        logger.warning("[SingleInstance] 检测到陈旧锁(主实例无响应),接管启动")
        return self._claim_primary()

    def _handle_shared_memory_race(self) -> bool:
        """Preserve the existing shared-memory race fallback. 保留既有共享内存竞态回退。"""
        if not self._shared_memory.attach():
            return False
        self._shared_memory.detach()
        self._notify_primary()
        self._notify_second_instance()
        return False

    def _try_lock_shared_memory(self) -> bool:
        """Try the non-Windows shared-memory path. 尝试非 Windows 共享内存路径。"""
        self._semaphore.acquire()
        try:
            if self._shared_memory.attach():
                return self._handle_existing_shared_memory()
            if self._shared_memory.create(1):
                return self._claim_primary()
            return self._handle_shared_memory_race()
        finally:
            self._semaphore.release()

    @property
    def app_id(self) -> str:
        """应用唯一标识符"""
        return self._app_id

    def try_lock(self) -> bool:
        """尝试获取单实例锁

        Returns:
            True: 成功获取锁，当前是唯一实例
            False: 获取锁失败，已有实例在运行
        """
        if self._is_locked:
            return True
        if IS_WINDOWS:
            return self._try_lock_windows()
        return self._try_lock_shared_memory()

    # ==================== IPC(激活已有窗口) ====================
    def _server_name(self) -> str:
        """本地套接字名(与 app_id 关联)。"""
        return f"{self._app_id}_ipc"

    def _start_server(self):
        """主实例:启动本地套接字监听,接收第二实例的激活请求。"""
        from PySide6.QtNetwork import QLocalServer

        # 清理可能的崩溃残留(同名 server 未正常关闭)
        QLocalServer.removeServer(self._server_name())
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_new_connection)
        if not self._server.listen(self._server_name()):
            # 监听失败不致命:单实例锁仍有效,只是少了激活能力
            self._server = None

    def _retain_connection(self, connection):
        """Retain a pending IPC connection until completion. 保持待处理 IPC 连接。"""
        if not hasattr(self, "_conns"):
            self._conns = []
        self._conns.append(connection)
        connection.disconnected.connect(
            lambda current=connection: self._release_connection(current)
        )
        connection.readChannelFinished.connect(
            lambda current=connection: self._release_connection(current)
        )
        connection.errorOccurred.connect(
            lambda _error, current=connection: self._release_connection(current)
        )
        connection.stateChanged.connect(
            lambda _state, current=connection: self._schedule_connection_check(current)
        )

    def _schedule_connection_check(self, connection):
        """Check a socket after Qt has delivered pending state changes. 延迟检查 Qt 待处理状态变化。"""
        QTimer.singleShot(0, lambda current=connection: self._release_if_closed(current))

    def _release_if_closed(self, connection):
        """Release sockets that closed before their signals were connected. 释放连接信号绑定前已关闭的套接字。"""
        if connection not in getattr(self, "_conns", []):
            return
        try:
            from PySide6.QtNetwork import QLocalSocket

            closed = (
                connection.state() == QLocalSocket.LocalSocketState.UnconnectedState
                or not connection.isOpen()
            )
        except (OSError, RuntimeError):
            closed = True
        if closed:
            self._release_connection(connection)

    def _release_connection(self, connection):
        """Release and schedule deletion of one IPC connection. 释放并延迟删除 IPC 连接。"""
        connections = getattr(self, "_conns", [])
        if connection not in connections:
            return
        connections.remove(connection)
        connection.deleteLater()

    def _read_connection_message(self, connection) -> str:
        """Read one IPC message with the existing fallback. 读取一条 IPC 消息并保留既有回退。"""
        try:
            return bytes(connection.readAll()).decode("utf-8", "ignore")
        except (OSError, RuntimeError) as exc:
            logger.debug(f"[SingleInstance] 读取 IPC 消息失败: {exc}")
            return ""

    def _send_ack(self, connection):
        """Send the primary-instance liveness acknowledgement. 发送主实例存活确认。"""
        try:
            connection.write(_ACK_MESSAGE)
            connection.flush()
            connection.waitForBytesWritten(_IPC_TIMEOUT_MS)
        except (OSError, RuntimeError) as exc:
            logger.warning(f"[SingleInstance] 回 ack 失败: {exc}")

    def _disconnect_connection(self, connection):
        """Disconnect and release one IPC connection. 断开并释放一条 IPC 连接。"""
        try:
            connection.disconnectFromServer()
        except (OSError, RuntimeError) as exc:
            logger.debug(f"[SingleInstance] 断开 IPC 连接失败: {exc}")
        finally:
            self._release_connection(connection)

    def _consume_connection(self, connection):
        """Consume an available IPC payload exactly once. 仅处理一次可用 IPC 载荷。"""
        if connection not in getattr(self, "_conns", []):
            return
        try:
            data = self._read_connection_message(connection)
            if data.startswith("activate"):
                self.activateRequested.emit()
                self._send_ack(connection)
        finally:
            self._disconnect_connection(connection)

    def _on_new_connection(self):
        """主实例:收到第二实例连接,读取消息后发 activateRequested。"""
        if not self._server:
            return
        connection = self._server.nextPendingConnection()
        if not connection:
            return
        self._retain_connection(connection)
        connection.readyRead.connect(
            lambda current=connection: self._consume_connection(current)
        )
        # 兜底:连接建立时数据可能已就绪(错过 readyRead 信号)
        if connection.bytesAvailable() > 0:
            self._consume_connection(connection)
        else:
            self._schedule_connection_check(connection)

    def _close_connections(self):
        """Abort and release every retained IPC connection. 中止并释放全部 IPC 连接。"""
        for connection in list(getattr(self, "_conns", [])):
            try:
                connection.abort()
            except (OSError, RuntimeError) as exc:
                logger.debug(f"[SingleInstance] 中止 IPC 连接失败: {exc}")
            finally:
                self._release_connection(connection)

    def _notify_primary(self) -> bool:
        """第二实例:连接主实例、发激活请求并等待 ack。

        返回值语义(存活探测):
        - True:收到主实例回的 ack,证明主实例事件循环仍在运行(活实例);
        - False:连不上,或连上后等 ack 超时——主实例已死或卡死成僵尸,
          其持有的锁应视为陈旧锁,调用方可接管启动。

        注意:仅凭 connectToServer 成功无法区分死活——卡死进程的 socket 仍会被
        操作系统 backlog 接受连接(已实测)。故必须以应用层 ack 往返为准。
        """
        from PySide6.QtNetwork import QLocalSocket

        sock = QLocalSocket()
        sock.connectToServer(self._server_name())
        if not sock.waitForConnected(_IPC_TIMEOUT_MS):
            return False
        sock.write(_ACTIVATE_MESSAGE)
        sock.flush()
        sock.waitForBytesWritten(_IPC_TIMEOUT_MS)
        got_ack = sock.waitForReadyRead(_ACK_TIMEOUT_MS)
        if got_ack:
            got_ack = self._read_primary_ack(sock).startswith(_ACK_MESSAGE)
        self._disconnect_primary_socket(sock, QLocalSocket)
        return got_ack

    @staticmethod
    def _read_primary_ack(sock) -> bytes:
        """Read the primary acknowledgement with the existing fallback. 读取主实例确认并保留既有回退。"""
        try:
            return bytes(sock.readAll())
        except (OSError, RuntimeError):
            return b""

    @staticmethod
    def _disconnect_primary_socket(sock, socket_type):
        """Disconnect the second-instance probe socket. 断开第二实例探测套接字。"""
        sock.disconnectFromServer()
        if sock.state() != socket_type.LocalSocketState.UnconnectedState:
            sock.waitForDisconnected(_IPC_TIMEOUT_MS)

    def unlock(self):
        """释放单实例锁"""
        if not self._is_locked:
            return

        # 关闭 IPC 监听
        if self._server is not None:
            try:
                self._server.close()
            except (OSError, RuntimeError) as exc:
                logger.debug(f"[SingleInstance] 关闭 IPC server 失败: {exc}")
            self._server = None
        self._close_connections()

        if IS_WINDOWS:
            if self._mutex_handle:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None
        else:
            if self._shared_memory:
                self._shared_memory.detach()

        self._is_locked = False

    def __enter__(self) -> "SingleInstance":
        self.try_lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()
        return False

    def __del__(self):
        self.unlock()


# 全局引用保持，防止被GC
_global_instance = None


def ensure_single_instance(
    app_id: str, on_second_instance: Optional[Callable] = None
) -> bool:
    """便捷函数：确保单实例运行

    Args:
        app_id: 应用唯一标识符
        on_second_instance: 当检测到第二个实例时的回调函数

    Returns:
        True: 当前是唯一实例，可以继续运行
        False: 已有实例在运行，应该退出
    """
    global _global_instance
    instance = SingleInstance(app_id, on_second_instance)
    if instance.try_lock():
        # 保持实例引用，防止被垃圾回收导致锁释放
        _global_instance = instance

        # 注册退出清理
        import atexit

        atexit.register(instance.unlock)
        return True
    return False
