# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Headless 全组件加载 probe — 重排验证工具

遍历根 qmldir 注册的全部公开组件,逐个 createComponent 实例化；singleton
通过 QtObject wrapper 强制引擎创建并读取。默认模式下，必须由父组件注入
required property 的内部子模块会被归类为预期跳过；--full-required 模式会
使用真实依赖 wrapper 创建这些模块，使 Skin 专项覆盖可以达到全部注册项。

用法: python scripts/test_process.py --qt-platform offscreen --timeout 180 -- python tests/qml/probe_all_components.py
退出码: 0=无非预期错误, 1=有非预期加载错误
"""
import argparse
import importlib
import importlib.util
import os
import re
import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

# Force the automated probe headless and suppress native crash dialogs.
# 强制自动化探测无界面运行，并禁止原生崩溃弹窗。
configure_qml_test_process()

from PySide6.QtCore import (
    QEventLoop,
    QTimer,
    QUrl,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPONENT_LOAD_TIMEOUT_MS = 10_000

EXPECTED_REQUIRED_PROPERTY_SKIPS = {
    "ButtonContent": "ButtonCore 内部内容区, required 属性由 ButtonCore 注入",
    "ButtonDropdown": "ButtonCore 内部分裂/下拉区, required 属性由 ButtonCore 注入",
    "ButtonProgress": "ButtonCore 内部进度层, required 属性由 ButtonCore 注入",
    "ListWidgetItem": "ListWidget delegate, itemData/itemIndex 由 ListWidget 注入",
    "SettingsCardContent": "SettingsCard 内部内容区, type 由 SettingsCard 注入",
    "HorizontalScrollMixin": "Mixin 附着组件, target 由宿主组件注入",
    "ViewportMixin": "Mixin 附着组件, target 由宿主组件注入",
}

REQUIRED_PROPERTY_PROBES = {
    "ButtonContent": """
import QtQuick
import PrismQML
ButtonContent {
    feature: Enums.button.feature_standard
    style: Enums.button.style_default
    text: "TICKET"
    icon: ""
    iconSize: Enums.iconSize.medium
    loading: false
    loadingText: ""
    progress: 0
    textColor: Enums.foregroundColor
    fontSize: Enums.typography.body
}
""",
    "ButtonDropdown": """
import QtQuick
import PrismQML
ButtonDropdown {
    isToolButton: false
    feature: Enums.button.feature_standard
    menuItems: []
    menu: null
    controlEnabled: true
    loading: false
    showDropdownIndicator: false
    dropdownOpen: false
    parentRadius: Enums.surfaceRadius(Enums.radius.small)
    fontSize: Enums.typography.body
    textColor: Enums.foregroundColor
}
""",
    "ButtonProgress": """
import QtQuick
import PrismQML
ButtonProgress {
    feature: Enums.button.feature_standard
    style: Enums.button.style_default
    progress: 0
    showProgress: false
}
""",
    "ListWidgetItem": """
import QtQuick
import PrismQML
ListWidgetItem {
    itemIndex: 0
    itemData: ({})
}
""",
    "SettingsCardContent": """
import QtQuick
import PrismQML
SettingsCardContent {
    type: Enums.settingsCard.type_default
}
""",
    "HorizontalScrollMixin": """
import QtQuick
import PrismQML
Item {
    Flickable { id: targetItem; width: 100; height: 100 }
    HorizontalScrollMixin { target: targetItem }
}
""",
    "ViewportMixin": """
import QtQuick
import PrismQML
Item {
    Item { id: targetItem; width: 100; height: 100 }
    ViewportMixin { target: targetItem }
}
""",
}


def parse_args():
    """解析 probe 运行来源。"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installed",
        action="store_true",
        help="从当前解释器已安装的 prismqml 包探测 QML 组件",
    )
    parser.add_argument(
        "--skin",
        choices=("fluent", "neobrutalism", "vintage_ticket"),
        help="创建组件前设置指定 Skin",
    )
    parser.add_argument(
        "--theme",
        choices=("light", "dark"),
        help="创建组件前设置指定明暗主题",
    )
    parser.add_argument(
        "--full-required",
        action="store_true",
        help="使用依赖 wrapper 创建全部 required-property 内部模块",
    )
    return parser.parse_args()


def resolve_package_root(installed: bool) -> Path:
    """返回包含 PrismQML 模块目录的 Python 包根。"""
    if not installed:
        return Path(__file__).resolve().parents[2] / "prismqml"

    spec = importlib.util.find_spec("prismqml")
    locations = spec.submodule_search_locations if spec else None
    if not locations:
        raise ModuleNotFoundError("当前解释器未安装 prismqml 包")
    package_root = Path(next(iter(locations))).resolve()
    source_root = (REPO_ROOT / "prismqml").resolve()
    if package_root == source_root:
        raise RuntimeError("--installed 被源码树遮蔽，未验证已安装 prismqml 包")
    return package_root


def load_runtime_setup(package_root: Path):
    """从被探测包加载真实 QML 环境与注册入口。"""
    sys.path.insert(0, str(package_root.parent))
    package = importlib.import_module("prismqml")
    imported_root = Path(package.__file__).resolve().parent
    if imported_root != package_root.resolve():
        raise RuntimeError(
            f"PrismQML Python/QML 根不一致: {imported_root} != {package_root}"
        )
    return package


def configure_probe_font_directory() -> None:
    """在 Windows offscreen 下使用系统字体目录。"""
    if os.name != "nt" or os.environ.get("QT_QPA_FONTDIR"):
        return
    windows_root = os.environ.get("WINDIR")
    if not windows_root:
        return
    font_directory = Path(windows_root) / "Fonts"
    if font_directory.is_dir():
        os.environ["QT_QPA_FONTDIR"] = str(font_directory)


def parse_qmldir(path: Path):
    """解析 qmldir,返回 [(typeName, is_singleton), ...]"""
    types = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("module"):
            continue
        m = re.match(r"^(singleton\s+)?([A-Z]\w*)\s+(\S+\.qml)$", line)
        if m:
            types.append((m.group(2), bool(m.group(1))))
    return types


def is_expected_required_property_skip(type_name: str, errors: list[str]) -> bool:
    """判断是否为已知 required property 内部子模块跳过项。"""
    if type_name not in EXPECTED_REQUIRED_PROPERTY_SKIPS:
        return False

    for error in errors:
        detail = error
        if detail.startswith("create() 返回 None:"):
            detail = detail.split(":", 1)[1]
        parts = [part.strip() for part in detail.split(";") if part.strip()]
        if not parts:
            return False
        for part in parts:
            if (
                "Required property " not in part
                or " was not initialized" not in part
            ):
                return False
    return True


def wait_for_component(component: QQmlComponent) -> bool:
    """等待异步 QML 类型依赖加载完成。"""
    if component.status() != QQmlComponent.Status.Loading:
        return True

    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    component.statusChanged.connect(loop.quit)
    timer.start(COMPONENT_LOAD_TIMEOUT_MS)
    while component.status() == QQmlComponent.Status.Loading and timer.isActive():
        loop.exec()
    return component.status() != QQmlComponent.Status.Loading


def create_probe_object(engine: QQmlEngine, type_name: str, qml: str):
    """编译并创建一个探测 wrapper。"""
    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl(f"inline:{type_name}"))
    if not wait_for_component(comp):
        return comp, None, [f"QML component 加载超时: {COMPONENT_LOAD_TIMEOUT_MS}ms"]
    if comp.isError():
        return comp, None, [error.toString() for error in comp.errors()]

    obj = comp.create()
    if obj is None:
        details = "; ".join(error.toString() for error in comp.errors())
        return comp, None, [f"create() 返回 None: {details}"]
    return comp, obj, []


def probe_component(
    engine: QQmlEngine,
    type_name: str,
    full_required: bool = False,
):
    """创建单个普通组件并返回成功状态与错误。"""
    qml = (
        REQUIRED_PROPERTY_PROBES[type_name]
        if full_required and type_name in REQUIRED_PROPERTY_PROBES
        else f"import PrismQML\n{type_name} {{}}\n"
    )
    component, obj, errors = create_probe_object(engine, type_name, qml)
    if obj is None:
        return False, errors
    obj.deleteLater()
    del component
    return True, []


def probe_singleton(engine: QQmlEngine, type_name: str):
    """通过 wrapper 强制创建并读取单例对象。"""
    qml = (
        "import QtQml\n"
        "import PrismQML\n"
        f"QtObject {{ readonly property bool singletonReady: !!{type_name} }}\n"
    )
    component, obj, errors = create_probe_object(engine, type_name, qml)
    if obj is None:
        return False, errors
    ready = bool(obj.property("singletonReady"))
    obj.deleteLater()
    del component
    if not ready:
        return False, ["singleton wrapper 未取得真实对象"]
    return True, []


def make_qt_message_handler(messages: list[str]):
    """创建会收集 warning 及更高等级消息的 Qt handler。"""
    failure_types = {
        QtMsgType.QtWarningMsg,
        QtMsgType.QtCriticalMsg,
        QtMsgType.QtFatalMsg,
    }

    def handle_message(message_type, context, message):
        if message_type not in failure_types:
            return
        location = f"{context.file}:{context.line}: " if context.file else ""
        messages.append(f"{message_type.name}: {location}{message}")

    return handle_message


def flush_qt_events() -> None:
    """运行一轮事件循环以收集 singleton 完成期消息。"""
    loop = QEventLoop()
    QTimer.singleShot(0, loop.quit)
    loop.exec()


def collect_singleton_results(engine: QQmlEngine, types):
    """创建所有 singleton 并收集其 Qt 运行时消息。"""
    errors = {}
    ok = 0
    singleton_messages = []
    previous_handler = qInstallMessageHandler(
        make_qt_message_handler(singleton_messages)
    )
    try:
        for type_name, is_singleton in types:
            if not is_singleton:
                continue
            passed, type_errors = probe_singleton(engine, type_name)
            if passed:
                ok += 1
            else:
                errors[type_name] = type_errors
        flush_qt_events()
    finally:
        qInstallMessageHandler(previous_handler)

    if singleton_messages:
        errors["Singleton Qt runtime"] = singleton_messages
    return ok, errors


def collect_results(engine: QQmlEngine, types, full_required: bool = False):
    """收集组件创建、预期跳过和真实错误。"""
    ok, errors = collect_singleton_results(engine, types)
    expected_required_skips = {}

    for type_name, is_singleton in types:
        if is_singleton:
            continue
        passed, type_errors = probe_component(engine, type_name, full_required)
        if passed:
            ok += 1
        elif is_expected_required_property_skip(type_name, type_errors):
            expected_required_skips[type_name] = type_errors
        else:
            errors[type_name] = type_errors
    return ok, errors, expected_required_skips


def report_results(ok, errors, expected_required_skips, total):
    """输出 probe 汇总与错误详情。"""
    total_skips = len(expected_required_skips)
    print(f"\n{'='*60}")
    print(f"组件加载 probe 结果: {ok} OK / {len(errors)} 错误 / "
          f"{total_skips} 跳过 "
          f"(required {len(expected_required_skips)}) "
          f"(共 {total})")
    print(f"{'='*60}")
    if expected_required_skips:
        print("\n[预期 required property 跳过]")
        for name in sorted(expected_required_skips):
            print(f"    {name}: {EXPECTED_REQUIRED_PROPERTY_SKIPS[name]}")
    if errors:
        for name, errs in sorted(errors.items()):
            print(f"\n[错误] {name}:")
            for e in errs:
                print(f"    {e}")


def main():
    """运行源码树或安装包的全组件 probe。"""
    args = parse_args()
    package_root = resolve_package_root(args.installed)
    package = load_runtime_setup(package_root)
    qmldir = package_root / "PrismQML" / "qmldir"
    if not qmldir.is_file():
        raise FileNotFoundError(f"找不到 QML 模块注册文件: {qmldir}")

    package.configure_qml_environment()
    configure_probe_font_directory()
    app = QApplication([sys.argv[0]])
    if args.skin:
        package.setSkin(package.Skin(args.skin))
    if args.theme:
        package.setTheme(package.Theme(args.theme))
    engine = QQmlEngine()
    package.register_types(engine)
    engine.addImportPath(str(package_root))
    types = parse_qmldir(qmldir)
    results = collect_results(engine, types, args.full_required)
    QTimer.singleShot(0, app.quit)
    app.exec()
    report_results(*results, len(types))
    return 1 if results[1] else 0


if __name__ == "__main__":
    raise SystemExit(main())
