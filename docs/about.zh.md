# 关于

## PrismQML 是什么

PrismQML 是基于 PySide6 + QML 的多皮肤 UI 引擎，由 **FluentQML 升级而来**——从单一 Fluent Design 组件库，演进为支持多设计语言（Fluent + 新粗野）的换皮引擎。

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

API 完全兼容，迁移只是改名。

## 为什么改名

`FluentQML` 这个名字锁死在"Fluent"单一设计语言上。加入新粗野（Neobrutalism）皮肤后，库已是多皮肤引擎，名实不符。PyPI / GitHub 不支持仓库改名，故新建 PrismQML（取"棱镜"意——一束光折射成多种面貌，对应一套控件呈现多种设计语言），旧 FluentQML 仓库存档保留，已分发的 `fqml` 包继续可用。

## License

PrismQML 采用 [MIT 许可证](https://github.com/aki-riko/PrismQML/blob/main/LICENSE)。内置 Fluent UI System Icons 图标集亦为 MIT。
