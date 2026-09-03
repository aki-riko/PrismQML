<div class="prismqml-hero" markdown>

<span class="hero-eyebrow">PRISMQML · 棱镜映界</span>

# 一套 QML 控件，<em>多种设计语言</em>一键切换

<p class="hero-sub">基于 PySide6 + QML 的多皮肤 UI 引擎：同一套控件可在
Fluent、新粗野、复古票据与新拟态之间实时切换，并独立选择明暗主题。
<code>setSkin()</code> 一行换肤，120fps+ 流畅动画。</p>

<div class="hero-actions" markdown>
[快速开始 :material-arrow-right:](getting-started.md){ .md-button }
[皮肤系统 :material-palette:](guide/skins.md){ .md-button .hero-btn-ghost }
[控件总览](components/index.md){ .md-button .hero-btn-ghost }
</div>

</div>

<div class="prismqml-grid" markdown>

<div class="prismqml-card" markdown>

<span class="card-icon icon-blue" markdown>:material-palette:</span>

### :material-palette: 多皮肤引擎

`setSkin()` 一键切换 Fluent / 新粗野 / 复古票据 / 新拟态，四套皮肤均支持明暗模式。

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-teal" markdown>:material-puzzle:</span>

### :material-puzzle: token 驱动架构

颜色、几何、阴影全部走 token。新增一套皮肤几乎不动控件代码，皮肤与控件解耦。

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-orange" markdown>:material-lightning-bolt:</span>

### :material-lightning-bolt: 纯 QML 渲染

无帧率上限，120fps+ 流畅动画，Python 侧专注业务逻辑。

</div>

<div class="prismqml-card" markdown>

<span class="card-icon icon-purple" markdown>:material-package-variant:</span>

### :material-package-variant: 180+ QML 类型

按钮 / 输入 / 卡片 / 对话框 / 表格 / 图表 / 导航等常见场景全覆盖。

</div>

</div>

## 四套皮肤

<div class="prismqml-skins" markdown>

<div class="prismqml-skin-card skin-fluent" markdown>

<span class="skin-dot"></span>

### Fluent

圆角控件、模糊阴影、蓝色主题色，可选 Mica 云母效果。

</div>

<div class="prismqml-skin-card skin-neobrutalism" markdown>

<span class="skin-dot"></span>

### 新粗野

粗边框、零模糊硬阴影、橙色主色，按下时压平硬阴影。

</div>

<div class="prismqml-skin-card skin-vintage" markdown>

<span class="skin-dot"></span>

### 复古票据

暖纸背景、旧油墨前景与印章语义色，直角表面细线分隔。

</div>

<div class="prismqml-skin-card skin-neumorphism" markdown>

<span class="skin-dot"></span>

### 新拟态

同色表面、双向软阴影、凹凸交互。

</div>

</div>

![PrismQML 四套皮肤组件实景对比](images/prismqml-skins.png)

## 安装

```bash
pip install prismqml
```

分发名与导入名一致：`pip install prismqml` 后 `from prismqml import ...`。
要求 Python 3.9+ 与 PySide6 6.9+（Qt 6.9+）。Windows 宿主在创建首个
`QQuickWindow` 前固定使用 D3D11；其他平台保留 Qt 的平台默认后端。

```python
from prismqml import App, WindowType, setSkin, Skin

setSkin(Skin.NEOBRUTALISM)   # 一行切换整个应用的设计语言

app = App()
window = app.create_window(WindowType.BAR)
window.setWindowTitle("我的应用")
window.resize(1200, 800)
window.show()
app.exec()
```

## 下一步

- [快速开始](getting-started.md) — 几行代码跑起第一个窗口
- [安装](install.md) — pip 安装与开发模式
- [皮肤系统](guide/skins.md) — PrismQML 的招牌能力
- [控件总览](components/index.md) — 全部可用控件
- [组件速查表](components/list.md) — 全部类型的按分类快速索引
- [自动更新接入](auto-update.md) — 检查、下载进度、安装交接与真实升级验收

---

PrismQML 由 [FluentQML](https://github.com/aki-riko/FluentQML) 升级而来（多皮肤引擎定位），MIT 许可证。
