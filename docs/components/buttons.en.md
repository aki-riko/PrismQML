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

## style (8)

| Value | Description |
|-------|-------------|
| `style_default` | Default (white/outlined) |
| `style_primary` | Accent fill (auto-uses theme color; orange under neo) |
| `style_transparent` | Transparent |
| `style_filled` | Status-color fill (success/danger etc. by `level`) |
| `style_text` | Text only |
| `style_hyperlink` | Hyperlink |
| `style_gradient` | Gradient |
| `style_glow` | Bloom glow (accent face plus a soft breathing halo) |

### Glow button `style_glow`

A glow button keeps the `style_primary` face, ink, and press treatment, and only
adds a soft halo around it:

```qml
Fluent.Button {
    text: "Start"
    style: Fluent.Enums.button.style_glow
}
```

- The halo is stacked translucent rounded rectangles, **not a shader blur**: on a
  real D3D11 window both `RectangularShadow` and `MultiEffect` blur drew nothing
  behind this surface, while the layered rectangles are visible (`StepperHalo`
  already uses the same technique).
- The halo is lazy: only `style_glow` instantiates it, so every other style keeps
  the object count and pixels it had before.
- Disabled/loading states keep a faint static halo, hover brightens it and press
  pulls it in; the breathing loop stops during a countdown and under reduced
  motion.
- Ticket paper has zero elevation by design, so the bloom collapses to a plain
  accent face there.

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
