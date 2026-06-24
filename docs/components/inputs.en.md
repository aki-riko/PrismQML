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

!!! warning "Import"
    `ComboBox` shares a name with QtQuick, import by submodule:
    ```qml
    import "../prismqml/PrismQML/controls/inputs/ComboBox"
    ComboBoxDefault { model: ["Option 1", "Option 2", "Option 3"] }
    ```

## Slider

```qml
import "../prismqml/PrismQML/controls/inputs/Slider"
SliderCore { value: 60; from: 0; to: 100 }
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

## Others

- `SpinBox` — numeric stepper
- `PinInput` — OTP/PIN segmented input
- `BeforeAfterSlider` — image comparison slider

## Skin adaptation

Under neo: inputs have a white fill with thick black borders, **border + hard shadow turn orange on focus**; checkboxes/radios/switches use thick black borders with orange checked states.
