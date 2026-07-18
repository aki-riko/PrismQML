# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Public generated icon behavior contracts. 生成图标的公开行为合同。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from prismqml import getThemeManager
from prismqml.python.core.icons import Icon


ROOT = Path(__file__).resolve().parents[1]
RECOVERED_ICON_VALUES = (
    "BulletedList",
    "FitPage",
    "Hide",
    "Message",
    "NavigateForward",
    "OpenFile",
    "OpenFolderHorizontal",
    "PowerButton",
    "StickyNotes",
    "Update",
    "View",
    "Volume",
    "Zoom",
)
ICON_PROBE_SOURCE = """import QtQuick
import PrismQML
QtObject {
    property string addValue: Enums.icon.add
    property string addAliasValue: Enums.icons.add
    property string addPath: Enums.icon.path(Enums.icon.add)
    property string basePath: Enums.icon.basePath
    property string addMapped: Enums.icon.iconList.ADD
    property string addCalled: Enums.icon("ADD")
    property var unknownValue: Enums.icon.not_a_real_icon
    property string unknownCalled: Enums.icon("NOT_A_REAL_ICON")
    property int iconCount: Object.keys(Enums.icon.iconList).length
    property string allIconValues: Object.keys(Enums.icon.iconList).map(function(enumName) {
        return Enums.icon.iconList[enumName]
    }).join("|")
    property string exceptionalIcons: [
        Enums.icon.i_o_s_arrow,
        Enums.icon.i_o_s_arrow_l_t_r,
        Enums.icon.i_o_s_arrow_r_t_l,
        Enums.icon.i_o_s_chevron_right,
        Enums.icon.multiplier1_2x,
        Enums.icon.multiplier1_5x,
        Enums.icon.multiplier1_8x,
        Enums.icon.multiplier_5x
    ].join("|")
    property string reservedIcons: [
        Enums.icon.icon_class,
        Enums.icon.icon_delete,
        Enums.icon.icon_new,
        Enums.icon.icon_print
    ].join("|")
    property string recoveredIcons: [
        Enums.icon.bulleted_list,
        Enums.icon.fit_page,
        Enums.icon.hide,
        Enums.icon.message,
        Enums.icon.navigate_forward,
        Enums.icon.open_file,
        Enums.icon.open_folder_horizontal,
        Enums.icon.power_button,
        Enums.icon.sticky_notes,
        Enums.icon.update,
        Enums.icon.view,
        Enums.icon.volume,
        Enums.icon.zoom
    ].join("|")
}
"""


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_icon_probe() -> tuple[QQmlEngine, QQmlComponent, object]:
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    engine.rootContext().setContextProperty("ThemeManager", getThemeManager())
    component = QQmlComponent(engine)
    component.setData(
        ICON_PROBE_SOURCE.encode("utf-8"), QUrl("inline:icon-contract.qml")
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert not component.isError(), [error.toString() for error in component.errors()]
    return engine, component, component.create()


def test_python_icon_enum_keeps_public_helpers(qapp):
    assert str(Icon.ADD) == "Add"
    assert Icon.get_all() == [icon.value for icon in Icon]
    assert Icon.get_all_enum_names() == [icon.name for icon in Icon]
    assert Path(Icon.ADD.path()).is_file()
    assert not Icon.ADD.to_qicon().isNull()
    assert not Icon.ADD.to_qicon("#123456").isNull()
    assert tuple(icon.value for icon in Icon if icon.value in RECOVERED_ICON_VALUES) == (
        RECOVERED_ICON_VALUES
    )


def test_svg_python_and_qml_registry_sets_match(qapp):
    svg_dir = ROOT / "prismqml/PrismQML/controls/icons/fluent"
    svg_values = {path.stem for path in svg_dir.glob("*.svg")}
    keep = _create_icon_probe()
    probe = keep[-1]
    assert probe is not None
    assert svg_values == {icon.value for icon in Icon}
    assert svg_values == set(probe.property("allIconValues").split("|"))


def test_qml_icon_singleton_matches_python_registry(qapp):
    keep = _create_icon_probe()
    probe = keep[-1]
    assert probe is not None
    assert probe.property("addValue") == "Add"
    assert probe.property("addAliasValue") == "Add"
    assert probe.property("addPath") == "fluent/Add.svg"
    assert probe.property("basePath") == "fluent/"
    assert probe.property("addMapped") == "Add"
    assert probe.property("addCalled") == "Add.svg"
    assert probe.property("unknownValue") is None
    assert probe.property("unknownCalled") == ""
    assert probe.property("iconCount") == len(Icon)
    assert probe.property("exceptionalIcons") == (
        "iOSArrow|iOSArrowLTR|iOSArrowRTL|iOSChevronRight|"
        "Multiplier1_2x|Multiplier1_5x|Multiplier1_8x|Multiplier_5x"
    )
    assert probe.property("reservedIcons") == "Class|Delete|New|Print"
    assert probe.property("recoveredIcons") == "|".join(RECOVERED_ICON_VALUES)
