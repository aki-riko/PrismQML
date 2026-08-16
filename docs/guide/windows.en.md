# Windows

PrismQML creates navigated main windows via `App.create_window(WindowType)`.

## Window types

| Type | Value | Description |
|------|-------|-------------|
| `WindowType.BAR` | 1 | Compact side navigation (default) |
| `WindowType.SPLIT` | 0 | Expanded side navigation |
| `WindowType.FILLED` | 2 | Filled split window |

```python
from pathlib import Path

from prismqml import App, WindowType

app = App(application_icon=Path(__file__).with_name("app_icon.png"))

window = app.create_window(WindowType.BAR)     # compact side nav
# window = app.create_window(WindowType.SPLIT) # expanded side nav
# window = app.create_window(WindowType.FILLED)# filled split
```

Configure the application icon once on `App`; existing windows, future
windows, the taskbar, and the default splash inherit it automatically. Use a
window's `setWindowIcon()` only when that window needs an explicit override.

## Adding navigation pages

```python
window.addPage(HomePage, "Home", "Home")        # QML component, icon name, title
window.addPage(SettingsPage, "Settings", "Settings")
window.show()
```

## Window features

- **Lazy loading** — page content loads on first switch, speeding up startup
- **Mica effect** — Windows 11 translucent background (auto-disabled under non-Fluent skins to preserve their surface model)
- **System tray** — see [System Tray](tray.md)
- **Splash screen** — `SplashScreen` auto-fades once the first frame is ready (mounted by default)

## Splash screen

`NavigationWindowCore` owns creation, window coverage, and first-page-ready
dismissal. After the window becomes visible, the splash remains stable for at
least 600ms by default before its exit animation starts. Python, C++, and pure
QML therefore use the same lifecycle; hosts only pass configuration and do not
create the component themselves:

```python
window.showSplash(title="PrismQML", subtitle="Loading components...")
# window.setSplashEnabled(False)  # disable when needed
```

```cpp
window.setSplash(true, {}, {}, QStringLiteral("Loading components..."));
```

```qml
import PrismQML as Fluent

Fluent.Windows {
    windowTitle: "My App"
    windowIcon: "qrc:/app_icon.svg"
    splashSubtitle: "Loading..."
    // Override when needed; the default comes from Enums.duration.splashMinimumVisible.
    splashMinimumVisibleDuration: 600
}
```

Pure QML windows may replace the visual through `splashComponent`. Its root
object must provide `finish()`, which the framework calls once the first page
is ready.

!!! tip "Windows under non-Fluent skins"
    Neobrutalism, Vintage Ticket, and Neumorphism auto-disable Mica and switch
    to their own surfaces, borders, shadows, and navigation states. The skin
    system handles these changes without application-specific configuration.
