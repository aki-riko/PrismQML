# PrismQML

> **一套 QML 控件，多种设计语言一键切换。**

PrismQML 是基于 PySide6 + QML 的**多皮肤 UI 引擎**：同一套控件可在
**Fluent**、**新粗野（Neobrutalism）**、**复古票据（Vintage Ticket）**与
**新拟态（Neumorphism）**之间实时切换，并独立选择明暗主题。

![PrismQML 四套皮肤组件实景对比](images/prismqml-skins.png)

```python
from prismqml import setSkin, Skin

setSkin(Skin.NEOBRUTALISM)   # 一行切换整个应用的设计语言
```

## 为什么是 PrismQML

- **🎨 多皮肤引擎** — `setSkin()` 一键切换 Fluent / 新粗野 / 复古票据 / 新拟态，四套皮肤均支持明暗模式。
- **🧩 token 驱动架构** — 颜色、几何、阴影全部走 token。新增一套皮肤几乎不动控件代码，皮肤与控件解耦。
- **⚡ 纯 QML 渲染** — 无帧率上限，120fps+ 流畅动画。
- **🐍 PySide6 原生** — 无缝集成，业务逻辑留在 Python 侧，无需为业务界面编写 C++。
- **📦 180+ QML 类型** — 覆盖按钮 / 输入 / 卡片 / 对话框 / 表格 / 图表 / 导航等常见场景。
- **🪟 完整桌面能力** — 导航窗口、原生弹层、通知、Mica、系统托盘与自动更新均有统一入口。
- **🌍 跨平台** — Windows、macOS、Linux。

## 安装

```bash
pip install prismqml
```

分发名与导入名一致：`pip install prismqml` 后 `from prismqml import ...`。
要求 Python 3.9+ 与 PySide6 6.9+（Qt 6.9+）。Windows 宿主在创建首个
`QQuickWindow` 前固定使用 D3D11；其他平台保留 Qt 的平台默认后端。

## 下一步

- [快速开始](getting-started.md) — 几行代码跑起第一个窗口
- [皮肤系统](guide/skins.md) — PrismQML 的招牌能力
- [控件总览](components/index.md) — 全部可用控件
- [自动更新接入](auto-update.md) — 检查、下载进度、安装交接与真实升级验收
- [Windows 安装器模板](windows-installer.md) — 清单驱动的 Inno Setup 生成与编译

---

PrismQML 由 [FluentQML](https://github.com/aki-riko/FluentQML) 升级而来（多皮肤引擎定位），MIT 许可证。
