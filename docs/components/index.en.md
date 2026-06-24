# Components Overview

PrismQML provides 170+ QML types covering buttons, inputs, data, feedback, dialogs, navigation, and more. **All controls adapt to the current [skin](../guide/skins.md) automatically** — no need to write separate code for Fluent / Neobrutalism.

## Import

Most controls are imported from the top-level module:

```qml
import PrismQML as Fluent

Fluent.Button { text: "OK" }
Fluent.Card { /* ... */ }
```

!!! warning "Controls sharing names with QtQuick"
    `ComboBox`, `Slider`, etc. share names with QtQuick.Controls native types and are not exported
    at the top-level `PrismQML` module. Import by submodule directory:
    `import "../prismqml/PrismQML/controls/inputs"`.

## Categories

| Category | Main controls |
|----------|---------------|
| [Buttons](buttons.md) | Button · CustomButton · ToolButton |
| [Inputs](inputs.md) | LineEdit · ComboBox · Slider · SpinBox · CheckBox · RadioButton · ToggleSwitch · PinInput |
| [Cards](cards.md) | Card · ExampleCard · Expander |
| [Data](data.md) | TableView · ListView · TreeView · Carousel · Avatar |
| [Feedback](feedback.md) | ProgressBar · ProgressRing · Toast · InfoBar · Tooltip · Skeleton |
| [Dialogs](dialogs.md) | Dialog · FlyoutSheet · MaskedDialog · ProgressDialog · PopupWindow |
| [Navigation](navigation.md) | NavigationBar · NavigationView · TabWidget · Breadcrumb · PipsPager |
| [Containers](containers.md) | Layout · ScrollArea · Separator · GroupBox · Drawer · Timeline |
| [Charts](charts.md) | ChartView (bar/line/pie, etc.) |
| [Icons](icons.md) | Icon (built-in Fluent icon set) |
| [Menus](menus.md) | Menu · MenuBar |
| [Badges](badges.md) | Badge · Tag · Chip |
| [Effects](effects.md) | NeoShadow · ShadowedRectangle · ColorOverlay · GaussianBlur |

> Full list in each `controls/` subdirectory's `qmldir`.
