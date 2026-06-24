# 图标

## Icon

PrismQML 内置完整 Fluent 图标集（`controls/icons/fluent/`，MIT）。

```qml
import PrismQML as Fluent

Fluent.Icon {
    icon: "Home"
    iconSize: Fluent.Enums.iconSize.m
    color: Fluent.Enums.textColor.primary
}
```

按图标名引用（如 `"Home"` / `"Settings"` / `"Visibility"` / `"Power"`）。导航项、托盘菜单、按钮等都可用图标名。

## Python 侧

```python
from prismqml import Icon, make_icon, make_theme_icon

icon = make_icon("Settings")          # QIcon
themed = make_theme_icon("Home")      # 跟随主题色
```

## 图标集

图标集名为 `fluent`（Microsoft Fluent UI System Icons，MIT 许可）。注：这是图标资源名，与设计皮肤无关——neo 皮肤同样使用这套图标。
