# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TableWidget architecture gates. TableWidget 架构门禁。"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TABLE_WIDGET = (
    REPO_ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Table"
    / "TableWidget.qml"
)
DATA_CONTROLLER = TABLE_WIDGET.parent / "_internal" / "TableDataController.js"
TABLE_CONTENT = TABLE_WIDGET.parent / "_internal" / "TableWidgetContent.qml"
DATA_METHODS = {
    "_isPureJsArray",
    "addRow",
    "clearData",
    "removeRow",
    "getRow",
    "setRowCount",
    "setColumnCount",
    "setHorizontalHeaderLabels",
    "setItem",
    "item",
    "selectedItems",
    "sortItems",
    "setData",
    "setCellWidget",
    "cellWidget",
    "hasCellWidget",
}


def test_table_data_operations_are_delegated_without_qml_objects():
    entry_source = TABLE_WIDGET.read_text(encoding="utf-8")
    controller_source = DATA_CONTROLLER.read_text(encoding="utf-8")

    assert '.pragma library' in controller_source
    assert 'import "_internal/TableDataController.js" as TableDataController' in entry_source
    assert "TableInternal.TableDataController" not in entry_source
    for method in DATA_METHODS:
        assert f"function {method}(" in controller_source
        assert f"TableDataController.{method}(" in entry_source


def test_table_widget_modules_stay_within_architecture_limit():
    for path in (TABLE_WIDGET, DATA_CONTROLLER):
        assert len(path.read_text(encoding="utf-8").splitlines()) < 500


def test_table_widget_keeps_visual_content_modularized():
    entry_source = TABLE_WIDGET.read_text(encoding="utf-8")
    content_source = TABLE_CONTENT.read_text(encoding="utf-8")

    assert len(entry_source.splitlines()) < 400
    assert TABLE_CONTENT.exists()
    assert len(content_source.splitlines()) < 200
    assert 'import "_internal" as TableInternal' in entry_source
    assert "TableInternal.TableWidgetContent {" in entry_source
    assert "required property var table" in content_source
    assert "property alias paintedRowComponent: paintedRowComponent" in content_source
    assert "property alias contentDelegate: contentDelegateComponent" in content_source
    assert "property alias headerContent: headerContentComponent" in content_source
    assert "property alias defaultTableContextMenuLoader: defaultTableContextMenuLoader" in content_source

    for marker in (
        "TableInternal.TableRowDelegate {",
        "TableInternal.TableHeader {",
        "TableInternal.TableDefaultContextMenu {",
        "PaintedRow {",
        "Paginator {",
        "\n    Loader {",
        "\n    Connections {",
    ):
        assert marker not in entry_source
