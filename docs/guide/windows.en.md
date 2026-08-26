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

The main window close path also reuses the same `PageTransition`. By default it
uses `Enums.animation.lazy_circle` to collapse the window content; the real
close is submitted only after the collapse completes. If the host rejects the
close request, `stop()` restores the original page visibility.

```qml
Fluent.Windows {
    closeAnimationType: Enums.animation.lazy_circle
    closeAnimation: null
}
```

`closeAnimationType: Enums.animation.none` skips the visual transition and
enters the real close path synchronously. With `Enums.animation.custom`,
`closeAnimation` uses the same `Component` contract described below. Startup,
lazy-page, and main-window exit transitions can therefore share one built-in or
custom lifecycle.

### Splash exit animation

The default `SplashScreen` uses `Enums.animation.lazy_circle`, sharing the same
collapse/expand lifecycle as lazy-loaded pages. Window-level properties are
forwarded to the default splash:

```qml
Fluent.Windows {
    splashExitAnimationType: Enums.animation.none
    // Or: Enums.animation.lazy_circle (the default)
    // splashExitAnimation: mySplashTransition
}
```

The same options are available when using `SplashScreen` directly:

```qml
SplashScreen {
    exitAnimationType: Enums.animation.lazy_circle
    exitAnimation: null
}
```

Built-in modes are exposed through `Enums.animation`:

| Value | Behavior |
| --- | --- |
| `Enums.animation.none` | Does not create a transition backend; `finish()` completes synchronously and hides the splash. |
| `Enums.animation.lazy_circle` | The default circular collapse/expand transition, including first-frame, target-frame, and fallback handling. |
| `Enums.animation.custom` | Uses the `Component` supplied by `exitAnimation` / `splashExitAnimation`. |

A custom `Component` must implement the following contract. The
`sourceItem` argument is the item being collapsed or expanded; `PageTransition`
reads and forwards the declared state and signals.

```qml
Component {
    Item {
        property bool active: false
        property bool running: false
        property bool collapsing: false
        property bool collapsed: false
        property real progress: 0

        signal collapseStarted()
        signal collapseFinished()
        signal expandStarted()
        signal expandFinished()

        function collapse(sourceItem) { /* ... */ return true }
        function expand(sourceItem) { /* ... */ return true }
        function stop() { /* cancel and restore your state */ }
    }
}
```

`collapse()` and `expand()` should emit their matching start and finish
signals and keep `progress`, `collapsing`, and `collapsed` consistent.
`stop()` cancels the current operation. When `finish()` is called, the default
splash invokes `expand(sourceItem)` and hides itself only after the completion
signal, then emits `finished()`. Lazy-loaded pages normally call
`collapse(sourceItem)` before changing content and `expand(sourceItem)` after
the new content is ready.

If the `Component` is missing a contract member, cannot be created, or the
built-in transition cannot capture its source, the facade logs the failure and
uses the no-animation path with deterministic final visibility. Custom
implementations should make `stop()` safe to call repeatedly. After a
transition finishes, the facade releases its source reference so a later
`stop()` cannot reveal a page that has already completed collapsing.

Pure QML windows may replace the visual through `splashComponent`. Its root
object must provide `finish()`, which the framework calls once the first page
is ready.

### PageTransition

Use the public `PageTransition` component when the same transition is needed by
a page or another overlay:

```qml
PageTransition {
    id: transition
    animationType: Enums.animation.lazy_circle
    revealTarget: true

    function showPage(page) {
        transition.expand(page)
    }
}
```

It exposes `collapse(sourceItem)`, `expand(sourceItem)`, and `stop()` methods,
the `active`, `running`, `collapsing`, `collapsed`, and `progress` states, and
four lifecycle signals. Its `customAnimation` property accepts the
`Component` contract above; custom mode should also set
`animationType: Enums.animation.custom`. `animationType:
Enums.animation.none` bypasses dynamic loading and emits start/finish signals
synchronously.

!!! tip "Windows under non-Fluent skins"
    Neobrutalism, Vintage Ticket, and Neumorphism auto-disable Mica and switch
    to their own surfaces, borders, shadows, and navigation states. The skin
    system handles these changes without application-specific configuration.
