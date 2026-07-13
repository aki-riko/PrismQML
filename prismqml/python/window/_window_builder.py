# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Window Builder - 窗口构建器

负责 QML 窗口的动态构建与字符串拼接。
"""

from typing import List, TYPE_CHECKING
from pathlib import Path
from string import Template
import hashlib
import os
import time
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtCore import QUrl, QStandardPaths
from ..core.logger import warning, info, exception
from ..core.engine import EngineManager
from ..providers import get_svg_provider
from ._generated_qml_cache import (
    GENERATED_SPLASH_QML_CACHE_DIR,
    GENERATED_WINDOW_QML_CACHE_DIR,
    write_generated_qml,
)
from ._splash_builder import create_splash

if TYPE_CHECKING:
    from .window_core import NavigationItem


_WINDOW_QML_TEMPLATE = Template(
    """import QtQuick
import "file:///${qml_dir}"
import "file:///${qml_dir}/_internal"

${qml_component} {
    id: window
    objectName: "mainWindow"
    width: ${width}
    height: ${height}
    // Python WindowCore calls show() after pending state and splash are mounted.
    visible: false
    windowTitle: "${window_title}"
    windowIcon: "${window_icon}"
    windowIconColored: ${window_icon_colored}
    startupProfilingVerbose: ${startup_profiling_verbose}
    lazyLoading: false
    micaEnabled: ${mica_enabled}
$indent
    navigationItems: [${nav_items}]
    bottomNavigationItems: [${bottom_items}]

    // Python动态填充的页面容器（绑定到stack.currentIndex控制可见性）
${pages}
$indent
    onCurrentPageChanged: (index) => {
    }
}
"""
)


class WindowBuilderMixin:
    """窗口构建器 Mixin，提供 _create_window 等方法"""

    _GENERATED_QML_CACHE_DIR = GENERATED_WINDOW_QML_CACHE_DIR
    _GENERATED_SPLASH_QML_CACHE_DIR = GENERATED_SPLASH_QML_CACHE_DIR

    @staticmethod
    def _escape_qml(text: str) -> str:
        """转义 QML 字符串中的特殊字符，防止注入

        安全说明：此函数仅用于转义用户传入的字符串值（如标题、文本标签），
        不可用于 QML 模板代码片段——花括号转义会破坏 QML 语法。

        Args:
            text: 原始字符串

        Returns:
            转义后的安全字符串
        """
        # 反斜杠必须最先替换，避免二次转义
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "\\r")
        text = text.replace("\t", "\\t")
        # 花括号在 QML 中有语义（对象字面量 / JavaScript 代码块），需要 Unicode 转义
        text = text.replace("{", "\\u007B")
        text = text.replace("}", "\\u007D")
        return text

    @classmethod
    def _write_generated_window_qml(cls, source: str) -> Path:
        """Write generated root-window QML to a stable file for Qt's file cache path."""
        return write_generated_qml(
            source,
            cls._GENERATED_QML_CACHE_DIR,
            "window",
            "[WindowBuilder]",
        )

    @classmethod
    def _write_generated_splash_qml(cls, source: str) -> Path:
        """Write generated splash QML to a stable file so Qt can disk-cache it."""
        return write_generated_qml(
            source,
            cls._GENERATED_SPLASH_QML_CACHE_DIR,
            "splash",
            "[Splash]",
        )

    def _profile_generated_window_qml(
        self, window_qml_file: Path, qml_component: str
    ) -> None:
        try:
            qml_bytes = window_qml_file.read_bytes()
            qml_digest = hashlib.sha256(qml_bytes).hexdigest()[:20]
            info(
                "[启动剖析] PrismQML._create_window generated qml: "
                f"path={window_qml_file}, bytes={len(qml_bytes)}, "
                f"sha={qml_digest}, component={qml_component}, "
                f"nav={len(self._nav_items)}, bottom={len(self._bottom_nav_items)}, "
                f"pages={len(self._nav_items) + len(self._bottom_nav_items)}, "
                "verbose=True"
            )
        except OSError as exc:
            warning(f"[启动剖析] 读取生成窗口 QML 失败: {exc}")
        info("[启动剖析] PrismQML._create_window QQmlComponent(file) begin")

    @staticmethod
    def _profile_window_component_result(component, loaded_window) -> None:
        info(
            "[启动剖析] PrismQML._create_window component.create(file) result: "
            f"loaded={loaded_window is not None}, "
            f"errors={[error.toString() for error in component.errors()]}"
        )

    def _load_generated_window_component(
        self, window_qml: str, qml_component: str, profile, verbose: bool
    ):
        window_qml_file = self._write_generated_window_qml(window_qml)
        profile("写入/确认窗口 QML 缓存")
        if verbose:
            self._profile_generated_window_qml(window_qml_file, qml_component)
        component = QQmlComponent(
            self._engine, QUrl.fromLocalFile(str(window_qml_file))
        )
        profile("QQmlComponent(file)")
        if component.isError():
            warning(
                "[WindowBuilder] 文件化窗口 QML 加载失败: "
                f"{[error.toString() for error in component.errors()]}"
            )
            return None
        return component

    def _load_generated_window_boundary(
        self, window_qml: str, qml_component: str, profile, verbose: bool
    ):
        loaded_window = None
        try:
            component = self._load_generated_window_component(
                window_qml, qml_component, profile, verbose
            )
            if component is None:
                return None
            if verbose:
                info("[启动剖析] PrismQML._create_window component.create(file) begin")
            loaded_window = component.create()
            self._window_component = component
            profile("component.create(file)")
            if verbose:
                self._profile_window_component_result(component, loaded_window)
        except Exception as exc:
            outcome = (
                "文件化加载窗口 QML 失败，回退到 loadData"
                if loaded_window is None
                else "文件化窗口 QML 创建后诊断失败，保留已创建窗口"
            )
            exception(
                f"[WindowBuilder] {outcome}: {type(exc).__name__}: {exc}"
            )
        return loaded_window

    def _render_navigation_items_qml(self) -> str:
        """Render top navigation item data. 渲染顶部导航项数据。"""
        esc = self._escape_qml
        return ", ".join(
            [
                f'{{ "text": "{esc(item.text)}", "icon": "{esc(self._resolve_icon_path(item.icon))}" }}'
                for item in self._nav_items
            ]
        )

    def _render_bottom_items_qml(self) -> str:
        """Render keyed bottom items with selectable routing. 渲染带 key 的底部项。"""
        esc = self._escape_qml
        nav_count = len(self._nav_items)
        return ", ".join(
            [
                f'{{ "text": "{esc(item.text)}", "icon": "{esc(self._resolve_icon_path(item.icon))}", "key": "page_{nav_count + i}", "selectable": {"true" if getattr(item, "selectable", True) else "false"} }}'
                for i, item in enumerate(self._bottom_nav_items)
            ]
        )

    def _render_page_containers_qml(self) -> str:
        """Render bound containers for every navigation item. 渲染全部绑定容器。"""
        page_count = len(self._nav_items) + len(self._bottom_nav_items)
        return "\n".join(
            [
                f"""
        Item {{
            id: page_{i}
            objectName: "page_{i}"
            width: parent ? parent.width : 0
            height: parent ? parent.height : 0
            Component.onCompleted: window.profileDetail("generated page container page_{i} completed parent=" + parent)
            onParentChanged: window.profileDetail("generated page container page_{i} parentChanged parent=" + parent)
        }}"""
                for i in range(page_count)
            ]
        )

    def _render_window_qml(
        self,
        qml_dir: Path,
        qml_component: str,
        window_icon_qml: str,
        startup_profile_verbose: bool,
        mica_enabled: bool,
        nav_items_qml: str,
        bottom_items_qml: str,
        pages_qml: str,
    ) -> str:
        """Render the generated root-window QML. 渲染生成的根窗口 QML。"""
        esc = self._escape_qml
        return _WINDOW_QML_TEMPLATE.substitute(
            qml_dir=qml_dir.as_posix(),
            qml_component=qml_component,
            width=self._width,
            height=self._height,
            window_title=esc(self._title),
            window_icon=esc(window_icon_qml),
            window_icon_colored="true" if self._icon_colored else "false",
            startup_profiling_verbose="true" if startup_profile_verbose else "false",
            mica_enabled="true" if mica_enabled else "false",
            nav_items=nav_items_qml,
            bottom_items=bottom_items_qml,
            pages=pages_qml,
            indent="    ",
        )

    def _resolve_window_qml_state(self, icon_dir: Path, get_config_manager):
        """Resolve root component, icon, and Mica state. 解析根窗口状态。"""
        from .window_core import _WINDOW_TYPE_QML_NAMES

        qml_component = _WINDOW_TYPE_QML_NAMES.get(self._window_type, "WindowsBar")
        window_icon_qml = (
            self._resolve_icon_path(self._icon)
            if self._icon
            else f"file:///{icon_dir.as_posix()}/Apps.svg"
        )
        mica_enabled = bool(
            self._pending_props.get("micaEnabled", get_config_manager().micaEnabled)
        )
        return qml_component, window_icon_qml, mica_enabled

    def _compose_window_qml(
        self,
        qml_dir: Path,
        icon_dir: Path,
        startup_profile_verbose: bool,
        get_config_manager,
        profile,
    ):
        """Compose generated window QML in the original order. 按原顺序组合窗口 QML。"""
        nav_items_qml = self._render_navigation_items_qml()
        bottom_items_qml = self._render_bottom_items_qml()
        pages_qml = self._render_page_containers_qml()
        profile("生成导航/页面 QML 数据")
        qml_component, window_icon_qml, mica_enabled = (
            self._resolve_window_qml_state(icon_dir, get_config_manager)
        )
        window_qml = self._render_window_qml(
            qml_dir,
            qml_component,
            window_icon_qml,
            startup_profile_verbose,
            mica_enabled,
            nav_items_qml,
            bottom_items_qml,
            pages_qml,
        )
        profile("拼接窗口 QML")
        return window_qml, qml_component, window_icon_qml, mica_enabled

    def _create_window(self):
        """创建QML窗口"""
        profile_start = time.perf_counter()
        profile_last = profile_start

        def profile(label: str):
            nonlocal profile_last
            now = time.perf_counter()
            info(
                f"[启动剖析] PrismQML._create_window {label}: "
                f"+{int((now - profile_last) * 1000)}ms / "
                f"total {int((now - profile_start) * 1000)}ms"
            )
            profile_last = now

        startup_profile_verbose = os.environ.get("PRISMQML_STARTUP_PROFILE_VERBOSE", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if startup_profile_verbose:
            cache_location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
            info(
                "[启动剖析] PrismQML QML cache env: "
                f"QML_DISK_CACHE_PATH={os.environ.get('QML_DISK_CACHE_PATH', '')!r}, "
                f"QML_DISABLE_DISK_CACHE={os.environ.get('QML_DISABLE_DISK_CACHE', '')!r}, "
                f"QML_FORCE_DISK_CACHE={os.environ.get('QML_FORCE_DISK_CACHE', '')!r}, "
                f"QtCacheLocation={cache_location!r}"
            )

        from ..core import ThemeManager, getShadowManager
        from ..config import getConfigManager
        profile("导入核心管理器")

        # 获取或创建引擎
        try:
            self._engine = EngineManager.get_engine()
        except RuntimeError:
            # 引擎未初始化，创建新引擎
            self._engine = QQmlApplicationEngine()
            EngineManager.set_engine(self._engine)
        profile("获取/创建 QML Engine")

        # 注入管理器
        from .mica_window import get_mica_manager
        from .native_window import get_native_window_hook
        from ..providers.clipboard import get_clipboard_helper
        from ..core.icon_provider import register_icon_provider
        profile("导入窗口依赖")

        ctx = self._engine.rootContext()
        ctx.setContextProperty("ThemeManager", ThemeManager())
        ctx.setContextProperty("ShadowManager", getShadowManager())
        ctx.setContextProperty("ConfigManager", getConfigManager())
        ctx.setContextProperty("MicaManager", get_mica_manager())
        ctx.setContextProperty("ClipboardHelper", get_clipboard_helper())
        ctx.setContextProperty("PrismQmlStartupProfileVerbose", startup_profile_verbose)
        # WindowCore 延后调用 NativeWindow.attach/finalizeAttach，让 frameless 享受 DWM 动画
        ctx.setContextProperty("NativeWindow", get_native_window_hook())
        profile("注入 ContextProperty")

        # 注册Icon到QML（Python作为单一来源）
        register_icon_provider(self._engine)

        # 注册SVG图片提供器（高质量SVG渲染）
        self._engine.addImageProvider("svg", get_svg_provider())
        profile("注册 ImageProvider")

        from ..core.utils import qml_path
        qml_dir = qml_path()
        icon_dir = qml_dir / "controls" / "icons" / "fluent"
        profile("解析 QML 路径")

        window_qml, qml_component, window_icon_qml, mica_enabled = (
            self._compose_window_qml(
                qml_dir,
                icon_dir,
                startup_profile_verbose,
                getConfigManager,
                profile,
            )
        )

        # Isolate file fallback now; full window orchestration split remains P7I-F.
        # 先隔离文件回退边界；完整窗口编排拆分仍留在 P7I-F。
        loaded_window = self._load_generated_window_boundary(
            window_qml,
            qml_component,
            profile,
            startup_profile_verbose,
        )

        if loaded_window is None:
            self._engine.loadData(window_qml.encode("utf-8"))
            profile("engine.loadData fallback")
            if self._engine.rootObjects():
                loaded_window = self._engine.rootObjects()[-1]

        if loaded_window is None:
            raise RuntimeError("Failed to create window")

        self._window = loaded_window
        profile("获取 rootObject")

        # 找到内容区域（StackedWidget）
        self._find_content_area()
        profile("查找 content area")

        # 连接信号
        self._connect_signals()
        profile("连接 QML 信号")

        # ⚠️ apply 子类 __init__ 期间缓存的 setProperty (Mica 等),
        # 这一步必须在 nativeHookReady (50ms 后) 之前完成,否则 hookReady 读到默认值
        def same_icon(left: str, right: str) -> bool:
            def canonical(value: str) -> str:
                if value.startswith("qrc:"):
                    return ":/" + value[4:].lstrip("/")
                return value

            return canonical(str(left)) == canonical(str(right))

        initial_props = {
            "windowTitle": self._title,
            "windowIcon": window_icon_qml,
            "windowIconColored": self._icon_colored,
            "micaEnabled": mica_enabled,
        }
        for key, initial_value in initial_props.items():
            if key not in self._pending_props:
                continue
            pending_value = self._pending_props[key]
            if key == "windowIcon":
                is_same = same_icon(pending_value, initial_value)
            else:
                is_same = pending_value == initial_value
            if is_same:
                self._pending_props.pop(key, None)

        if self._pending_props or self._pending_calls:
            info(
                "[启动剖析] PrismQML._create_window pending state: "
                f"props={list(self._pending_props.keys())}, calls={len(self._pending_calls)}"
            )
        self._apply_pending_state()
        profile("应用 pending state")

        # 默认挂载启动画面: 在窗口树就绪后立即创建 SplashScreen 覆盖层,
        # 框架首屏内容加载完成时会自动 finish() 淡出。必须在框架的异步
        # mainLoader(startupTimer 50ms 后才 active)之前挂好 _splashInstance,
        # 此处同步执行 → onLoaded 时 _splashInstance 必已就位。
        self._create_splash()
        profile("创建 Splash")

    def _resolve_icon_path(self, name: str) -> str:
        """把图标名/路径解析为 QML 可用的 url。

        从 _create_window 内的闭包提取为实例方法,供窗口图标 / 用户卡片 /
        启动画面共用同一套解析规则。
        """
        if not name:
            return ""

        # 支持内置协议
        if name.startswith(("qrc:/", "file:///", "http://", "https://")):
            return name

        # Qt 简写协议
        if name.startswith(":/"):
            return "qrc" + name

        # 本地绝对路径
        if "\\" in name or (len(name) > 1 and name[1] == ":") or name.startswith("/"):
            path_str = name.replace("\\", "/")
            return f"file:///{path_str.lstrip('/')}"

        # 内置图标回退
        from ..core.utils import qml_path
        icon_dir = qml_path() / "controls" / "icons" / "fluent"
        return f"file:///{(icon_dir / f'{name}.svg').as_posix()}"

    def _create_splash(self):
        """创建启动画面并挂到 QML 根对象的 _splashInstance。

        框架 (NavigationWindowCore._dismissSplashWhenReady) 会在首屏内容
        真正加载完成时自动调 _splashInstance.finish() 淡出,无需 Python 干预。
        _splash_enabled=False 时跳过。

        失败不致命: splash 仅是视觉增强,任何异常只 warning 并继续启动。
        """
        create_splash(self)

    def _build_nav_items_json(self, items: List['NavigationItem']) -> str:
        """构建导航项JSON"""
        esc = self._escape_qml
        return ", ".join(
            [f'{{"text": "{esc(item.text)}", "icon": "{esc(item.icon)}"}}' for item in items]
        )
