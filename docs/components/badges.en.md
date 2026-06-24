# Badges

Small labels / badges / chips.

## Badge

```qml
import PrismQML as Fluent

Fluent.Badge { count: 8; level: Fluent.Enums.statusLevel.error }      // count
Fluent.Badge { text: "NEW"; level: Fluent.Enums.statusLevel.success } // text
Fluent.Badge { dot: true }                                            // dot
```

`level`: info / success / warning / error / attention / processing.

## Tag

```qml
Fluent.Tag { text: "Tag" }
```

## Chip

```qml
Fluent.Chip { text: "Selectable"; checked: true; closable: true }
```

Supports checked state and a close button.

## Skin adaptation

Under neo: badges/tags/chips get thick black borders; badge status colors use high-saturation versions; Chip has an orange fill when selected, white otherwise, both with black borders + hard shadows.
