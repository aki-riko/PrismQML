# 主题

主题控制界面的**明暗**，与[皮肤](skins.md)（设计语言）正交。

## 切换主题

```python
from prismqml import setTheme, Theme

setTheme(Theme.LIGHT)   # 浅色
setTheme(Theme.DARK)    # 深色
setTheme(Theme.AUTO)    # 跟随系统
```

```python
from prismqml import getTheme, isDark
print(getTheme())   # Theme.DARK
print(isDark())     # True
```

## 自定义主题色

```python
from prismqml import setAccentColor, getAccentColor

setAccentColor("#0078d4")
print(getAccentColor())  # "#0078d4"
```

!!! note "neo 皮肤下的主题色"
    新粗野皮肤有自己固定的橙色主色体系，`accentColor` 在 neo 下会自动解析为 neo 橙，
    `setAccentColor` 的自定义值主要作用于 Fluent 皮肤。

## QML 中使用

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "确定"
    style: Fluent.Enums.button.style_primary
}

Rectangle {
    color: ThemeManager.accentColor   // 直接访问 ThemeManager 单例
}
```
