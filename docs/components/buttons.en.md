# Buttons

A unified `Button` control that auto-detects its type by content (icon only → tool button; icon+text / text only → push button), combined via three orthogonal dimensions: `style` / `shape` / `feature`.

## Basic usage

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "OK"
    style: Fluent.Enums.button.style_primary
    onClicked: console.log("clicked")
}
```

## Unified menu entry point

Both `feature_dropdown` and `feature_split` accept a menu object that follows the `PopupWindowCore` contract (for example, `MenuCore`). The button handles prewarming, anchoring, toggling, and the arrow state; `menuItems` remains available for simple menus.

```qml
Fluent.MenuCore {
    id: actionMenu
    Fluent.Action { text: "Open" }
    Fluent.Action { text: "Export" }
}

Fluent.Button {
    text: "Actions"
    feature: Fluent.Enums.button.feature_split
    menu: actionMenu
    onClicked: console.log("main button clicked")
}
```

An external menu must expose `isOpen`, `prewarm()`, `openAtControl(control)`, and `close()`; an explicit warning is emitted for an invalid contract.

## style (7)

| Value | Description |
|-------|-------------|
| style_default | Default (white/outlined) |
| style_primary | Accent fill (auto-uses theme color; orange under neo) |
| style_transparent | Transparent |
| style_filled | Status-color fill (success/danger etc. by level) |
| style_text | Text only |
| style_hyperlink | Hyperlink |
| style_gradient | Gradient |

## glow (orthogonal axis)

Glow is **not** a style. It is its own axis alongside style / shape /
eature, so it composes with any combination of them:

`qml
// Accent button with a bloom
Fluent.Button {
    text: "Start"
    style: Fluent.Enums.button.style_primary
    glow: Fluent.Enums.button.glow_accent
}

// Or on top of any other style or feature
Fluent.Button {
    text: "Delete"
    style: Fluent.Enums.button.style_filled
    level: 3
    glow: Fluent.Enums.button.glow_accent
}
`

| Value | Description |
|-------|-------------|
| glow_none | No bloom (default) |
| glow_accent | Bloom following the resolved face colour |

- The halo takes the hue of **whatever face the style resolved**: an accent button
  blooms blue, a filled success button blooms green, a neutral default button
  blooms pale grey. That is what lets it compose with every fill style.
- It is drawn by one RectangularShadow. Qt 6.9+ renders it from a signed-distance
  field with **no offscreen layer**, the repo's mandated first choice for
  rectangular surfaces (AGENTS.md 6.2) and the only variant with a genuinely
  smooth falloff on a real display; stacked translucent rectangles band there.
- It is sized as a **ratio of the button height** (glowBlurRatio 0.45 /
  glowSpreadRatio 0.10), so 32 px and 60 px buttons read the same; fixed pixels
  run away on small buttons.
- The halo is lazy: only glow_accent instantiates it, so every other button keeps
  the object count and pixels it had before.
- The pulse animates only the shadow colour's alpha and never the geometry; it
  stops during a countdown, under reduced motion, and while the window is hidden.
- Flat styles with no fill (style_transparent / style_text / style_hyperlink)
  have no face for a bloom to sit behind, so they draw no halo.
- Ticket paper has zero elevation by design, so the bloom is not created there.
- A real bloom can only be judged on D3D11: the offscreen Software scene graph
  executes no shader effects. Accept with scripts/manual/glow_button_bloom_probe.py.

## shape

| Value | Description |
|-------|-------------|
| `shape_default` | Default radius (small under neo) |
| `shape_pill` | Pill (fully rounded) |

## feature (9)

Progress bar / ring / indeterminate / toggle / dropdown / split / countdown, etc.:

```qml
Fluent.Button {
    text: "Download"
    feature: Fluent.Enums.button.feature_progress_bar
}
```

`feature_none` · `feature_progress_bar` · `feature_progress_ring` · `feature_indeterminate_bar` · `feature_indeterminate_ring` · `feature_toggle` · `feature_dropdown` · `feature_split` · `feature_countdown`

## Skin adaptation

- **Fluent**: rounded + blurred shadow, hover semi-transparent overlay
- **Neobrutalism**: thick black border + hard shadow, "flattens" on press; primary is orange, filled uses high-saturation status colors (green/red/amber)

Switching skins needs no button code change — `style_primary`'s fill follows `accentColor` automatically.
