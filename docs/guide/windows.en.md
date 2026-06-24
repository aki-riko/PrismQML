# Windows

PrismQML creates navigated main windows via `App.create_window(WindowType)`.

## Window types

| Type | Value | Description |
|------|-------|-------------|
| `WindowType.BAR` | 1 | Compact side navigation (default) |
| `WindowType.SPLIT` | 0 | Expanded side navigation |
| `WindowType.FILLED` | 2 | Filled split window |

```python
from prismqml import App, WindowType

app = App()

window = app.create_window(WindowType.BAR)     # compact side nav
# window = app.create_window(WindowType.SPLIT) # expanded side nav
# window = app.create_window(WindowType.FILLED)# filled split
```

## Adding navigation pages

```python
window.addPage(HomePage, "Home", "Home")        # QML component, icon name, title
window.addPage(SettingsPage, "Settings", "Settings")
window.show()
```

## Window features

- **Lazy loading** — page content loads on first switch, speeding up startup
- **Mica effect** — Windows 11 translucent background (auto-disabled under neo skin for a solid flat look)
- **System tray** — see [System Tray](tray.md)
- **Splash screen** — `SplashScreen` auto-fades once the first frame is ready (mounted by default)

!!! tip "Windows under the neo skin"
    The neo skin auto-disables Mica (solid cream background), adds thick black borders to the content
    area, and turns the selected nav item into a solid orange block — all handled by the skin system.
