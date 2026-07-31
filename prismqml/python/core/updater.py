# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""通用应用更新组件 - 基于 GitHub Releases 的检测 / 下载 / 安装启动。

典型用法(应用层)::

    from prismqml import Updater

    updater = Updater("owner/repo", "v1.0.3", asset_keyword="Setup")
    ctx.setContextProperty("Updater", updater)
    # QML 侧:Updater.checkForUpdate() / 接 updateAvailable 信号 / downloadUpdate(url)
    #          / runInstallerAndQuit(path, "/VERYSILENT")

所有网络操作均异步,通过信号回传结果;不阻塞 GUI 线程。
"""

import os
import sys
from typing import BinaryIO, Optional

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    QCoreApplication,
    QUrl,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

from ._updater_download import (
    commit_download_file,
    discard_completed_download,
    open_unique_download_file,
    verify_download_digest,
    write_download_bytes,
)
from ._updater_release import (
    _is_newer,
    _parse_version,
    decode_release_payload,
    is_safe_update_url,
    is_sha256_digest,
    pick_asset as _pick_asset,
)
from .logger import getLogger

logger = getLogger()

# GitHub API 要求带 User-Agent,否则返回 403。
_USER_AGENT = b"PrismQML-Updater"
_UPDATER_API_BASE_ENV = "PRISMQML_UPDATER_API_BASE_URL"
_DEFAULT_API_BASE_URL = "https://api.github.com"
_CONNECTION_CACHE_EXPIRY_SECONDS = 0
_INSTALL_STRATEGIES = frozenset(("in_place", "dual_slot"))


def _validate_install_strategy(value: str) -> str:
    if value not in _INSTALL_STRATEGIES:
        raise ValueError("install_strategy must be 'in_place' or 'dual_slot'")
    return value


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


def _network_request(url: str) -> QNetworkRequest:
    """Build one updater request with bounded connection lifetime. 构造连接寿命受控的更新请求。"""
    request = QNetworkRequest(QUrl(url))
    request.setRawHeader(b"User-Agent", _USER_AGENT)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    # GitHub 关闭空闲 HTTP/2 连接时，Qt 可能在关闭回调中读取已关闭的
    # QSslSocket；不缓存更新器连接可避免该 Qt 生命周期竞态。
    request.setAttribute(
        QNetworkRequest.Attribute.ConnectionCacheExpiryTimeoutSecondsAttribute,
        _CONNECTION_CACHE_EXPIRY_SECONDS,
    )
    return request


class Updater(QObject):
    """基于 GitHub Releases 的应用更新器。

    检测最新 release、比对版本、异步下载安装包、启动平台安装程序。
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
    downloadProgress = Signal("qint64", "qint64")  # (received, total)
    downloadFinished = Signal(str)                  # (localPath)
    downloadFailed = Signal(str)                    # (errorMessage)
    installPreparationFinished = Signal()
    installPreparationFailed = Signal(str)

    def __init__(
        self,
        repo: str,
        current_version: str,
        asset_keyword: str = "Setup",
        parent: Optional[QObject] = None,
        *,
        api_base_url: Optional[str] = None,
        install_strategy: str = "in_place",
    ):
        super().__init__(parent)
        self._repo = repo
        self._current_version = current_version
        self._asset_keyword = asset_keyword
        self._api_base_url = _resolve_api_base_url(api_base_url)
        self._nam = QNetworkAccessManager(self)
        self._check_reply: Optional[QNetworkReply] = None
        self._download_reply: Optional[QNetworkReply] = None
        self._download_file: Optional[BinaryIO] = None
        self._download_partial_path = ""
        self._download_path = ""
        self._download_error = ""
        self._expected_digest = ""
        self._expected_download_url = ""
        self._require_artifact_digest = True
        self._install_strategy = _validate_install_strategy(install_strategy)
        self._slot_preparation = self._create_slot_preparation()

    def _create_slot_preparation(self):
        if self._install_strategy != "dual_slot":
            return None
        from .update_slots import SlotUpdatePreparation

        preparation = SlotUpdatePreparation(self)
        preparation.finished.connect(self.installPreparationFinished)
        preparation.failed.connect(self.installPreparationFailed)
        return preparation

    @property
    def api_base_url(self) -> str:
        """Resolved API base URL. 已解析的更新 API 根地址。"""
        return self._api_base_url

    @Property(str, constant=True)
    def repository(self) -> str:
        """Repository identifier exposed to QML. 暴露给 QML 的仓库标识。"""
        return self._repo
    @Property(str, constant=True)
    def currentVersion(self) -> str:
        """Current version exposed to QML. 暴露给 QML 的当前版本。"""
        return self._current_version
    @Property(bool, constant=True)
    def requireArtifactDigest(self) -> bool:
        """Whether release assets must carry SHA-256. 是否要求资产带 SHA-256。"""
        return self._require_artifact_digest

    @Property(str, constant=True)
    def installStrategy(self) -> str:
        """Selected installer strategy. 当前安装策略。"""
        return self._install_strategy
    def set_require_artifact_digest(self, value: bool) -> None:
        """Set the policy from trusted Python code, not from QML. 仅允许可信 Python 入口设置策略。"""
        self._require_artifact_digest = bool(value)
    # ==================== 检测 ====================
    @Slot()
    def checkForUpdate(self):
        """异步请求 GitHub latest release,完成后发 updateAvailable / upToDate / checkFailed。"""
        if self._check_reply is not None or self._download_reply is not None:
            self.checkFailed.emit("更新检查已在进行")
            return
        self._expected_digest = ""
        self._expected_download_url = ""
        url = _latest_release_url(self._repo, self._api_base_url)
        if not is_safe_update_url(url):
            self.checkFailed.emit("更新 API 地址不安全")
            return
        req = _network_request(url)
        req.setRawHeader(b"Accept", b"application/vnd.github+json")
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
        try:
            data = decode_release_payload(raw)
        except (ValueError, UnicodeDecodeError) as e:
            logger.warning(f"[Updater] 解析 release JSON 失败: {e}")
            self.checkFailed.emit("解析更新信息失败")
            return

        self._handle_release_data(data)

    def _handle_release_data(self, data: dict):
        """Emit one validated release result. 发出一个已校验的 release 结果。"""
        tag = data["tag_name"]
        if not _is_newer(tag, self._current_version):
            self._expected_digest = ""
            self._expected_download_url = ""
            logger.debug(f"[Updater] 已是最新版本 {self._current_version}")
            self.upToDate.emit(self._current_version)
            return
        asset = _pick_asset(data["assets"], self._asset_keyword)
        download_url = asset["browser_download_url"] if asset else ""
        digest = asset.get("digest", "") if asset else ""
        if asset and not is_safe_update_url(download_url):
            self.checkFailed.emit("更新资产下载地址不安全")
            return
        if asset and self._require_artifact_digest and not is_sha256_digest(digest):
            self.checkFailed.emit("更新资产缺少有效 SHA-256 摘要")
            return
        self._expected_digest = digest
        self._expected_download_url = download_url
        logger.info(f"[Updater] 发现新版本 {tag}(当前 {self._current_version})")
        self.updateAvailable.emit(tag, data["body"], download_url, data["html_url"])

    def _inject_release_for_test(self, raw: bytes):
        """测试专用:直接喂入 release JSON 字节,走与网络回调相同的解析路径。"""
        self._process_release_data(raw)

    # ==================== 下载 ====================
    @Slot(str)
    def downloadUpdate(self, url: str):
        """异步下载安装包，并通过 progress/finished/failed 信号报告结果。"""
        if self._check_reply is not None or self._download_reply is not None:
            message = "更新检查已在进行" if self._check_reply is not None else "下载已在进行"
            self.downloadFailed.emit(message)
            return
        error = self._validate_download_url(url)
        if error:
            self.downloadFailed.emit(error)
            return
        try:
            (
                self._download_file,
                self._download_partial_path,
                self._download_path,
            ) = open_unique_download_file(url)
        except OSError as e:
            logger.exception(f"[Updater] 创建下载文件失败: {e}")
            self.downloadFailed.emit(f"创建下载文件失败: {e}")
            return

        self._download_error = ""
        try:
            self._download_reply = self._start_download_request(url)
        except (KeyboardInterrupt, SystemExit):
            self._cleanup_partial()
            raise
        except Exception as e:
            logger.exception(f"[Updater] 创建下载请求失败: {e}")
            self._fail_download(f"创建下载请求失败: {e}")

    def _validate_download_url(self, url: str) -> str:
        """Validate URL and release digest binding. 校验地址及摘要绑定。"""
        if not url:
            return "下载地址为空"
        if not is_safe_update_url(url):
            return "下载地址不安全"
        if url != self._expected_download_url:
            self._expected_digest = ""
        if self._require_artifact_digest and not is_sha256_digest(self._expected_digest):
            return "下载地址未绑定有效 SHA-256 摘要"
        return ""

    def _start_download_request(self, url: str):
        """Create and wire one download reply. 创建并连接单个下载响应。"""
        request = _network_request(url)
        reply = self._nam.get(request)
        reply.downloadProgress.connect(self._on_download_progress)
        reply.readyRead.connect(lambda reply=reply: self._on_download_ready_read(reply))
        reply.finished.connect(lambda reply=reply: self._on_download_finished(reply))
        return reply

    def _on_download_progress(self, received: int, total: int):
        self.downloadProgress.emit(int(received), int(total))

    def _on_download_ready_read(self, reply=None):
        # 边收边写,避免大文件全部驻留内存。
        if reply is not self._download_reply or self._download_file is None:
            return
        payload = bytes(reply.readAll())
        if not payload or self._download_error:
            return
        try:
            write_download_bytes(self._download_file, payload)
        except (KeyboardInterrupt, SystemExit):
            self._abort_download_reply(reply)
            raise
        except OSError as e:
            self._download_error = f"写入下载文件失败: {e}"
            logger.exception(f"[Updater] {self._download_error}")
            self._abort_failed_download(reply)

    def _on_download_finished(self, reply=None):
        if reply is not self._download_reply:
            if reply is not None:
                reply.deleteLater()
            return
        self._download_reply = None
        if reply is None:
            self._fail_download("下载响应无效")
            return
        try:
            error_message = self._finalize_download(reply)
        except (KeyboardInterrupt, SystemExit):
            self._cleanup_partial()
            raise
        finally:
            reply.deleteLater()
        if error_message:
            self._fail_download(error_message)
            return
        path = self._download_path
        logger.info(f"[Updater] 下载完成: {path}")
        self.downloadFinished.emit(path)

    def _finalize_download(self, reply) -> str:
        """Write the tail and commit, returning an error message. 完成下载提交。"""
        if self._download_error:
            return self._download_error
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return reply.errorString()
        try:
            remaining = bytes(reply.readAll())
            if remaining:
                write_download_bytes(self._download_file, remaining)
            commit_download_file(
                self._download_file,
                self._download_partial_path,
                self._download_path,
            )
            self._download_file = None
        except OSError as e:
            logger.exception(f"[Updater] 提交下载文件失败: {e}")
            return f"提交下载文件失败: {e}"
        if not os.path.isfile(self._download_path) or os.path.getsize(self._download_path) == 0:
            return "下载文件无效"
        if self._expected_digest and not verify_download_digest(
            self._download_path, self._expected_digest
        ):
            return "下载文件摘要校验失败"
        self._download_partial_path = ""
        return ""

    def _abort_download_reply(self, reply):
        """Abort one reply while preserving an active exception. 中止下载响应。"""
        self._download_reply = None
        try:
            reply.abort()
        except Exception as e:
            logger.exception(f"[Updater] 中止下载响应失败: {e}")
        finally:
            reply.deleteLater()
            self._cleanup_partial()

    def _abort_failed_download(self, reply):
        """Abort after ordinary I/O failure. 在普通 I/O 失败后中止响应。"""
        try:
            reply.abort()
        except Exception as e:
            logger.exception(f"[Updater] 中止失败下载响应失败: {e}")
            self._download_reply = None
            reply.deleteLater()
            self._fail_download(self._download_error)

    def _fail_download(self, message: str):
        """Abort the active file transaction and emit one failure. 中止下载事务。"""
        self._cleanup_partial()
        self._download_error = ""
        self.downloadFailed.emit(message)

    def _cleanup_partial(self):
        """Close and remove partial/final transaction files. 清理下载事务文件。"""
        handle, self._download_file = self._download_file, None
        if handle is not None:
            try:
                handle.close()
            except OSError as e:
                logger.exception(f"[Updater] 关闭下载残留失败: {e}")
        for path in (self._download_partial_path, self._download_path):
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                logger.exception(f"[Updater] 清理下载残留失败: {e}")
        self._download_partial_path = ""

    # ==================== 安装 ====================
    @Slot(str, str, result=bool)
    def runInstallerAndQuit(self, installer_path: str, silent_args: str = "") -> bool:
        """启动安装包并在成功后请求退出。Launch installer, then request quit.

        Windows 遵循安装包 manifest 处理 UAC；macOS/Linux 使用平台安装处理器。
        文件缺失或启动失败时返回 False，且绝不退出当前应用。
        """
        if not installer_path or not os.path.isfile(installer_path):
            logger.warning(f"[Updater] 安装包不存在: {installer_path}")
            return False
        from ._updater_install import (
            launch_non_windows_installer,
            launch_windows_installer,
        )

        args = [a for a in silent_args.split(" ") if a] if silent_args else []
        launcher = (
            launch_windows_installer
            if sys.platform == "win32"
            else launch_non_windows_installer
        )
        if not launcher(installer_path, args):
            self._download_path = discard_completed_download(
                installer_path, self._download_path
            )
            return False
        logger.info(f"[Updater] 已启动安装包,应用即将退出: {installer_path} {args}")
        QCoreApplication.quit()
        return True

    @Slot(str, str, result=bool)
    def stageInstallerForNextLaunch(
        self, installer_path: str, silent_args: str = ""
    ) -> bool:
        """Install into the inactive Windows slot without closing this process."""
        if self._install_strategy != "dual_slot":
            logger.warning("[Updater] 当前更新器未启用 Windows 双槽策略")
            return False
        if self._slot_preparation is None:
            logger.error("[Updater] Windows 双槽准备器未初始化")
            return False
        if not self._slot_preparation.stage(installer_path, silent_args):
            self._download_path = discard_completed_download(
                installer_path, self._download_path
            )
            return False
        return True

    @Slot(str, result=bool)
    def openInBrowser(self, url: str) -> bool:
        """用系统浏览器打开 URL(检测到新版时跳 Releases 页的兜底)。"""
        if not is_safe_update_url(url, allow_local_http=False):
            return False
        from PySide6.QtGui import QDesktopServices
        return QDesktopServices.openUrl(QUrl(url))
