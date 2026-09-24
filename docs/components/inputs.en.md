# Inputs

Text input, selection, and toggle form controls.

## LineEdit

```qml
import PrismQML as Fluent

Fluent.LineEdit {
    placeholderText: "Enter text"
    width: 240
}
```

Supports clear button, password mode, labels (LineEditLabel), tag input (TagLineEdit), etc.

## ComboBox

```qml
import PrismQML as Fluent
Fluent.ComboBoxDefault { model: ["Option 1", "Option 2", "Option 3"] }
```

## Slider

```qml
import PrismQML as Fluent
Fluent.Slider { value: 60; from: 0; to: 100 }
```

## Toggles

- `CheckBox` — checkbox (tristate supported)
- `RadioButton` — radio
- `ToggleSwitch` — switch

```qml
Fluent.CheckBox { text: "Remember me"; checked: true }
Fluent.RadioButton { text: "Option A" }
Fluent.ToggleSwitch { text: "Enabled"; checked: true }
```

Tristate values are exposed through `Enums.toggle`: `state_unchecked`, `state_partially_checked`, and `state_checked`. `checked` and `checkState` stay synchronized; the partially checked state maps to `checked: false`.

```qml
Fluent.CheckBox {
    text: "Partially selected"
    tristate: true
    checkState: Fluent.Enums.toggle.state_partially_checked
}
```

## SpinBox numeric stepper

```qml
import PrismQML as Fluent

Fluent.SpinBox {
    minimum: 0
    maximum: 100
    value: 42
}
```

`type` selects the variant: `Enums.input.spinbox_normal`, `spinbox_double`, `spinbox_compact`, `spinbox_compact_double`; `prefix` / `suffix` provide text units.

A unit can also be an icon: `prefixIcon` / `suffixIcon` accept a Fluent icon name, emoji or image path (svg/png/qrc/file), render right beside the value, and `iconSize` sets the size (default `Enums.iconSize.s`). Icons are tinted with the control text color; set `iconThemeAware: false` to keep the original artwork colors.

```qml
Fluent.SpinBox {
    value: 42
    prefixIcon: Fluent.Enums.icon.wallet
    suffixIcon: "qrc:/app/images/gold_brick.svg"
    iconThemeAware: false
}
```

## Others

- `SpinBox` — numeric stepper
- `PinInput` — OTP/PIN segmented input
- `BeforeAfterSlider` — image comparison slider

## SwipeControl

Drag the content sideways to reveal actions on either edge: releasing past half snaps the row open, otherwise it closes; tapping an action emits `actionTriggered(key, side)` and closes the row, and tapping the content while open closes it too. Mouse and touch share one `DragHandler`, so it works on desktop as well.

```qml
Fluent.SwipeControl {
    width: 420; height: 52
    leftActions: [
        { key: "flag", text: "Flag", icon: <path>, level: Enums.statusLevel.info }
    ]
    rightActions: [
        { key: "archive", text: "Archive", icon: <path>, level: Enums.statusLevel.warning },
        { key: "delete", text: "Delete", icon: <path>, level: Enums.statusLevel.error }
    ]
    onActionTriggered: (key, side) => runAction(key, side)

    Rectangle { anchors.fill: parent }   // content goes through the default property
}
```

- `actionWidth` is the width of one revealed action (defaults to `Enums.controlSize.swipeActionWidth`); an entry with `enabled: false` is dimmed and not clickable.
- Button tint comes from `Enums.statusLevel.getColorByLevel(level)`, with text and icons in `Enums.accentForeground`.
- Imperative control: `open("left")` / `open("right")` / `close()`, with `isOpen` / `openSide` for state.

## Skin adaptation

Under neo: inputs have a white fill with thick black borders, **border + hard shadow turn orange on focus**; checkboxes/radios/switches use thick black borders with orange checked states.
