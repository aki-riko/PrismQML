# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Headless 全组件加载 probe — 重排验证工具

遍历根 qmldir 注册的全部公开组件,逐个 createComponent 实例化,
捕获加载/绑定错误。已知必须由父组件注入 required property 的内部子模块
会被归类为预期跳过,真正新增的加载错误仍会失败。

用法: python tests/qml/probe_all_components.py
退出码: 0=无非预期错误, 1=有非预期加载错误
"""
import sys
import re
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

# 定位 qml 包根
PKG_ROOT = Path(__file__).resolve().parents[2] / "prismqml"
QML_DIR = PKG_ROOT / "PrismQML"
QMLDIR = QML_DIR / "qmldir"


EXPECTED_REQUIRED_PROPERTY_SKIPS = {
    "ButtonContent": "ButtonCore 内部内容区, required 属性由 ButtonCore 注入",
    "ButtonDropdown": "ButtonCore 内部分裂/下拉区, required 属性由 ButtonCore 注入",
    "ButtonProgress": "ButtonCore 内部进度层, required 属性由 ButtonCore 注入",
    "ListWidgetItem": "ListWidget delegate, itemData/itemIndex 由 ListWidget 注入",
    "SettingsCardContent": "SettingsCard 内部内容区, type 由 SettingsCard 注入",
    "HorizontalScrollMixin": "Mixin 附着组件, target 由宿主组件注入",
    "ViewportMixin": "Mixin 附着组件, target 由宿主组件注入",
}


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


def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    # 注册 import 路径:包根的父目录,使 `import PrismQML` 生效
    engine.addImportPath(str(PKG_ROOT))

    types = parse_qmldir(QMLDIR)
    errors = {}
    expected_required_skips = {}
    ok = 0
    singleton_skips = []

    for type_name, is_singleton in types:
        if is_singleton:
            # 单例(Enums/Translator/DpiManager)由引擎托管,不单独 createComponent
            singleton_skips.append(type_name)
            continue
        qml = f"import PrismQML\n{type_name} {{}}\n"
        comp = QQmlComponent(engine)
        comp.setData(qml.encode("utf-8"), QUrl("inline"))
        if comp.isError():
            type_errors = [e.toString() for e in comp.errors()]
            if is_expected_required_property_skip(type_name, type_errors):
                expected_required_skips[type_name] = type_errors
            else:
                errors[type_name] = type_errors
            continue
        obj = comp.create()
        if obj is None:
            type_errors = ["create() 返回 None: " +
                           "; ".join(e.toString() for e in comp.errors())]
            if is_expected_required_property_skip(type_name, type_errors):
                expected_required_skips[type_name] = type_errors
            else:
                errors[type_name] = type_errors
            continue
        ok += 1
        obj.deleteLater()

    total_skips = len(singleton_skips) + len(expected_required_skips)
    print(f"\n{'='*60}")
    print(f"组件加载 probe 结果: {ok} OK / {len(errors)} 错误 / "
          f"{total_skips} 跳过 "
          f"(单例 {len(singleton_skips)} / required {len(expected_required_skips)}) "
          f"(共 {len(types)})")
    print(f"{'='*60}")
    if singleton_skips:
        print("\n[单例跳过]")
        for name in singleton_skips:
            print(f"    {name}: singleton 由 QML 引擎托管")
    if expected_required_skips:
        print("\n[预期 required property 跳过]")
        for name in sorted(expected_required_skips):
            print(f"    {name}: {EXPECTED_REQUIRED_PROPERTY_SKIPS[name]}")
    if errors:
        for name, errs in sorted(errors.items()):
            print(f"\n[错误] {name}:")
            for e in errs:
                print(f"    {e}")

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
