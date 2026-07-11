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
import argparse
import importlib.util
import re
import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

# Force the automated probe headless and suppress native crash dialogs.
# 强制自动化探测无界面运行，并禁止原生崩溃弹窗。
configure_qml_test_process()

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_REQUIRED_PROPERTY_SKIPS = {
    "ButtonContent": "ButtonCore 内部内容区, required 属性由 ButtonCore 注入",
    "ButtonDropdown": "ButtonCore 内部分裂/下拉区, required 属性由 ButtonCore 注入",
    "ButtonProgress": "ButtonCore 内部进度层, required 属性由 ButtonCore 注入",
    "ListWidgetItem": "ListWidget delegate, itemData/itemIndex 由 ListWidget 注入",
    "SettingsCardContent": "SettingsCard 内部内容区, type 由 SettingsCard 注入",
    "HorizontalScrollMixin": "Mixin 附着组件, target 由宿主组件注入",
    "ViewportMixin": "Mixin 附着组件, target 由宿主组件注入",
}


def parse_args():
    """解析 probe 运行来源。"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--installed",
        action="store_true",
        help="从当前解释器已安装的 prismqml 包探测 QML 组件",
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


def probe_component(engine: QQmlEngine, type_name: str):
    """创建单个组件并返回成功状态与错误。"""
    qml = f"import PrismQML\n{type_name} {{}}\n"
    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
    if comp.isError():
        return False, [error.toString() for error in comp.errors()]

    obj = comp.create()
    if obj is None:
        details = "; ".join(error.toString() for error in comp.errors())
        return False, [f"create() 返回 None: {details}"]
    obj.deleteLater()
    return True, []


def collect_results(engine: QQmlEngine, types):
    """收集组件创建、预期跳过和真实错误。"""
    errors = {}
    expected_required_skips = {}
    ok = 0
    singleton_skips = []
    for type_name, is_singleton in types:
        if is_singleton:
            singleton_skips.append(type_name)
            continue
        passed, type_errors = probe_component(engine, type_name)
        if passed:
            ok += 1
        elif is_expected_required_property_skip(type_name, type_errors):
            expected_required_skips[type_name] = type_errors
        else:
            errors[type_name] = type_errors
    return ok, errors, expected_required_skips, singleton_skips


def report_results(ok, errors, expected_required_skips, singleton_skips, total):
    """输出 probe 汇总与错误详情。"""
    total_skips = len(singleton_skips) + len(expected_required_skips)
    print(f"\n{'='*60}")
    print(f"组件加载 probe 结果: {ok} OK / {len(errors)} 错误 / "
          f"{total_skips} 跳过 "
          f"(单例 {len(singleton_skips)} / required {len(expected_required_skips)}) "
          f"(共 {total})")
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


def main():
    """运行源码树或安装包的全组件 probe。"""
    args = parse_args()
    package_root = resolve_package_root(args.installed)
    qmldir = package_root / "PrismQML" / "qmldir"
    if not qmldir.is_file():
        raise FileNotFoundError(f"找不到 QML 模块注册文件: {qmldir}")

    app = QApplication([sys.argv[0]])
    engine = QQmlEngine()
    engine.addImportPath(str(package_root))
    types = parse_qmldir(qmldir)
    results = collect_results(engine, types)
    report_results(*results, len(types))
    QTimer.singleShot(0, app.quit)
    app.exec()
    return 1 if results[1] else 0


if __name__ == "__main__":
    raise SystemExit(main())
