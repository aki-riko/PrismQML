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
window.addPage(HomePage, "Home", "Home")        # QML component, icon name, nav text
window.addPage(SettingsPage, "Settings", "Settings")
window.show()
```

Set `visible=False` to keep a page route without presenting an item in the
navigation bar. Its page index and programmatic `navigateTo()` target stay
unchanged:

```python
window.addPage(HiddenPage, "Page", "Hidden page", position="bottom", visible=False)
```

## Window features

- **Lazy loading** — page content loads on first switch, speeding up startup
- **Mica effect** — Windows 11 translucent background (auto-disabled under non-Fluent skins to preserve their surface model)
- **System tray** — see [System Tray](tray.md)
- **Splash screen** — `SplashScreen` auto-fades once the first frame is ready (mounted by default)

## Mica and Acrylic

### Mica

Fluent.Windows applies the Windows 11 Mica backdrop automatically when all of
the following hold — no manual DWM API calls required:

- The `Window.MicaEnabled` setting is on (off by default)
- Windows 11 with Build ≥ 22621 (minimum for `DWMWA_SYSTEMBACKDROP_TYPE`)
- The current skin allows Mica (see the tip at the bottom of this page)

```python
from prismqml.python.config import getConfigManager

getConfigManager().setMicaEnabled(True)   # set before creating windows
```

To target any `QWindow` directly, use `MicaManager`:

| Member | Description |
|--------|-------------|
| `isMicaSupported` | Whether the DWM Mica backdrop is supported |
| `setMicaEffect(window, enabled, dark=False)` | Enable / disable Mica; returns `True` on success |
| `updateDarkMode(dark)` | Update dark mode for the current window |
| `setWindowCorner(window, rounded)` | Adjust corner preference without touching the Mica state |

```python
from prismqml import get_mica_manager

mica = get_mica_manager()
if not mica.setMicaEffect(window, True, dark=True):
    pass  # unsupported here; the window keeps its plain opaque background
```

On non-Windows, non-Win11, or older builds `isMicaSupported` is `False` and
`setMicaEffect()` simply returns `False` — no platform branching needed.

### Acrylic

Acrylic does not rely on a system backdrop: `AcrylicHelper` captures the
screen region relative to the window, blurs it, and serves it to a QML
`Image` through `image://acrylic`:

```python
from prismqml import get_acrylic_helper

helper = get_acrylic_helper()
helper.blurRadius = 60                             # range 1–100, default 100
url = helper.grabAndBlur(window, 0, 0, 300, 200)   # → "image://acrylic/<id>"
```

- The `imageReady(str)` signal carries the latest image URL;
  `grabWindowFrame(window, x, y, width, height)` captures the exact visible
  window pixels without blur
- The `image://acrylic` image provider is registered automatically by
  `App` / `register_types()`

## Generic Caption Action

A window can optionally place one generic action button immediately to the left of
the minimize, maximize, and close buttons. The engine owns placement, theme
styling, hit testing, and the signal; the host owns the meaning (for example AI,
help, or feedback):

```python
window.set_caption_action("Bot", "AI")
window.on_caption_action_triggered(open_ai_assistant)
```

```cpp
window.setCaptionAction(QStringLiteral("Bot"), QStringLiteral("AI"));
window.onCaptionActionTriggered(openAiAssistant);
```

The same capability is available to pure-QML windows:

```qml
Fluent.Windows {
    captionActionVisible: true
    captionActionIcon: "Bot"
    captionActionToolTip: "AI"
    onCaptionActionTriggered: openAiAssistant()
}
```

Leave `captionActionVisible: false` (the default) when no action is needed; the
system buttons keep their original geometry without an empty reserved slot.

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

Pure-QML `Fluent.Windows` instances register with the App-owned startup
lifecycle when they are created, so hosts do not need to call an internal
binding method. Non-standard QML windows can join the same FastSplash lifecycle
through the public `app.attach_startup_window(window)` API.

The main window close path also reuses the same `PageTransition`. By default it
uses `Enums.lazyAnimation.lazy_circle` to collapse the window content; the real
close is submitted only after the collapse completes. If the host rejects the
close request, `stop()` restores the original page visibility.

```qml
Fluent.Windows {
    closeAnimationType: Enums.lazyAnimation.lazy_circle
    closeAnimation: null
}
```

`closeAnimationType: Enums.lazyAnimation.none` skips the visual transition and
enters the real close path synchronously. With `Enums.lazyAnimation.custom`,
`closeAnimation` uses the same `Component` contract described below. Startup,
lazy-page, and main-window exit transitions can therefore share one built-in or
custom lifecycle.

The collapse pacing is shared between the main-window exit and page switches:
duration from `Enums.lazyLoadingTransitionMetrics.coverDuration` (420ms) and
easing from `Easing.InOutQuad`. Collapse progress runs 1 -> 0 with the radius
scaling linearly, so an ease-in curve holds the radius near maximum for most of
the duration and then crosses the entire remaining distance in the last few
frames, which on a low-refresh display reads as the window being cut away
half-collapsed. Measured on a real display, both sites produce identical pacing,
so one set of values serves both.

`PageTransition` exposes `coverDuration` and `coverEasing` for per-site
overrides:

```qml
Fluent.PageTransition {
    coverDuration: 360
    coverEasing: Easing.InOutCubic
}
```

When tuning `coverDuration`, note that the lazy page-switch Loader activation
budget is derived from it (`coverDuration` plus `loaderActivationHeadroom`), so
changing the collapse duration will not squeeze out the loading indicator.

### Splash exit animation

The default `SplashScreen` uses `Enums.lazyAnimation.lazy_circle`, sharing the same
collapse/expand lifecycle as lazy-loaded pages. Window-level properties are
forwarded to the default splash:

```qml
Fluent.Windows {
    splashExitAnimationType: Enums.lazyAnimation.none
    // Or: Enums.lazyAnimation.lazy_circle (the default)
    // splashExitAnimation: mySplashTransition
}
```

The same options are available when using `SplashScreen` directly:

```qml
SplashScreen {
    exitAnimationType: Enums.lazyAnimation.lazy_circle
    exitAnimation: null
}
```

Splash exit modes are exposed through `Enums.lazyAnimation`; regular
`StackedWidget` page-switch modes use `Enums.animation`:

| Value | Behavior |
| --- | --- |
| `Enums.lazyAnimation.none` | Does not create a transition backend; `finish()` completes synchronously and hides the splash. |
| `Enums.lazyAnimation.lazy_circle` | The default circular collapse/expand transition, including first-frame, target-frame, and fallback handling. |
| `Enums.lazyAnimation.custom` | Uses the `Component` supplied by `exitAnimation` / `splashExitAnimation`. |

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
    animationType: Enums.lazyAnimation.lazy_circle
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
`animationType: Enums.lazyAnimation.custom`. `animationType:
Enums.lazyAnimation.none` bypasses dynamic loading and emits start/finish signals
synchronously.

Lazy pages use `Enums.lazyAnimation.lazy_circle` by default, independently of
regular `StackedWidget` page-switch animations.

!!! tip "Windows under non-Fluent skins"
    Neobrutalism, Vintage Ticket, and Neumorphism auto-disable Mica and switch
    to their own surfaces, borders, shadows, and navigation states. The skin
    system handles these changes without application-specific configuration.
