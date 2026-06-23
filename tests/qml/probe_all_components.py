# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是 FluentQML 的一部分，采用 MIT 许可证授权。
"""Headless 全组件加载 probe — 重排验证工具

遍历根 qmldir 注册的全部公开组件,逐个 createComponent 实例化,
捕获加载/绑定错误。重排前跑一次记基线,重排后跑对比,不新增错误即安全。

用法: python tests/qml/probe_all_components.py
退出码: 0=无错误, 1=有加载错误
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


def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    # 注册 import 路径:包根的父目录,使 `import PrismQML` 生效
    engine.addImportPath(str(PKG_ROOT))

    types = parse_qmldir(QMLDIR)
    errors = {}
    ok = 0
    skipped = []

    for type_name, is_singleton in types:
        if is_singleton:
            # 单例(Enums/Translator/DpiManager)由引擎托管,不单独 createComponent
            skipped.append(type_name)
            continue
        qml = f"import PrismQML\n{type_name} {{}}\n"
        comp = QQmlComponent(engine)
        comp.setData(qml.encode("utf-8"), QUrl("inline"))
        if comp.isError():
            errors[type_name] = [e.toString() for e in comp.errors()]
            continue
        obj = comp.create()
        if obj is None:
            errors[type_name] = ["create() 返回 None: " +
                                 "; ".join(e.toString() for e in comp.errors())]
            continue
        ok += 1
        obj.deleteLater()

    print(f"\n{'='*60}")
    print(f"组件加载 probe 结果: {ok} OK / {len(errors)} 错误 / "
          f"{len(skipped)} 单例跳过 (共 {len(types)})")
    print(f"{'='*60}")
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
