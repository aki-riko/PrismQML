# Theming

Theme controls the **light/dark** appearance, orthogonal to [skins](skins.md) (design language).

## Switching theme

```python
from prismqml import setTheme, Theme

setTheme(Theme.LIGHT)   # light
setTheme(Theme.DARK)    # dark
setTheme(Theme.AUTO)    # follow system
```

```python
from prismqml import getTheme, isDark
print(getTheme())   # Theme.DARK
print(isDark())     # True
```

## Custom accent color

```python
from prismqml import setAccentColor, getAccentColor

setAccentColor("#0078d4")
print(getAccentColor())  # "#0078d4"
```

!!! note "Accent color under neo skin"
    Neobrutalism has its own fixed orange accent system. `accentColor` auto-resolves to neo orange
    under the neo skin, so `setAccentColor` custom values mainly apply to the Fluent skin.

## Using in QML

```qml
import PrismQML as Fluent

Fluent.Button {
    text: "OK"
    style: Fluent.Enums.button.style_primary
}

Rectangle {
    color: ThemeManager.accentColor   // access the ThemeManager singleton directly
}
```
