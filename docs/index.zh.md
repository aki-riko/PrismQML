# PrismQML

> **一套 QML 控件，多种设计语言一键切换。**

PrismQML 是基于 PySide6 + QML 的**多皮肤 UI 引擎**：同一套控件可在 **Fluent** 与**新粗野（Neobrutalism）**之间切换，并独立选择明暗主题。

```python
from prismqml import setSkin, Skin

setSkin(Skin.NEOBRUTALISM)   # 一行切换整个应用的设计语言
```

## 为什么是 PrismQML

- **🎨 多皮肤引擎** — `setSkin()` 一键在 Fluent / 新粗野之间切换，两者均支持明暗模式。
- **🧩 token 驱动架构** — 颜色、几何、阴影全部走 token。新增一套皮肤几乎不动控件代码，皮肤与控件解耦。
- **⚡ 纯 QML 渲染** — 无帧率上限，120fps+ 流畅动画。
- **🐍 PySide6 原生** — 无缝集成，业务逻辑留在 Python 侧，不碰 C++。
- **📦 控件齐全** — 按钮 / 输入 / 卡片 / 对话框 / 表格 / 图表 / 导航等全套。
- **🌍 跨平台** — Windows、macOS、Linux。

## 安装

```bash
pip install prismqml
```

分发名与导入名一致：`pip install prismqml` 后 `from prismqml import ...`。

## 下一步

- [快速开始](getting-started.md) — 几行代码跑起第一个窗口
- [皮肤系统](guide/skins.md) — PrismQML 的招牌能力
- [控件总览](components/index.md) — 全部可用控件
- [自动更新接入](auto-update.md) — 检查、下载进度、安装交接与真实升级验收
- [Windows 安装器模板](windows-installer.md) — 清单驱动的 Inno Setup 生成与编译

---

PrismQML 由 [FluentQML](https://github.com/aki-riko/FluentQML) 升级而来（多皮肤引擎定位），MIT 许可证。
