# 系统托盘

`SystemTrayIcon` 提供系统托盘图标 + 右键菜单。

```python
from prismqml import SystemTrayIcon, Icon

tray = SystemTrayIcon(icon="AppIcon.png", toolTip="我的应用")
tray.addAction(text="显示", icon="Visibility", triggered=window.show)
tray.addSeparator()
tray.addAction(text="退出", icon="Power", triggered=app.quit)
tray.show()
```

- `icon` — 托盘图标（路径或图标名）
- `toolTip` — 悬停提示
- `addAction(text, icon, triggered)` — 添加菜单项，`triggered` 接回调
- `addSeparator()` — 分隔线

图标名（如 `"Visibility"` / `"Power"`）来自内置 Fluent 图标集，详见 [图标](../components/icons.md)。
