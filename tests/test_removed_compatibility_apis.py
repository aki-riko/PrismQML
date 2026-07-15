# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Pre-1.0 compatibility APIs must stay removed. 旧兼容 API 删除回归。"""

import inspect
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

from prismqml import NavigationItem, Window, getThemeManager


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_direct_child_stack(engine: QQmlEngine):
    source = '''import QtQuick
import PrismQML
StackedWidget {
    width: 320
    height: 200
    lazyLoading: true
    Rectangle { objectName: "page0" }
    Rectangle { objectName: "page1" }
}
'''
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl("inline"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert not component.isError(), [error.toString() for error in component.errors()]
    return component, component.create()


def _is_base_named_source(path: Path) -> bool:
    stem = path.stem
    snake_parts = stem.lower().split("_")
    base_prefix = stem == "Base" or (
        len(stem) > 4 and stem.startswith("Base") and stem[4].isupper()
    )
    return stem.endswith("Base") or base_prefix or "base" in snake_parts


def _is_generated_or_local(path: Path, root: Path) -> bool:
    directories = path.relative_to(root).parts[:-1]
    return any(
        part.startswith(".") or part == "build" or part.startswith("build-")
        for part in directories
    )


def test_documentation_uses_current_core_module_names():
    stale_names = (
        "SettingsBase",
        "IconBase",
        "WindowBase",
        "OverlayDialogBase",
        "ButtonBase",
        "settings_base",
        "icon_base",
        "window_base",
    )
    targets = [Path("AGENTS.md"), Path("README.md"), Path("README.en.md")]
    targets.extend(
        sorted(path.relative_to(ROOT) for path in (ROOT / "docs").rglob("*.md"))
    )

    for target in targets:
        content = _read(target.as_posix())
        for stale_name in stale_names:
            assert stale_name not in content, f"{target}: {stale_name}"


def test_product_sources_do_not_use_base_module_filenames():
    source_suffixes = {".c", ".cpp", ".h", ".hpp", ".js", ".py", ".qml", ".rs"}
    roots = (ROOT / "prismqml", ROOT / "cpp")
    offenders = sorted(
        path.relative_to(ROOT).as_posix()
        for root in roots
        for path in root.rglob("*")
        if path.suffix.lower() in source_suffixes
        and not _is_generated_or_local(path, root)
        and _is_base_named_source(path)
    )
    assert not offenders, offenders


def test_qmldir_does_not_register_base_types():
    offenders = []
    for qmldir in (ROOT / "prismqml").rglob("qmldir"):
        lines = qmldir.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            fields = line.strip().split()
            is_registration = fields and not fields[0].startswith("#")
            if is_registration and fields[0].endswith("Base"):
                offenders.append(
                    f"{qmldir.relative_to(ROOT)}:{line_number}:{fields[0]}"
                )
    assert not offenders, offenders


def test_navigation_item_page_builder_api_is_removed():
    assert "page_builder" not in inspect.signature(NavigationItem).parameters
    assert not hasattr(NavigationItem("Home"), "page_builder")
    assert "page_builder" not in _read("prismqml/python/window/_page_manager.py")


def test_broken_window_user_card_api_is_removed():
    builder = _read("prismqml/python/window/_window_builder.py")
    core = _read("prismqml/python/window/window_core.py")

    assert not hasattr(Window, "setUserCard")
    assert "_user_card" not in core
    assert "userCard:" not in builder
    assert "userCardPosition" not in builder


def test_qml_signal_method_and_property_aliases_are_removed():
    action = _read("prismqml/PrismQML/controls/menus/Action.qml")
    shortcut = _read("prismqml/PrismQML/controls/inputs/ShortcutEditor.qml")
    settings = _read(
        "prismqml/PrismQML/controls/settings/SettingsCard/SettingsCardContent.qml"
    )
    tray = _read("prismqml/PrismQML/controls/menus/SystemTrayMenu.qml")
    check_icon = _read("prismqml/PrismQML/controls/icons/CheckIcon.qml")

    assert "signal clicked()" not in action
    assert "control.clicked()" not in action
    assert "shortcutModified" not in shortcut
    assert "onShortcutModified" not in settings
    assert "onShortcutRecorded" in settings
    assert "function exec(" not in tray
    assert "property bool checked:" not in check_icon


def test_stacked_widget_page_components_mode_is_removed():
    targets = (
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml",
        "prismqml/PrismQML/_internal/WindowsBar.qml",
        "prismqml/PrismQML/_internal/WindowsBarContent.qml",
        "prismqml/PrismQML/_internal/WindowsSplit.qml",
        "prismqml/PrismQML/_internal/WindowsFilled.qml",
        "tests/qml/test_lazy_reload_components.py",
    )

    for target in targets:
        assert "pageComponents" not in _read(target), target
    assert "property var pageSources" in _read(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )


def test_direct_children_do_not_enter_removed_lazy_loader_mode(qapp):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    engine.rootContext().setContextProperty("ThemeManager", getThemeManager())
    component, stack = _create_direct_child_stack(engine)
    assert stack is not None

    stack.setProperty("currentIndex", 1)
    _pump(50)
    expression = QQmlExpression(QQmlEngine.contextForObject(stack), stack, "_displayIndex")
    value = expression.evaluate()
    if isinstance(value, tuple):
        value = value[0]
    assert int(value) == 1
