# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""PrismQML Window Builder - 窗口构建器

负责 QML 窗口的动态构建与字符串拼接。
"""

from typing import List, Optional, TYPE_CHECKING
from pathlib import Path
import hashlib
import os
import time
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtCore import QTimer, QMetaObject, Q_ARG, QUrl, QStandardPaths
from ..core.logger import warning, info, error, debug
from ..core.engine import EngineManager
from ..providers import get_svg_provider

if TYPE_CHECKING:
    from .window_base import NavigationItem

class WindowBuilderMixin:
    """窗口构建器 Mixin，提供 _create_window 等方法"""

    _GENERATED_QML_CACHE_DIR = Path.home() / ".prismqml" / "qml_cache" / "generated_windows"
    _GENERATED_SPLASH_QML_CACHE_DIR = Path.home() / ".prismqml" / "qml_cache" / "generated_splash"

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
        source_bytes = source.encode("utf-8")
        digest = hashlib.sha256(source_bytes).hexdigest()[:20]
        qml_file = cls._GENERATED_QML_CACHE_DIR / f"window_{digest}.qml"

        cls._GENERATED_QML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if qml_file.exists():
            try:
                if qml_file.read_bytes() == source_bytes:
                    return qml_file
            except OSError:
                pass

        qml_file.write_bytes(source_bytes)
        return qml_file

    @classmethod
    def _write_generated_splash_qml(cls, source: str) -> Path:
        """Write generated splash QML to a stable file so Qt can disk-cache it."""
        source_bytes = source.encode("utf-8")
        digest = hashlib.sha256(source_bytes).hexdigest()[:20]
        qml_file = cls._GENERATED_SPLASH_QML_CACHE_DIR / f"splash_{digest}.qml"

        cls._GENERATED_SPLASH_QML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if qml_file.exists():
            try:
                if qml_file.read_bytes() == source_bytes:
                    return qml_file
            except OSError:
                pass

        qml_file.write_bytes(source_bytes)
        return qml_file

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

        def icon_path(name: str) -> str:
            return self._resolve_icon_path(name)

        # 构建导航项
        esc = self._escape_qml
        nav_items_qml = ", ".join(
            [
                f'{{ "text": "{esc(item.text)}", "icon": "{esc(icon_path(item.icon))}" }}'
                for item in self._nav_items
            ]
        )

        # Bottom items: all items get key, selectable controls page switching
        # 底部项：所有项都有key，selectable控制是否切换页面
        bottom_items_qml = ", ".join(
            [
                f'{{ "text": "{esc(item.text)}", "icon": "{esc(icon_path(item.icon))}", "key": "page_{len(self._nav_items) + i}", "selectable": {"true" if getattr(item, "selectable", True) else "false"} }}'
                for i, item in enumerate(self._bottom_nav_items)
            ]
        )

        # 生成用户卡片QML
        user_card_qml = ""
        if self._user_card:
            avatar = self._user_card.get("avatar", "")
            title = self._user_card.get("title", "")
            subtitle = self._user_card.get("subtitle", "")
            position = self._user_card.get("position", "bottom")
            # 如果avatar是图标名，转换为路径
            if avatar and not (
                "/" in avatar or "\\" in avatar or avatar.startswith("image://")
            ):
                avatar = icon_path(avatar)
            # Windows路径转换为QML格式（正斜杠 + file:///前缀）
            if avatar and ("\\" in avatar or (len(avatar) > 1 and avatar[1] == ":")):
                avatar = "file:///" + avatar.replace("\\", "/")
            user_card_qml = f'''
    userCard: {{ "avatar": "{esc(avatar)}", "title": "{esc(title)}", "subtitle": "{esc(subtitle)}" }}
    userCardPosition: "{esc(position)}"'''

        # 页面容器由Python动态创建，作为窗口默认子元素会自动放入StackedWidget
        # StackedWidget会自动管理可见性和动画
        # All items get page containers (function items just have empty containers)
        # 所有项都创建页面容器（功能项的容器为空）
        # 注意：必须显式绑定宽高到父容器，StackedWidget的Component.onCompleted
        # 只在初始化时执行，无法处理后续动态添加的子项
        page_items = []
        for i in range(len(self._nav_items) + len(self._bottom_nav_items)):
            page_items.append(f"""
        Item {{
            id: page_{i}
            objectName: "page_{i}"
            width: parent ? parent.width : 0
            height: parent ? parent.height : 0
            Component.onCompleted: window.profileDetail("generated page container page_{i} completed parent=" + parent)
            onParentChanged: window.profileDetail("generated page container page_{i} parentChanged parent=" + parent)
        }}""")

        pages_qml = "\n".join(page_items) if page_items else ""
        profile("生成导航/页面 QML 数据")

        # 根据window_type选择QML组件
        from .window_base import _WINDOW_TYPE_QML_NAMES
        qml_component = _WINDOW_TYPE_QML_NAMES.get(self._window_type, "WindowsBar")
        window_icon_qml = icon_path(self._icon) if self._icon else f"file:///{icon_dir.as_posix()}/Apps.svg"
        mica_enabled = bool(self._pending_props.get("micaEnabled", getConfigManager().micaEnabled))

        # 生成窗口QML
        window_qml = f"""import QtQuick
import "file:///{qml_dir.as_posix()}"
import "file:///{qml_dir.as_posix()}/_internal"

{qml_component} {{
    id: window
    objectName: "mainWindow"
    width: {self._width}
    height: {self._height}
    windowTitle: "{esc(self._title)}"
    windowIcon: "{esc(window_icon_qml)}"
    windowIconColored: {'true' if self._icon_colored else 'false'}
    startupProfilingVerbose: {'true' if startup_profile_verbose else 'false'}
    lazyLoading: false
    micaEnabled: {'true' if mica_enabled else 'false'}
    
    navigationItems: [{nav_items_qml}]
    bottomNavigationItems: [{bottom_items_qml}]
{user_card_qml}
    // Python动态填充的页面容器（绑定到stack.currentIndex控制可见性）
{pages_qml}
    
    onCurrentPageChanged: (index) => {{
    }}
}}
"""
        profile("拼接窗口 QML")

        loaded_window = None
        try:
            window_qml_file = self._write_generated_window_qml(window_qml)
            profile("写入/确认窗口 QML 缓存")
            if startup_profile_verbose:
                try:
                    qml_bytes = window_qml_file.read_bytes()
                    qml_digest = hashlib.sha256(qml_bytes).hexdigest()[:20]
                    info(
                        "[启动剖析] PrismQML._create_window generated qml: "
                        f"path={window_qml_file}, bytes={len(qml_bytes)}, "
                        f"sha={qml_digest}, component={qml_component}, "
                        f"nav={len(self._nav_items)}, bottom={len(self._bottom_nav_items)}, "
                        f"pages={len(self._nav_items) + len(self._bottom_nav_items)}, "
                        f"verbose={startup_profile_verbose}"
                    )
                except OSError as exc:
                    warning(f"[启动剖析] 读取生成窗口 QML 失败: {exc}")
                info("[启动剖析] PrismQML._create_window QQmlComponent(file) begin")
            component = QQmlComponent(self._engine, QUrl.fromLocalFile(str(window_qml_file)))
            profile("QQmlComponent(file)")
            if component.isError():
                warning(f"[WindowBuilder] 文件化窗口 QML 加载失败: {[e.toString() for e in component.errors()]}")
            else:
                if startup_profile_verbose:
                    info("[启动剖析] PrismQML._create_window component.create(file) begin")
                loaded_window = component.create()
                self._window_component = component
                profile("component.create(file)")
                if startup_profile_verbose:
                    info(
                        "[启动剖析] PrismQML._create_window component.create(file) result: "
                        f"loaded={loaded_window is not None}, errors={[e.toString() for e in component.errors()]}"
                    )
        except Exception as e:
            warning(f"[WindowBuilder] 文件化加载窗口 QML 失败，回退到 loadData: {e}")

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
        if not self._splash_enabled or self._window is None:
            return

        try:
            profile_start = time.perf_counter()
            profile_last = profile_start

            def profile(label: str):
                nonlocal profile_last
                now = time.perf_counter()
                info(
                    f"[启动剖析] PrismQML._create_splash {label}: "
                    f"+{int((now - profile_last) * 1000)}ms / "
                    f"total {int((now - profile_start) * 1000)}ms"
                )
                profile_last = now

            from ..core.utils import qml_path
            esc = self._escape_qml
            profile("导入/准备")

            # 图标/标题默认回退到窗口自身配置
            icon = self._splash_icon or self._icon
            icon_url = self._resolve_icon_path(icon) if icon else ""
            title = self._splash_title or self._title or ""
            subtitle = self._splash_subtitle or ""

            qml_dir = qml_path()
            splash_qml = f"""import QtQuick
import "file:///{qml_dir.as_posix()}"

Rectangle {{
    id: splash

    property string iconSource: "{esc(icon_url)}"
    property string title: "{esc(title)}"
    property string subtitle: "{esc(subtitle)}"
    property string activeIconSource: ""
    property bool startupProfilingVerbose: PrismQmlStartupProfileVerbose

    signal finished()

    anchors.fill: parent
    z: Enums.zIndex.tooltip
    color: Enums.backgroundColor
    opacity: 1
    visible: true

    function finish() {{
        fadeOutAnim.start()
    }}

    NumberAnimation {{
        id: fadeOutAnim
        target: splash
        property: "opacity"
        to: 0
        duration: Enums.duration.medium
        easing.type: Easing.InCubic
        onFinished: {{
            splash.visible = false
            splash.finished()
        }}
    }}

    Timer {{
        id: splashContentTimer
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            contentLoader.active = true
            if (splash.startupProfilingVerbose) {{
                console.info("[启动剖析] Splash content Loader activated")
            }}
        }}
    }}

    Timer {{
        id: splashIconTimer
        interval: 0
        running: false
        repeat: false
        onTriggered: {{
            splash.activeIconSource = splash.iconSource
            if (splash.startupProfilingVerbose) {{
                console.info("[启动剖析] Splash icon source activated")
            }}
        }}
    }}

    Loader {{
        id: contentLoader
        anchors.fill: parent
        active: false
        sourceComponent: splashContentComponent

        onLoaded: {{
            if (splash.iconSource !== "") {{
                splashIconTimer.start()
            }}
            if (splash.startupProfilingVerbose) {{
                console.info("[启动剖析] Splash content Loader loaded")
            }}
        }}
    }}

    Component {{
        id: splashContentComponent

        Column {{
            anchors.centerIn: parent
            spacing: Enums.spacing.xl

            Image {{
                anchors.horizontalCenter: parent.horizontalCenter
                width: 102
                height: 102
                source: splash.activeIconSource
                sourceSize: Qt.size(102, 102)
                asynchronous: true
                cache: true
                smooth: true
                mipmap: true
                fillMode: Image.PreserveAspectFit
                visible: splash.activeIconSource !== ""
            }}

            Text {{
                anchors.horizontalCenter: parent.horizontalCenter
                text: splash.title
                visible: text !== ""
                color: Enums.textColor.primary
                font.family: Enums.fontFamily
                font.pixelSize: 20
                font.bold: true
            }}

            Text {{
                anchors.horizontalCenter: parent.horizontalCenter
                text: splash.subtitle
                visible: text !== ""
                color: Enums.textColor.secondary
                font.family: Enums.fontFamily
                font.pixelSize: 13
            }}
        }}
    }}
}}
"""
            profile("拼接 Splash QML")
            startup_profile_verbose = os.environ.get("PRISMQML_STARTUP_PROFILE_VERBOSE", "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            component = None
            component_source = "file"
            try:
                splash_qml_file = self._write_generated_splash_qml(splash_qml)
                profile("写入/确认 Splash QML 缓存")
                if startup_profile_verbose:
                    try:
                        qml_bytes = splash_qml_file.read_bytes()
                        qml_digest = hashlib.sha256(qml_bytes).hexdigest()[:20]
                        info(
                            "[启动剖析] PrismQML._create_splash generated qml: "
                            f"path={splash_qml_file}, bytes={len(qml_bytes)}, sha={qml_digest}, "
                            f"iconSet={bool(icon_url)}, titleSet={bool(title)}, subtitleSet={bool(subtitle)}"
                        )
                    except OSError as exc:
                        warning(f"[启动剖析] 读取生成 Splash QML 失败: {exc}")
                    info("[启动剖析] PrismQML._create_splash QQmlComponent(file) begin")
                component = QQmlComponent(self._engine, QUrl.fromLocalFile(str(splash_qml_file)))
                profile("QQmlComponent(file)")
                if component.isError():
                    warning(f"[Splash] 文件化组件加载失败: {[e.toString() for e in component.errors()]}")
                    component = None
            except Exception as e:
                warning(f"[Splash] 文件化加载失败，回退到 inline: {e}")

            if component is None:
                component_source = "inline"
                component = QQmlComponent(self._engine)
                component.setData(splash_qml.encode("utf-8"), QUrl("inline-splash"))
                profile("component.setData fallback")
            if component.isError():
                warning(f"[Splash] 组件加载失败: {[e.toString() for e in component.errors()]}")
                return

            splash = component.create()
            profile(f"component.create({component_source})")
            if splash is None:
                warning("[Splash] create() 返回 None,跳过启动画面")
                return

            # 挂到窗口 contentItem 作为顶层覆盖层(SplashScreen 内部 anchors.fill)
            splash.setParentItem(self._window.contentItem())
            splash.setProperty("width", self._window.width())
            splash.setProperty("height", self._window.height())
            # QML 端 _dismissSplashWhenReady 读这个引用,首屏就绪时自动 finish()
            self._window.setProperty("_splashInstance", splash)
            profile("挂载到窗口")
            # 持引用防 GC(QQmlComponent.create 的所有权在调用方)
            self._splash_instance = splash
            self._splash_component = component
            debug("[Splash] 启动画面已挂载,等待首屏就绪后自动淡出")
        except Exception as e:
            warning(f"[Splash] 创建启动画面失败(不影响启动): {e}")

    def _build_nav_items_json(self, items: List['NavigationItem']) -> str:
        """构建导航项JSON"""
        esc = self._escape_qml
        return ", ".join(
            [f'{{"text": "{esc(item.text)}", "icon": "{esc(item.icon)}"}}' for item in items]
        )
