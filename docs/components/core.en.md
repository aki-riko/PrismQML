# Core and utilities

Platform capability and helper singletons from the root module. They do not draw standalone
controls; other QML components use them to share behavior.

## Touch

`Touch` reads the host-provided `PlatformInfo` and exposes `isTouch`, `isMobile`, `isCompact`,
and `minTargetSize`. On desktop, `minTargetSize` is `0`, so raising interactive metrics with it
does not change the desktop layout.

```qml
import PrismQML as Fluent

height: Fluent.Touch.target(Enums.controlSize.inputHeight)
readonly property bool active: Fluent.Touch.feedback(hovered, pressed)
visible: Fluent.Touch.reveal(hovered)
```

Methods:

- `feedback(hovered, pressed)`: returns hover state on desktop and press state on touch, avoiding
  a synthetic hover highlight that remains after release.
- `reveal(hovered)`: always returns `true` on touch and follows `hovered` on desktop, keeping
  hover-revealed entry points reachable on touch devices.
- `target(desktopSize)`: raises an interactive size to the touch minimum when needed.

Touch interfaces should not rely on hover tooltips; tooltip controls use `Touch.isTouch` to close
that entry path.

## WheelEventUtils

`WheelEventUtils` normalizes Qt wheel events across system direction settings. `verticalDelta(event)`
and `horizontalDelta(event)` return `0` when `angleDelta` is unavailable and invert the selected
axis when `event.inverted` is `true`.

```qml
var dy = Fluent.WheelEventUtils.verticalDelta(event)
var dx = Fluent.WheelEventUtils.horizontalDelta(event)
```

## AccessibilityHelper

`AccessibilityHelper` maps `Enums.accessibility` tokens to Qt `Accessible` roles and centralizes
accessible-name and description handling so components do not duplicate the mapping.

```qml
Accessible.role: AccessibilityHelper.roleValue(
    Enums.accessibility.role_button
)
Accessible.name: AccessibilityHelper.resolveName(
    explicitName, visibleText, toolTipText
)
Accessible.description: AccessibilityHelper.describe([
    hintText, shortcutText
])
```

Methods:

- `roleValue(role)`: returns the matching Qt accessible role; unknown tokens return
  `Accessible.NoRole`.
- `namePart(name)`: takes the primary name from `Primary name|extra detail`.
- `describe(parts)`: drops empty values and joins the remaining parts with `. `.
- `resolveName(explicitName, visibleText, toolTipText)`: chooses the first non-empty value in
  explicit-name, visible-text, tooltip order.
