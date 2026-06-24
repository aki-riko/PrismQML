# Skins

The skin system is PrismQML's signature capability: **one component set, multiple design languages**.

## Skin and theme are orthogonal

PrismQML splits "design language" and "light/dark" into two independent dimensions:

| Dimension | Controls | Values |
|-----------|----------|--------|
| **skin** | design language | `fluent` / `neobrutalism` |
| **theme** | light/dark | `light` / `dark` / `auto` |

They combine freely — neo skin has light/dark too, Fluent skin has light/dark too.

## Switching skins

```python
from prismqml import setSkin, Skin

setSkin(Skin.FLUENT)          # Fluent Design: rounded corners, blurred shadows, blue accent
setSkin(Skin.NEOBRUTALISM)    # Neobrutalism: thick black borders, hard shadows, orange accent
```

```python
from prismqml import getSkin
print(getSkin())   # Skin.NEOBRUTALISM
```

## Visual paradigms

=== "Fluent"

    - Rounded corners (small radius / pill)
    - Blurred shadows (RectangularShadow, with blur radius)
    - Blue accent, semi-transparent overlays for hover/press
    - Mica effect

=== "Neobrutalism"

    - Thick black borders (2px solid)
    - Hard shadows (offset solid-black rect, zero blur)
    - Orange accent + high-saturation colors (green/red/amber)
    - Buttons "flatten" the hard shadow on press; input focus turns the border orange
    - Solid & flat (Mica disabled)

<!-- TODO: Fluent vs Neobrutalism side-by-side screenshot -->

## Reading the skin in QML

```qml
import PrismQML

Rectangle {
    // Most of the time you don't need to branch — controls adapt automatically
    radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small
}
```

- `Enums.skin` — current skin string (`"fluent"` / `"neobrutalism"`)
- `Enums.isNeobrutalism` — boolean convenience
- `Enums.neo.*` — neo-specific tokens (borderWidth / radius / shadowOffset, etc.)

## Architecture: token-driven, skins decoupled from components

Skin switching is not done with `if neo` in every control — differences are **collapsed into the token layer**:

- **Colors** via `Theme` / `StateColor` / `Constants.neoColors`
- **Geometry** via `Metrics` (radius / border / shadow)
- **Accent**: `Enums.accentColor` auto-resolves to orange under neo — every control referencing the accent (primary buttons, selected states, focus borders) turns orange automatically, no changes needed

Components are nearly **skin-agnostic**. Adding a third skin only needs a new token palette + minor structural branches, with almost no component changes.

## Dark neo

Neo's dark mode follows the [neobrutalism.dev](https://neobrutalism.dev) dark paradigm: charcoal background + brightened accent + light borders/hard shadows + light text. Switching to dark theme auto-applies this palette under the neo skin.
