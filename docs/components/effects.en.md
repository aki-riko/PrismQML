# Effects

Visual effect components (`effects/` module).

## NeoShadow

The neo skin's signature — an offset solid-color rect with zero blur:

```qml
import PrismQML

NeoShadow {
    target: bgRect          // follows the target rect's geometry
    accent: control.focused // true turns it orange for emphasis
}
```

## ShadowedRectangle

A rect with a blurred shadow (Fluent-style soft shadow); `shadowVisible` toggles it.

## Others

- `Shadow` — generic shadow
- `ColorOverlay` — color overlay
- `GaussianBlur` — Gaussian blur
- `OpacityMask` — opacity mask (rounded-corner clipping)

## Skin adaptation

`NeoShadow` is dedicated to the neo hard-shadow paradigm; the Fluent skin uses `ShadowedRectangle` / `RectangularShadow` blurred shadows. Controls pick the shadow implementation by skin automatically — you usually never use these low-level effects directly.
