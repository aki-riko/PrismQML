# System Tray

`SystemTrayIcon` provides a tray icon + context menu.

```python
from prismqml import SystemTrayIcon, Icon

tray = SystemTrayIcon(icon="AppIcon.png", toolTip="My App")
tray.addAction(text="Show", icon="Visibility", triggered=window.show)
tray.addSeparator()
tray.addAction(text="Quit", icon="Power", triggered=app.quit)
tray.show()
```

- `icon` — tray icon (path or icon name)
- `toolTip` — hover tooltip
- `addAction(text, icon, triggered)` — add a menu item; `triggered` takes a callback
- `addSeparator()` — separator line

Icon names (e.g. `"Visibility"` / `"Power"`) come from the built-in Fluent icon set — see [Icons](../components/icons.md).
