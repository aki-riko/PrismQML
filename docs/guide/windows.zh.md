# 窗口

PrismQML 通过 `App.create_window(WindowType)` 创建带导航的主窗口。

## 窗口类型

| 类型 | 枚举值 | 说明 |
|------|--------|------|
| `WindowType.BAR` | 1 | 紧凑侧边导航（默认） |
| `WindowType.SPLIT` | 0 | 展开式侧边导航 |
| `WindowType.FILLED` | 2 | 填充式分割窗口 |

```python
from prismqml import App, WindowType

app = App()

window = app.create_window(WindowType.BAR)     # 紧凑侧边导航
# window = app.create_window(WindowType.SPLIT) # 展开式侧边导航
# window = app.create_window(WindowType.FILLED)# 填充式分割
```

## 添加导航页面

```python
window.addPage(HomePage, "Home", "首页")        # QML 组件, 图标名, 标题
window.addPage(SettingsPage, "Settings", "设置")
window.show()
```

## 窗口特性

- **懒加载** — 页面内容延迟到首次切换时加载，加快启动
- **云母效果（Mica）** — Windows 11 半透明背景（neo 皮肤下自动关闭，保持实心扁平）
- **系统托盘** — 见 [系统托盘](tray.md)
- **启动画面** — `SplashScreen` 首屏就绪后自动淡出（默认挂载）

!!! tip "neo 皮肤下的窗口"
    新粗野皮肤会自动关闭 Mica（实心米白底）、内容区加粗黑边、导航选中项变橙实心块——
    这些都由皮肤系统自动处理，无需手动配置。
