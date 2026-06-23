# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
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

from PySide6.QtCore import QObject, Signal

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
            # Windows Implementation: Named Mutex
            # 命名约定: Local\ 前缀确保在当前会话中唯一
            mutex_name = f"Local\\{self._app_id}"

            self._mutex_handle = kernel32.CreateMutexW(None, True, mutex_name)
            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                # Mutex已存在，说明有实例在运行
                # 关闭我们刚刚获取到的句柄（因为我们要退出了）
                if self._mutex_handle:
                    kernel32.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None

                # 通知主实例激活窗口
                self._notify_primary()
                if self._on_second_instance:
                    self._on_second_instance()
                return False

            # 成功创建Mutex并持有所有权
            if self._mutex_handle:
                self._is_locked = True
                self._start_server()  # 启动 IPC 监听,接收后续实例的激活请求
                return True

            return False

        else:
            # Non-Windows Implementation: QSharedMemory
            self._semaphore.acquire()
            try:
                # 尝试attach到已存在的共享内存
                if self._shared_memory.attach():
                    self._shared_memory.detach()
                    self._notify_primary()
                    if self._on_second_instance:
                        self._on_second_instance()
                    return False

                # 创建共享内存
                if self._shared_memory.create(1):
                    self._is_locked = True
                    self._start_server()
                    return True

                # 竞态条件
                if self._shared_memory.attach():
                    self._shared_memory.detach()
                    self._notify_primary()
                    if self._on_second_instance:
                        self._on_second_instance()
                    return False

                return False
            finally:
                self._semaphore.release()

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

    def _on_new_connection(self):
        """主实例:收到第二实例连接,读取消息后发 activateRequested。"""
        if not self._server:
            return
        conn = self._server.nextPendingConnection()
        if not conn:
            return
        # 保存引用防止被 GC(否则 readyRead 回调前对象就被回收)
        if not hasattr(self, "_conns"):
            self._conns = []
        self._conns.append(conn)

        def _handle():
            try:
                data = bytes(conn.readAll()).decode("utf-8", "ignore")
            except Exception:  # noqa: BLE001
                data = ""
            if data.startswith("activate"):
                self.activateRequested.emit()
            try:
                conn.disconnectFromServer()
            except Exception:  # noqa: BLE001
                pass
            if conn in self._conns:
                self._conns.remove(conn)

        def _ready():
            # 数据到齐再处理(activate 很短,一次 readyRead 即可)
            if conn.bytesAvailable() > 0:
                _handle()

        conn.readyRead.connect(_ready)
        # 兜底:连接建立时数据可能已就绪(错过 readyRead 信号)
        if conn.bytesAvailable() > 0:
            _handle()

    def _notify_primary(self) -> bool:
        """第二实例:连接主实例并发送激活请求。返回是否成功送达。"""
        from PySide6.QtNetwork import QLocalSocket

        sock = QLocalSocket()
        sock.connectToServer(self._server_name())
        if not sock.waitForConnected(500):
            return False
        sock.write(b"activate")
        sock.flush()
        sock.waitForBytesWritten(500)
        # 不立即 disconnect:等待数据被主实例读取(否则主实例 accept 前连接就断)。
        # waitForDisconnected 让主实例有机会处理;超时也无妨,进程即将退出。
        sock.disconnectFromServer()
        if sock.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            sock.waitForDisconnected(500)
        return True

    def unlock(self):
        """释放单实例锁"""
        if not self._is_locked:
            return

        # 关闭 IPC 监听
        if self._server is not None:
            try:
                self._server.close()
            except Exception:  # noqa: BLE001
                pass
            self._server = None

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
