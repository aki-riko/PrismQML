# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""通用应用更新组件 - 基于 GitHub Releases 的检测 / 下载 / 静默安装。

设计为引擎级通用组件(与 SingleInstance 平级),任何基于 PrismQML 的应用都可复用:
仅依赖 PySide6 自带的 QNetworkAccessManager / QProcess,不引入第三方网络库。

典型用法(应用层)::

    from prismqml import Updater

    updater = Updater("owner/repo", "v1.0.3", asset_keyword="Setup")
    ctx.setContextProperty("Updater", updater)
    # QML 侧:Updater.checkForUpdate() / 接 updateAvailable 信号 / downloadUpdate(url)
    #          / runInstallerAndQuit(path, "/VERYSILENT")

所有网络操作均异步,通过信号回传结果;不阻塞 GUI 线程。
"""

import ctypes
import os
import sys
import tempfile
from typing import Optional

if sys.platform == "win32":
    from ctypes import wintypes
else:
    wintypes = None

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
    QCoreApplication,
    QProcess,
    QUrl,
    QStandardPaths,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

from .logger import getLogger

logger = getLogger()

# GitHub API 要求带 User-Agent,否则返回 403。
_USER_AGENT = b"PrismQML-Updater"
_UPDATER_API_BASE_ENV = "PRISMQML_UPDATER_API_BASE_URL"
_DEFAULT_API_BASE_URL = "https://api.github.com"
_SHELL_EXECUTE_ERRORS = (
    OSError,
    AttributeError,
    ctypes.ArgumentError,
    TypeError,
    ValueError,
)


def _normalize_api_base_url(value: Optional[str]) -> str:
    """Normalize one API base candidate. 归一化单个 API 根地址候选值。"""
    return str(value or "").strip().rstrip("/")


def _resolve_api_base_url(api_base_url: Optional[str]) -> str:
    """Resolve explicit, environment, then default API base. 解析更新 API 根地址。"""
    for candidate in (
        api_base_url,
        os.environ.get(_UPDATER_API_BASE_ENV),
        _DEFAULT_API_BASE_URL,
    ):
        normalized = _normalize_api_base_url(candidate)
        if normalized:
            return normalized
    return _DEFAULT_API_BASE_URL


def _latest_release_url(repo: str, api_base_url: Optional[str] = None) -> str:
    """Build the latest-release endpoint. 构造 latest release 端点。"""
    normalized_repo = repo.strip().strip("/")
    return f"{_resolve_api_base_url(api_base_url)}/repos/{normalized_repo}/releases/latest"


def _normalize_version_tag(tag: str) -> str:
    """Normalize prefix and build metadata. 归一化前缀与构建元数据。"""
    normalized = tag.strip()
    if normalized[:1] in ("v", "V"):
        normalized = normalized[1:]
    return normalized.partition("+")[0].strip()


def _parse_version_segments(value: str) -> tuple:
    """Parse dot-separated precedence segments. 解析点分优先级片段。"""
    segments = []
    for raw_segment in value.split("."):
        segment = raw_segment.strip()
        if not segment:
            continue
        if segment.isascii() and segment.isdigit():
            segments.append((0, int(segment)))
        else:
            segments.append((1, segment))
    return tuple(segments)


def _parse_version(tag: str) -> tuple:
    """把版本号(如 'v1.0.3' / '1.2.0-beta')解析成可比较的元组。

    返回 ``(core, pre_marker)`` 二元组:
    - core: 主版本号各段(去前导 'v',按 '.' 拆,纯数字转 int,非数字保留为
      (1, str) 排在数字之后)。
    - pre_marker: 预发布标记。无预发布(无 '-')为 ``(1,)``,有预发布为
      ``(0,) + 预发布各段``。保证 core 相同时正式版 > 预发布版
      (如 '1.0.0' > '1.0.0-beta'),符合语义版本直觉。
    构建元数据不参与优先级；空白或仅 v/V 前缀返回 ``()``,视为最小版本。
    """
    normalized = _normalize_version_tag(tag)
    if not normalized:
        return ()

    core_str, separator, prerelease_str = normalized.partition("-")
    core = _parse_version_segments(core_str)
    if separator:  # 有 '-',是预发布版,排在同 core 正式版之前
        pre_marker = (0,) + _parse_version_segments(prerelease_str)
    else:    # 无预发布,正式版,排在最后(更大)
        pre_marker = (1,)
    return (core, pre_marker)


def _is_newer(latest: str, current: str) -> bool:
    """latest 是否比 current 新。两者均做 _parse_version 后逐段比较。"""
    return _parse_version(latest) > _parse_version(current)


def _pick_asset(assets: list, keyword: str) -> Optional[dict]:
    """从 release 的 assets 列表中挑选安装包。

    优先返回:名字含 keyword(不区分大小写)且以 .exe 结尾的第一个;
    其次:任意以 .exe 结尾的;再次:第一个 asset;空列表返回 None。
    """
    if not assets:
        return None
    kw = (keyword or "").lower()
    exe_assets = [a for a in assets if str(a.get("name", "")).lower().endswith(".exe")]
    if kw:
        for a in exe_assets:
            if kw in str(a.get("name", "")).lower():
                return a
    if exe_assets:
        return exe_assets[0]
    return assets[0]


def _configure_shell_execute():
    """Configure ShellExecuteW's pointer-safe ctypes contract. 配置指针安全签名。"""
    shell_execute = ctypes.windll.shell32.ShellExecuteW
    shell_execute.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_int,
    ]
    shell_execute.restype = wintypes.HINSTANCE
    return shell_execute


def _launch_windows_installer(installer_path: str, args: list[str]) -> bool:
    """Launch through the manifest-aware Windows shell. 通过 Windows shell 启动。"""
    try:
        shell_execute = _configure_shell_execute()
        result = int(shell_execute(
            None, "open", installer_path, " ".join(args) or None, None, 1
        ) or 0)
    except _SHELL_EXECUTE_ERRORS as exc:
        logger.exception(
            "[Updater] 启动安装包异常: "
            f"{type(exc).__name__}: {exc}"
        )
        return False
    if result <= 32:
        logger.warning(
            f"[Updater] 启动安装包失败(ShellExecute 返回 {result}): {installer_path}"
        )
        return False
    return True


def _launch_detached_installer(installer_path: str, args: list[str]) -> bool:
    """Launch through QProcess without blocking. 通过 QProcess 分离启动。"""
    ok, _pid = QProcess.startDetached(installer_path, args)
    if not ok:
        logger.warning(f"[Updater] 启动安装包失败: {installer_path}")
    return ok


class Updater(QObject):
    """基于 GitHub Releases 的应用更新器。

    检测最新 release、比对版本、异步下载安装包、静默安装并重启。
    所有结果经信号回传;同一时刻只处理一个下载任务。

    Attributes:
        repo: GitHub 仓库 "owner/repo"。
        current_version: 当前应用版本(如 "v1.0.3")。
        asset_keyword: 从 release assets 中挑安装包的关键词(默认 "Setup")。
        api_base_url: GitHub/GitHub Enterprise API 根地址；显式值优先于环境变量。
    """

    # 检测结果
    updateAvailable = Signal(str, str, str, str)  # (version, notes, downloadUrl, htmlUrl)
    upToDate = Signal(str)                          # (currentVersion)
    checkFailed = Signal(str)                       # (errorMessage)
    # 下载过程
    downloadProgress = Signal(int, int)             # (received, total)
    downloadFinished = Signal(str)                  # (localPath)
    downloadFailed = Signal(str)                    # (errorMessage)

    def __init__(
        self,
        repo: str,
        current_version: str,
        asset_keyword: str = "Setup",
        parent: Optional[QObject] = None,
        *,
        api_base_url: Optional[str] = None,
    ):
        super().__init__(parent)
        self._repo = repo
        self._current_version = current_version
        self._asset_keyword = asset_keyword
        self._api_base_url = _resolve_api_base_url(api_base_url)
        self._nam = QNetworkAccessManager(self)
        self._check_reply: Optional[QNetworkReply] = None
        self._download_reply: Optional[QNetworkReply] = None
        self._download_file = None  # 打开的目标文件句柄
        self._download_path = ""

    @property
    def api_base_url(self) -> str:
        """Resolved API base URL. 已解析的更新 API 根地址。"""
        return self._api_base_url

    # ==================== 检测 ====================
    @Slot()
    def checkForUpdate(self):
        """异步请求 GitHub latest release,完成后发 updateAvailable / upToDate / checkFailed。"""
        if self._check_reply is not None:
            logger.debug("[Updater] 已有检测请求在进行,忽略重复调用")
            return
        url = _latest_release_url(self._repo, self._api_base_url)
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", _USER_AGENT)
        req.setRawHeader(b"Accept", b"application/vnd.github+json")
        # 下载 asset 时会 302 到对象存储,这里统一允许安全重定向。
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                         QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        self._check_reply = self._nam.get(req)
        self._check_reply.finished.connect(self._on_check_finished)

    def _on_check_finished(self):
        reply = self._check_reply
        self._check_reply = None
        if reply is None:
            return
        try:
            err = reply.error()
            if err != QNetworkReply.NetworkError.NoError:
                msg = reply.errorString()
                logger.warning(f"[Updater] 检测更新网络错误: {msg}")
                self.checkFailed.emit(msg)
                return
            raw = bytes(reply.readAll())
        finally:
            reply.deleteLater()
        self._process_release_data(raw)

    def _process_release_data(self, raw: bytes):
        """解析 latest release 的 JSON 原始字节,发对应信号。

        从网络回调中抽出,便于注入假数据做单元测试(见 _inject_release_for_test)。
        """
        import json
        try:
            data = json.loads(raw.decode("utf-8", "ignore"))
        except (ValueError, UnicodeDecodeError) as e:
            logger.warning(f"[Updater] 解析 release JSON 失败: {e}")
            self.checkFailed.emit("解析更新信息失败")
            return

        tag = str(data.get("tag_name", ""))
        if not tag:
            self.checkFailed.emit("未找到发布版本")
            return

        if _is_newer(tag, self._current_version):
            notes = str(data.get("body", "") or "")
            html_url = str(data.get("html_url", "") or "")
            asset = _pick_asset(data.get("assets", []) or [], self._asset_keyword)
            download_url = str(asset.get("browser_download_url", "")) if asset else ""
            logger.info(f"[Updater] 发现新版本 {tag}(当前 {self._current_version})")
            self.updateAvailable.emit(tag, notes, download_url, html_url)
        else:
            logger.debug(f"[Updater] 已是最新版本 {self._current_version}")
            self.upToDate.emit(self._current_version)

    def _inject_release_for_test(self, raw: bytes):
        """测试专用:直接喂入 release JSON 字节,走与网络回调相同的解析路径。"""
        self._process_release_data(raw)

    # ==================== 下载 ====================
    @Slot(str)
    def downloadUpdate(self, url: str):
        """异步下载安装包到系统临时目录,过程发 downloadProgress,
        完成发 downloadFinished(localPath),失败发 downloadFailed。"""
        if not url:
            self.downloadFailed.emit("下载地址为空")
            return
        if self._download_reply is not None:
            logger.debug("[Updater] 已有下载在进行,忽略重复调用")
            return

        # 目标文件名:取 URL 末段;放到临时目录,避免污染用户目录。
        name = QUrl(url).fileName() or "update_installer.exe"
        tmp_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation) \
            or tempfile.gettempdir()
        self._download_path = os.path.join(tmp_dir, name)

        try:
            # 已存在的旧文件先删,避免追加写脏数据。
            if os.path.exists(self._download_path):
                os.remove(self._download_path)
            self._download_file = open(self._download_path, "wb")
        except OSError as e:
            logger.warning(f"[Updater] 创建下载文件失败: {e}")
            self.downloadFailed.emit(f"创建下载文件失败: {e}")
            self._download_file = None
            return

        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", _USER_AGENT)
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                         QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        self._download_reply = self._nam.get(req)
        self._download_reply.downloadProgress.connect(self._on_download_progress)
        self._download_reply.readyRead.connect(self._on_download_ready_read)
        self._download_reply.finished.connect(self._on_download_finished)

    def _on_download_progress(self, received: int, total: int):
        self.downloadProgress.emit(int(received), int(total))

    def _on_download_ready_read(self):
        # 边收边写,避免大文件全部驻留内存。
        if self._download_reply is not None and self._download_file is not None:
            try:
                self._download_file.write(bytes(self._download_reply.readAll()))
            except OSError as e:
                logger.warning(f"[Updater] 写入下载文件失败: {e}")

    def _on_download_finished(self):
        reply = self._download_reply
        self._download_reply = None
        # 关闭文件句柄前,先把 reply 缓冲区里可能残留的最后一块数据读完写入,
        # 防止 finished 触发时尾部字节还未经 readyRead 派发而丢失(成功路径才需要)。
        if self._download_file is not None:
            try:
                if reply is not None and reply.error() == QNetworkReply.NetworkError.NoError:
                    remaining = bytes(reply.readAll())
                    if remaining:
                        self._download_file.write(remaining)
            except OSError as e:
                logger.warning(f"[Updater] 写入下载文件失败: {e}")
            try:
                self._download_file.close()
            except OSError as e:
                logger.warning(f"[Updater] 关闭下载文件失败: {e}")
            self._download_file = None

        if reply is None:
            return
        try:
            err = reply.error()
            if err != QNetworkReply.NetworkError.NoError:
                msg = reply.errorString()
                logger.warning(f"[Updater] 下载失败: {msg}")
                # 删除不完整文件
                self._cleanup_partial()
                self.downloadFailed.emit(msg)
                return
        finally:
            reply.deleteLater()

        path = self._download_path
        if not path or not os.path.isfile(path) or os.path.getsize(path) == 0:
            self._cleanup_partial()
            self.downloadFailed.emit("下载文件无效")
            return
        logger.info(f"[Updater] 下载完成: {path}")
        self.downloadFinished.emit(path)

    def _cleanup_partial(self):
        """删除下载到一半的残留文件。"""
        try:
            if self._download_path and os.path.exists(self._download_path):
                os.remove(self._download_path)
        except OSError as e:
            logger.warning(f"[Updater] 清理下载残留失败: {e}")

    # ==================== 安装 ====================
    @Slot(str, str, result=bool)
    def runInstallerAndQuit(self, installer_path: str, silent_args: str = "") -> bool:
        """启动安装包并在成功后请求退出。Launch installer, then request quit.

        Windows 遵循安装包 manifest 处理 UAC；其他平台使用 QProcess detached。
        文件缺失或启动失败时返回 False，且绝不退出当前应用。
        """
        if not installer_path or not os.path.isfile(installer_path):
            logger.warning(f"[Updater] 安装包不存在: {installer_path}")
            return False
        args = [a for a in silent_args.split(" ") if a] if silent_args else []
        launcher = (
            _launch_windows_installer
            if sys.platform == "win32"
            else _launch_detached_installer
        )
        if not launcher(installer_path, args):
            return False
        logger.info(f"[Updater] 已启动安装包,应用即将退出: {installer_path} {args}")
        QCoreApplication.quit()
        return True

    @Slot(str, result=bool)
    def openInBrowser(self, url: str) -> bool:
        """用系统浏览器打开 URL(检测到新版时跳 Releases 页的兜底)。"""
        if not url:
            return False
        from PySide6.QtGui import QDesktopServices
        return QDesktopServices.openUrl(QUrl(url))
