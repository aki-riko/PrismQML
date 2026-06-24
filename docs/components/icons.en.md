# Icons

## Icon

PrismQML bundles the full Fluent icon set (`controls/icons/fluent/`, MIT).

```qml
import PrismQML as Fluent

Fluent.Icon {
    icon: "Home"
    iconSize: Fluent.Enums.iconSize.m
    color: Fluent.Enums.textColor.primary
}
```

Reference by icon name (e.g. `"Home"` / `"Settings"` / `"Visibility"` / `"Power"`). Nav items, tray menus, buttons, etc. all accept icon names.

## Python side

```python
from prismqml import Icon, make_icon, make_theme_icon

icon = make_icon("Settings")          # QIcon
themed = make_theme_icon("Home")      # follows theme color
```

## Icon set

The icon set is named `fluent` (Microsoft Fluent UI System Icons, MIT). Note: this is a resource name, unrelated to the design skin — the neo skin uses the same icons.
