# Effects

Visual effect components (`effects/` module).

## ShadowedRectangle

A rect with a blurred shadow (Fluent-style soft shadow); `shadowVisible` toggles it. Registered in the root module:

```qml
import PrismQML as Fluent

Fluent.ShadowedRectangle {
    color: Enums.cardColor
    radius: Enums.radius.large
    shadowLevel: Enums.shadow.level4
}
```

## Others

- `Shadow` — generic shadow
- `ColorOverlay` — color overlay
- `GaussianBlur` — Gaussian blur
- `OpacityMask` — opacity mask (rounded-corner clipping)

## FocusVisual

`FocusVisual` draws a theme-accent focus ring while its source item has active focus.
It follows the parent by default; set `focusSource` to track another item. The actual
ring is created lazily, so an unfocused control keeps no active ring object.

```qml
import PrismQML as Fluent

Item {
    id: fieldShell

    Fluent.FocusVisual {
        anchors.fill: parent
        focusSource: fieldShell
        radius: Enums.radius.small
    }
}
```

`radius` controls the corner radius and `ringColor` defaults to `Enums.accentColor`.
The helper does not accept pointer events, so it will not cover the control underneath;
the host is still responsible for receiving focus.

## NeoShadow

The neo skin's signature — an offset solid-color rect with zero blur. `NeoShadow`
is not registered in the root module; import the `effects/` subdirectory directly
to use it. Also note that `target` is a required property:

```qml
NeoShadow {
    target: bgRect          // follows the target rect's geometry (required)
    accent: control.focused // true turns it orange for emphasis
}
```

## Skin adaptation

`NeoShadow` is dedicated to the neo hard-shadow paradigm; the Fluent skin uses `ShadowedRectangle` / `RectangularShadow` blurred shadows. Controls pick the shadow implementation by skin automatically — you usually never use these low-level effects directly.
