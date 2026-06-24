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

## style (7)

| Value | Description |
|-------|-------------|
| `style_default` | Default (white/outlined) |
| `style_primary` | Accent fill (auto-uses theme color; orange under neo) |
| `style_transparent` | Transparent |
| `style_filled` | Status-color fill (success/danger etc. by `level`) |
| `style_text` | Text only |
| `style_hyperlink` | Hyperlink |
| `style_gradient` | Gradient |

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
