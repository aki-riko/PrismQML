# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Root-qmldir reachability for the Fluent parity components.

根 qmldir 可达性门禁：Fluent 对标组件的公开注册保护。

``probe_all_components`` 与 ``test_headless_test_entrypoints`` 只断言
"被 probe 到的类型全部 OK"，并且刻意不钉组件总数（RELEASING.md 禁止钉死
会随注册漂移的计数）。因此误删根 qmldir 里的注册行时，注册总数会同步变小，
既有门禁仍会通过，只有人工跑 probe 才能发现。

本测试补上那一环：用真实 ``import PrismQML`` 逐个实例化本轮新增的公开组件，
把公开注册面钉成"必须可达"。它只断言这些具名类型，不钉全量总数，因此新增
其它组件不会逼迫修改本文件。

The probe gates only assert "every probed type is OK" and deliberately avoid
pinning the component total. Deleting a root-qmldir registration therefore keeps
them green. This test pins reachability of the specific public types added for
Fluent parity, without pinning any global total.
"""

import pytest

# Newly registered public types that must stay reachable through `import PrismQML`.
# 必须保持经 `import PrismQML` 可达的新增公开类型。
REQUIRED_ROOT_TYPES = (
    "RadioMenuFlyoutItem",
    "CommandBarFlyout",
    "RelativePanel",
    "Viewbox",
    "ParallaxView",
    "AnimatedIcon",
    "MediaPlayerElement",
    "MapControl",
    "WebView2",
    "RibbonBar",
    "RibbonTab",
    "RibbonGroup",
    "AppBarButton",
    "AppBarToggleButton",
    "AppBarSeparator",
    "FocusVisual",
    "AccessibilityHelper",
)

# Types whose construction touches heavyweight backends stay uninstantiated here;
# reachability is still proven by the binding resolving without errors.
# 构造期会触达重型后端的类型在此只验证可达性，实例化交由各自的延迟创建测试。
INSTANTIATE_EXEMPT = frozenset(
    {
        "MediaPlayerElement",
        "MapControl",
        "WebView2",
        # Composite singletons are not creatable from QML, so reachability is the
        # only thing a component expression can prove for them.
        # 组合单例无法从 QML 实例化，因此组件表达式对它们只能证明可达。
        "AccessibilityHelper",
    }
)


def _component_source(type_name: str, instantiate: bool) -> bytes:
    # `import PrismQML as Fluent` is a namespace import, so every type must be
    # qualified with the `Fluent.` prefix. A bare type name never resolves here.
    # `import PrismQML as Fluent` 是命名空间导入，类型必须带 `Fluent.` 前缀；
    # 裸类型名在此写法下永远解析不到。
    qualified = f"Fluent.{type_name}"
    body = f"    property bool resolved: typeof {qualified} !== 'undefined'\n"
    if instantiate:
        body += f"    {qualified} {{ }}\n"
    return ("import QtQuick\nimport PrismQML as Fluent\n\nItem {\n" + body + "}\n").encode(
        "utf-8"
    )


@pytest.fixture(scope="module")
def _root_type_source() -> str:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    return (root / "prismqml" / "PrismQML" / "qmldir").read_text(encoding="utf-8")


def _registered_type_names(qmldir_source: str) -> set[str]:
    """Collect the type name of every active (non-commented) qmldir line.

    逐行取类型名 token：跳过可选的 `singleton` 修饰符，避免把修饰符当成类型名。
    """
    names: set[str] = set()
    for raw in qmldir_source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2 or not parts[-1].endswith(".qml"):
            continue
        # `singleton Foo Foo.qml` registers the type `Foo`, not `singleton`.
        # `singleton Foo Foo.qml` 注册的类型是 Foo 而非 singleton。
        names.add(parts[1] if parts[0] == "singleton" else parts[0])
    return names


def test_every_parity_type_is_registered_in_the_root_qmldir(
    _root_type_source: str,
) -> None:
    """Every required public type still has an active root-qmldir registration."""
    registered = _registered_type_names(_root_type_source)
    missing = [name for name in REQUIRED_ROOT_TYPES if name not in registered]
    assert missing == [], (
        "这些类型缺少根 qmldir 注册行，`import PrismQML` 消费者将看不到它们: "
        + ", ".join(missing)
    )


@pytest.mark.parametrize("type_name", REQUIRED_ROOT_TYPES)
def test_parity_type_resolves_through_the_root_module(
    qml_engine, type_name: str
) -> None:
    """Each type resolves through `import PrismQML`, and instantiates when safe."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent

    instantiate = type_name not in INSTANTIATE_EXEMPT
    component = QQmlComponent(qml_engine)
    component.setData(_component_source(type_name, instantiate), QUrl())

    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, (
        f"{type_name} 未能经 `import PrismQML` 解析: " + "; ".join(errors)
    )

    instance = component.create()
    assert instance is not None, f"{type_name} 实例化失败: " + "; ".join(errors)
    assert instance.property("resolved") is True, (
        f"{type_name} 在 `import PrismQML` 下未解析为已定义类型"
    )
    instance.deleteLater()
