# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Window Builder - 窗口构建器

负责 QML 窗口的动态构建与字符串拼接。
"""

from pathlib import Path
from string import Template
import hashlib
from PySide6.QtQml import QQmlComponent, QQmlListReference
from PySide6.QtCore import QUrl
from PySide6.QtQuick import QQuickItem
from ..core.logger import debug, warning, exception
from ._generated_qml_cache import (
    GENERATED_WINDOW_QML_CACHE_DIR,
    write_generated_qml,
)
from ._splash_builder import build_splash_properties, build_splash_template_values
from ._window_engine_setup import prepare_window_engine
from ._window_root_setup import finish_window_startup
from ._window_startup import (
    prepare_window_startup_profile,
    resolve_window_qml_paths,
)

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
    splashEnabled: ${splash_enabled}
    splashIcon: "${splash_icon}"
    splashTitle: "${splash_title}"
    splashSubtitle: "${splash_subtitle}"
    startupProfilingVerbose: ${startup_profiling_verbose}
    lazyLoading: false
    _pythonPageMode: true
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

    def _profile_generated_window_qml(
        self, window_qml_file: Path, qml_component: str
    ) -> None:
        try:
            qml_bytes = window_qml_file.read_bytes()
            qml_digest = hashlib.sha256(qml_bytes).hexdigest()[:20]
            debug(
                "[启动剖析] PrismQML._create_window generated qml: "
                f"path={window_qml_file}, bytes={len(qml_bytes)}, "
                f"sha={qml_digest}, component={qml_component}, "
                f"nav={len(self._nav_items)}, bottom={len(self._bottom_nav_items)}, "
                f"pages={len(self._nav_items) + len(self._bottom_nav_items)}, "
                "verbose=True"
            )
        except OSError as exc:
            warning(f"[启动剖析] 读取生成窗口 QML 失败: {exc}")
        debug("[启动剖析] PrismQML._create_window QQmlComponent(file) begin")

    @staticmethod
    def _profile_window_component_result(component, loaded_window) -> None:
        debug(
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
                debug("[启动剖析] PrismQML._create_window component.create(file) begin")
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

    def _build_navigation_items_data(self) -> list[dict]:
        """Build top navigation data for initial-property injection. 构建顶部导航初始属性数据。"""
        return [
            {
                "text": item.text,
                "icon": self._resolve_icon_path(item.icon),
            }
            for item in self._nav_items
        ]

    def _build_bottom_items_data(self) -> list[dict]:
        """Build bottom navigation data for initial-property injection. 构建底部导航初始属性数据。"""
        nav_count = len(self._nav_items)
        return [
            {
                "text": item.text,
                "icon": self._resolve_icon_path(item.icon),
                "key": f"page_{nav_count + index}",
                "selectable": bool(getattr(item, "selectable", True)),
            }
            for index, item in enumerate(self._bottom_nav_items)
        ]

    def _build_initial_window_properties(
        self,
        window_icon_qml: str,
        startup_profile_verbose: bool,
        mica_enabled: bool,
    ) -> dict:
        """Build runtime root properties without changing static QML source. 构建不改变静态 QML 源码的根属性。"""
        return {
            "objectName": "mainWindow",
            "width": self._width,
            "height": self._height,
            "visible": False,
            "windowTitle": self._title,
            "windowIcon": window_icon_qml,
            "windowIconColored": self._icon_colored,
            "startupProfilingVerbose": startup_profile_verbose,
            "lazyLoading": False,
            "_pythonPageMode": True,
            "micaEnabled": mica_enabled,
            "navigationItems": self._build_navigation_items_data(),
            "bottomNavigationItems": self._build_bottom_items_data(),
            **build_splash_properties(self),
        }

    def _append_static_page_containers(self, loaded_window) -> None:
        """Append lightweight Python-owned containers through the root default property. 通过根默认属性追加轻量 Python 页面容器。"""
        pages = QQmlListReference(loaded_window, "pages")
        if not pages.isValid() or not pages.canAppend():
            raise RuntimeError("Static window root does not expose appendable pages")

        page_count = len(self._nav_items) + len(self._bottom_nav_items)
        for index in range(page_count):
            page = QQuickItem(loaded_window.contentItem())
            page.setObjectName(f"page_{index}")
            if not pages.append(page):
                page.deleteLater()
                raise RuntimeError(f"Failed to append static page container page_{index}")

    def _load_static_window_component(
        self, qml_dir: Path, qml_component: str, profile, verbose: bool
    ):
        """Compile the stable packaged root component. 编译稳定的包内根组件。"""
        root_qml_file = qml_dir / "_internal" / f"{qml_component}.qml"
        if verbose:
            debug(
                "[启动剖析] PrismQML._create_window static qml: "
                f"path={root_qml_file}, component={qml_component}, "
                f"nav={len(self._nav_items)}, bottom={len(self._bottom_nav_items)}, "
                "verbose=True"
            )
        component = QQmlComponent(
            self._engine, QUrl.fromLocalFile(str(root_qml_file))
        )
        profile("QQmlComponent(static)")
        if component.isError():
            warning(
                "[WindowBuilder] 静态窗口 QML 加载失败，回退动态根: "
                f"{[error.toString() for error in component.errors()]}"
            )
            return None
        return component

    def _create_static_window_root(
        self,
        component,
        window_icon_qml: str,
        mica_enabled: bool,
        profile,
        verbose: bool,
    ):
        """Create the static root and append page containers. 创建静态根并追加页面容器。"""
        initial_properties = self._build_initial_window_properties(
            window_icon_qml,
            verbose,
            mica_enabled,
        )
        loaded_window = component.createWithInitialProperties(
            initial_properties,
            self._engine.rootContext(),
        )
        profile("component.createWithInitialProperties(static)")
        if loaded_window is None:
            warning(
                "[WindowBuilder] 静态窗口 QML 创建失败，回退动态根: "
                f"{[error.toString() for error in component.errors()]}"
            )
            return None
        self._append_static_page_containers(loaded_window)
        profile("创建静态根页面容器")
        return loaded_window

    def _load_static_window_boundary(
        self,
        qml_dir: Path,
        qml_component: str,
        window_icon_qml: str,
        mica_enabled: bool,
        profile,
        verbose: bool,
    ):
        """Load the stable packaged root and inject runtime data at creation. 加载稳定包内根组件并在创建时注入运行态数据。"""
        loaded_window = None
        try:
            component = self._load_static_window_component(
                qml_dir, qml_component, profile, verbose
            )
            if component is None:
                return None
            loaded_window = self._create_static_window_root(
                component,
                window_icon_qml,
                mica_enabled,
                profile,
                verbose,
            )
            if loaded_window is None:
                return None
            self._window_component = component
            if verbose:
                debug(
                    "[启动剖析] PrismQML._create_window static result: "
                    f"loaded=True, errors={[error.toString() for error in component.errors()]}"
                )
            return loaded_window
        except Exception as exc:
            if loaded_window is not None:
                loaded_window.deleteLater()
            exception(
                "[WindowBuilder] 静态窗口根加载失败，回退动态根: "
                f"{type(exc).__name__}: {exc}"
            )
            return None

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
            **build_splash_template_values(self, esc),
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
        return qml_dir, window_qml, qml_component, window_icon_qml, mica_enabled

    def _create_window(self):
        """创建QML窗口"""
        profile, startup_profile_verbose = prepare_window_startup_profile()
        getConfigManager = prepare_window_engine(
            self, startup_profile_verbose, profile
        )
        qml_dir, icon_dir = resolve_window_qml_paths(profile)
        rendered_window = self._compose_window_qml(
            qml_dir,
            icon_dir,
            startup_profile_verbose,
            getConfigManager,
            profile,
        )
        finish_window_startup(
            self,
            rendered_window,
            profile,
            startup_profile_verbose,
        )

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
