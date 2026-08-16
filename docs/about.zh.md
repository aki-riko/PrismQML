# 关于

## PrismQML 是什么

PrismQML 是基于 PySide6 + QML 的多皮肤 UI 引擎，由 **FluentQML 升级而来**——
从单一 Fluent Design 组件库，演进为支持 Fluent、新粗野、复古票据与新拟态的
多设计语言引擎。

## 从 FluentQML 迁移

如果你在用旧的 FluentQML（PyPI 包名 `fqml`，导入名 `fluentqml`），迁移到 PrismQML：

| 旧（FluentQML） | 新（PrismQML） |
|----------------|----------------|
| `pip install fqml` | `pip install prismqml` |
| `import fluentqml` | `import prismqml` |
| `from fluentqml import App` | `from prismqml import App` |
| QML `import FluentQML` | QML `import PrismQML` |
| `~/.fluentqml/` | `~/.prismqml/` |

迁移步骤：

1. `pip uninstall fqml && pip install prismqml`
2. 全局替换 `fluentqml` → `prismqml`（Python）、`FluentQML` → `PrismQML`（QML）
3. requirements 中 `fqml` → `prismqml`

包名、导入名与 QML 模块名是迁移的核心步骤。PrismQML 在 v1.0.0 前不保留
废弃兼容别名；若旧项目使用了 FluentQML 的内部路径或已移除 API，应按当前
[Python API](api/python.md) 与[控件总览](components/index.md)迁移。

## 为什么改名

`FluentQML` 这个名字锁死在"Fluent"单一设计语言上。加入新粗野（Neobrutalism）皮肤后，库已是多皮肤引擎，名实不符。PyPI / GitHub 不支持仓库改名，故新建 PrismQML（取"棱镜"意——一束光折射成多种面貌，对应一套控件呈现多种设计语言），旧 FluentQML 仓库存档保留，已分发的 `fqml` 包继续可用。

## License

PrismQML 采用 [MIT 许可证](https://github.com/aki-riko/PrismQML/blob/main/LICENSE)。内置 Fluent UI System Icons 图标集亦为 MIT。
