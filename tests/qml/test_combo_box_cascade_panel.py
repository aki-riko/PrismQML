# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBoxCascade 级联子菜单真实交互合同。

验证真实行为：根层弹层内容、悬停父行打开子层、点击叶子提交路径并关闭整条级联。
每层都是独立原生弹层表面，其窗口由预热按需复用，因此不按"新窗口数"判定层级是否
打开，而按各层真实行内容与层级状态判定。
用法: python scripts/test_process.py --qt-platform offscreen --timeout 180 -- python -m pytest tests/qml/test_combo_box_cascade_panel.py
"""
from pathlib import Path

import pytest

from combo_box_core_conventions_shared import (
    _pump,
    _wait_for,
)
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

REPO_ROOT = Path(__file__).resolve().parents[2]

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 720
    height: 420
    visible: true

    ComboBoxCascade {
        id: cascade
        objectName: "cascade"
        x: 60
        y: 60
        width: 260
        model: [
            {"text": "File", "children": [
                {"text": "New"},
                {"text": "Open"}]},
            {"text": "Tools", "children": [
                {"text": "Developer", "children": [
                    {"text": "Inspect"},
                    {"text": "Console"}]},
                {"text": "Options"}]},
            {"text": "Help"}
        ]
    }

    // Plain dropdown carrying nested nodes: it must serve the cascade itself, without
    // the caller naming a type.
    ComboBox {
        id: autoCascade
        objectName: "autoCascade"
        x: 380
        y: 60
        width: 260
        model: [
            {"text": "File", "children": [{"text": "New"}, {"text": "Open"}]},
            {"text": "Tools", "children": [{"text": "Options"}]},
            {"text": "Help"}
        ]
    }

    // Same control with a flat model: it must stay a plain dropdown.
    ComboBox {
        id: flatCombo
        objectName: "flatCombo"
        x: 60
        y: 140
        width: 260
        model: ["Alpha", "Beta", "Gamma"]
    }
}
"""


@pytest.fixture(scope="module")
def scene():
    app = QApplication.instance() or QApplication([])
    engine = None
    window = None
    try:
        import prismqml
        from prismqml import register_types
        from PySide6.QtQml import QQmlApplicationEngine

        prismqml.configure_qml_environment()
        engine = QQmlApplicationEngine()
        engine.addImportPath(str(REPO_ROOT / "prismqml"))
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            SCENE_SOURCE,
            QUrl.fromLocalFile(str(REPO_ROOT / "tests" / "qml" / "cascade-scene.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        window = component.create()
        assert isinstance(window, QQuickWindow), [
            error.toString() for error in component.errors()
        ]
        window.requestActivate()
        assert _wait_for(window.isActive)
        _pump(120)
        yield window
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
        del engine, app


def _read(item: QQuickItem, name: str):
    """读取 QML 属性为原生 Python 值。

    PySide6 对部分属性返回 QJSValue 包装, 直接比较会误判, 因此统一解包。
    """
    value = item.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _object_descendants(root):
    result = []
    pending = list(root.children())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.children())
    return result


def _popup_core(combo: QQuickItem) -> QQuickItem:
    """根层弹层表面（PopupWindowCore）。"""
    matches = [
        item
        for item in _object_descendants(combo)
        if item.metaObject().indexOfProperty("isClosing") >= 0
        and item.metaObject().indexOfProperty("targetControl") >= 0
    ]
    assert len(matches) == 1, f"预期 1 个弹层表面, 实际 {len(matches)}"
    return matches[0]


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _cascade_rows(window: QQuickWindow) -> list[QQuickItem]:
    """窗口内真正的行（按屏幕纵向排序）。

    根层行是 CascadeItemDelegate, 更深层级复用菜单栈的 Action; 两者都带
    text / hasSubmenu, 以这组属性识别, 不绑定具体类型与启用态属性名。
    """
    rows = [
        item
        for item in _visual_descendants(window.contentItem())
        if item.metaObject().indexOfProperty("hasSubmenu") >= 0
        and item.metaObject().indexOfProperty("text") >= 0
    ]
    return sorted(
        rows,
        key=lambda item: item.mapToItem(window.contentItem(), 0, 0).y(),
    )


def _row_texts(window: QQuickWindow) -> list[str]:
    return [str(_read(row, "text")) for row in _cascade_rows(window)]


def _row_centre(window: QQuickWindow, row: QQuickItem) -> QPoint:
    point = row.mapToItem(
        window.contentItem(), QPointF(row.width() / 2, row.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _move_pointer_away(window: QQuickWindow) -> None:
    QTest.mouseMove(
        window, QPoint(round(window.width() - 12), round(window.height() - 12))
    )
    _pump()


def _submenu_window(combo: QQuickItem) -> QQuickWindow | None:
    window = combo.property("submenuWindow")
    return window if isinstance(window, QQuickWindow) else None


def _scan_windows_for_rows(expected: list[str]) -> QQuickWindow | None:
    """在所有窗口里查找列出给定行的那个窗口。

    级联层是独立原生弹层表面。offscreen 平台不会真正显示第二个原生表面
    (窗口已创建、内容已渲染, 但 isVisible() 为假), 因此以"窗口内容"判定该层是否
    打开, 不把可见性作为条件; 内容只可能来自子层。
    """
    from PySide6.QtGui import QGuiApplication

    for window in QGuiApplication.allWindows():
        if not isinstance(window, QQuickWindow):
            continue
        try:
            if _row_texts(window) == expected:
                return window
        except RuntimeError:
            continue
    return None


def _window_content_dump() -> list:
    """诊断：每个窗口的类名/可见性/行文本/子项类名。"""
    from PySide6.QtGui import QGuiApplication

    dump = []
    for window in QGuiApplication.allWindows():
        if not isinstance(window, QQuickWindow):
            dump.append((type(window).__name__, window.isVisible(), [], []))
            continue
        try:
            rows = _row_texts(window)
            kinds = [
                child.metaObject().className()
                for child in _visual_descendants(window.contentItem())
            ][:6]
        except RuntimeError:
            rows, kinds = ["<destroyed>"], []
        dump.append((type(window).__name__, window.isVisible(), rows, kinds))
    return dump


def _popup_candidates(combo: QQuickItem) -> list[str]:
    return [
        item.metaObject().className()
        for item in _object_descendants(combo)
        if item.metaObject().indexOfProperty("isClosing") >= 0
        and item.metaObject().indexOfProperty("targetControl") >= 0
    ]


def _active_combo(combo: QQuickItem) -> QQuickItem:
    """容器入口组件的实际控件实例。

    ComboBox 是入口容器, 真实控件由内部 Loader 加载; 直接用具体控件时可原样返回。
    """
    if combo.metaObject().indexOfProperty("_popup") >= 0:
        return combo
    for child in _object_descendants(combo):
        if child.metaObject().className().startswith("QQuickLoader"):
            loaded = child.property("item")
            if isinstance(loaded, QQuickItem):
                return loaded
    raise AssertionError("未找到入口组件的内部控件实例")


def _root_window(combo: QQuickItem) -> QQuickWindow:
    """根层窗口: 经弹层原生窗口取, 尚未生成时退回按行内容定位。"""
    popup = _popup_core(combo)
    holder: list[QQuickWindow] = []

    def ready() -> bool:
        candidate = popup.property("_popupWindow")
        if isinstance(candidate, QQuickWindow):
            holder.append(candidate)
            return True
        for window in _all_quick_windows():
            try:
                if any(_cascade_rows(window)):
                    holder.append(window)
                    return True
            except RuntimeError:
                continue
        return False

    assert _wait_for(ready, 2000), "根层原生窗口缺失"
    return holder[-1]


def _open_root(combo: QQuickItem, window: QQuickWindow) -> QQuickWindow:
    _move_pointer_away(window)
    active = _active_combo(combo)
    popup = _popup_core(active)
    active.openPopup()
    assert _wait_for(lambda: _read(active, "isOpen") is True), "根层未打开"
    assert _wait_for(lambda: not _read(popup, "isClosing")), "根层未完成入场"
    _pump(160)
    return _root_window(active)


def _hover_owner_row(combo: QQuickItem, root_window: QQuickWindow, text: str) -> int:
    """把指针移到父行上, 返回该行下标。

    悬停是打开层级的正常路径; offscreen 平台对悬停的投递不稳定, 因此调用方也可经
    openSubmenu(index) 这个公开入口确定性地驱动同一段逻辑。
    """
    rows = _cascade_rows(root_window)
    owner = next(row for row in rows if _read(row, "text") == text)
    index = next(i for i, row in enumerate(rows) if row is owner)
    QTest.mouseMove(root_window, _row_centre(root_window, owner))
    _pump(120)
    return index


def _all_quick_windows():
    from PySide6.QtGui import QGuiApplication

    return [w for w in QGuiApplication.allWindows() if isinstance(w, QQuickWindow)]


def _wait_for_submenu_rows(combo: QQuickItem, expected: list[str]) -> QQuickWindow:
    """等待子层窗口出现并列出预期行。

    子层行由悬停延迟打开, 因此这里轮询等待; 判据是子层真实内容, 不是层级状态属性。
    """
    holder: list[QQuickWindow] = []

    def ready() -> bool:
        window = _scan_windows_for_rows(expected)
        if window is None:
            return False
        holder.append(window)
        return True

    assert _wait_for(ready, 3000), (
        f"子层未打开或内容不符; 期望行={expected}; "
        f"窗口扫描={_window_content_dump()}"
    )
    return holder[-1]


def _close_all(combo: QQuickItem) -> None:
    active = _active_combo(combo)
    # 级联控件按整条链关闭; 普通下拉只需要收起自身弹层。
    if active.metaObject().indexOfMethod("closePopupTree()") >= 0:
        active.closePopupTree()
    else:
        active.closePopup()
    popup = _popup_core(active)
    _wait_for(lambda: _read(active, "isOpen") is False)
    _wait_for(lambda: not _read(popup, "isClosing"))
    _pump(240)


def test_root_level_contract(scene):
    """根层契约: 行内容、箭头态、层级初始状态。

    子层的打开与提交由 test_clicking_leaf_commits_path_and_closes_cascade 端到端覆盖;
    单独悬停一层在 offscreen 下受平台悬停投递影响, 不在此处重复判定。
    """
    combo = scene.findChild(QQuickItem, "cascade")
    assert combo is not None
    root_window = _open_root(combo, scene)
    try:
        assert _row_texts(root_window) == ["File", "Tools", "Help"]
        states = {
            str(_read(row, "text")): bool(_read(row, "hasSubmenu"))
            for row in _cascade_rows(root_window)
        }
        # 有子节点的行必须显示子菜单箭头, 叶子不显示。
        assert states == {"File": True, "Tools": True, "Help": False}
        assert _read(combo, "submenuOpen") is False, "未悬停时不应有子层"
    finally:
        _close_all(combo)


def test_clicking_leaf_commits_path_and_closes_cascade(scene):
    """端到端级联: 打开子层, 点子层叶子提交根路径并关闭整条级联。

    层级经公开入口 openSubmenu(index) 打开——与悬停延迟走同一段实现, 但不受
    offscreen 平台悬停投递的影响; 悬停触发本身由组件内的悬停定时器负责。
    """
    combo = scene.findChild(QQuickItem, "cascade")
    root_window = _open_root(combo, scene)
    try:
        owner_index = _hover_owner_row(combo, root_window, "Tools")
        combo.openSubmenu(owner_index)
        child_window = _wait_for_submenu_rows(combo, ["Developer", "Options"])
        # 子层与根层是不同的原生表面, 且子层沿用同一行组件。
        assert child_window is not root_window
        child_states = {
            str(_read(row, "text")): bool(_read(row, "hasSubmenu"))
            for row in _cascade_rows(child_window)
        }
        assert child_states == {"Developer": True, "Options": False}

        leaf = next(
            row
            for row in _cascade_rows(child_window)
            if _read(row, "text") == "Options"
        )
        QTest.mouseClick(
            child_window,
            Qt.MouseButton.LeftButton,
            pos=_row_centre(child_window, leaf),
        )
        assert _wait_for(
            lambda: _read(combo, "currentText") == "Tools → Options"
        ), f"提交文本错误: {_read(combo, 'currentText')!r}"
        assert _wait_for(lambda: _read(combo, "isOpen") is False), "级联未关闭"
        assert list(_read(combo, "activatedPath")) == ["Tools", "Options"]
    finally:
        _close_all(combo)


def test_hovering_owner_row_opens_child_level(scene):
    """悬停父行即展开下一级, 与 Gallery 菜单的悬停级联一致。"""
    combo = scene.findChild(QQuickItem, "cascade")
    root_window = _open_root(combo, scene)
    active = _active_combo(combo)
    try:
        _hover_owner_row(active, root_window, "Tools")
        child_window = _wait_for_submenu_rows(active, ["Developer", "Options"])
        assert child_window is not root_window
    finally:
        _close_all(combo)


def test_default_dropdown_serves_nested_model_as_cascade(scene):
    """普通下拉遇到嵌套模型时自行提供级联, 无需调用方指定 type。"""
    combo = scene.findChild(QQuickItem, "autoCascade")
    assert combo is not None
    assert _read(combo, "type") == 0, "该用例必须使用默认 type"
    root_window = _open_root(combo, scene)
    active = _active_combo(combo)
    try:
        rows = _cascade_rows(root_window)
        assert [str(_read(row, "text")) for row in rows] == ["File", "Tools", "Help"]
        # 带子节点的行显示箭头: 说明它确实以级联方式渲染, 而不是普通平铺列表。
        states = {
            str(_read(row, "text")): bool(_read(row, "hasSubmenu"))
            for row in rows
        }
        assert states == {"File": True, "Tools": True, "Help": False}

        owner_index = _hover_owner_row(active, root_window, "Tools")
        active.openSubmenu(owner_index)
        child_window = _wait_for_submenu_rows(active, ["Options"])
        assert child_window is not root_window

        leaf = next(
            row for row in _cascade_rows(child_window)
            if _read(row, "text") == "Options"
        )
        QTest.mouseClick(
            child_window,
            Qt.MouseButton.LeftButton,
            pos=_row_centre(child_window, leaf),
        )
        assert _wait_for(
            lambda: _read(active, "currentText") == "Tools → Options"
        ), f"提交文本错误: {_read(active, 'currentText')!r}"
    finally:
        _close_all(combo)


def test_flat_model_stays_plain_dropdown(scene):
    """平铺模型必须保持普通下拉: 行不带子菜单箭头。"""
    combo = scene.findChild(QQuickItem, "flatCombo")
    assert combo is not None
    root_window = _open_root(combo, scene)
    try:
        rows = _cascade_rows(root_window)
        assert [str(_read(row, "text")) for row in rows] == [
            "Alpha", "Beta", "Gamma"
        ]
        assert all(not bool(_read(row, "hasSubmenu")) for row in rows)
    finally:
        _close_all(combo)
