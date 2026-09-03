# Components Overview

PrismQML provides 180+ QML types covering buttons, inputs, data, feedback,
dialogs, navigation, and more. **All controls adapt to the current
[skin](../guide/skins.md) automatically**, with no separate UI implementation
for Fluent / Neobrutalism / Vintage Ticket / Neumorphism.

## Import

Most controls are imported from the top-level module:

```qml
import PrismQML as Fluent

Fluent.Button { text: "OK" }
Fluent.Card { /* ... */ }
```

!!! note "Top-level components"
    `ComboBox` and `Slider` are registered by the top-level `PrismQML` module. Use
    `Fluent.ComboBox` / `Fluent.Slider` through the module alias; do not import
    QtQuick.Controls or internal directories.

## Categories

| Category | Main controls |
|----------|---------------|
| [Buttons](buttons.md) | Button · CustomButtonCore · CloseButton |
| [Inputs](inputs.md) | LineEdit · ComboBox · Slider · SpinBox · CheckBox · RadioButton · ToggleSwitch · PinInput |
| [Cards](cards.md) | Card · ExampleCard · Expander |
| [Data](data.md) | TableView · ListView · TreeView · Carousel · Avatar |
| [Feedback](feedback.md) | ProgressBar · ProgressRing · Toast · InfoBar · ToolTip · Skeleton |
| [Dialogs](dialogs.md) | MessageBox · ConfirmDialog · MaskedDialog · FlyoutSheet · ProgressDialog · PopupWindowCore |
| [Navigation](navigation.md) | NavigationBar · NavigationView · TabWidget · Breadcrumb · PipsPager |
| [Containers](containers.md) | FlowLayout · GridLayout · HBoxLayout · VBoxLayout · ScrollArea · Separator · GroupBox · Drawer · Timeline |
| [Charts](charts.md) | ChartView (bar/line/pie, etc.) |
| [Icons](icons.md) | Icon (built-in Fluent icon set) |
| [Menus](menus.md) | ContextMenu · MenuBar |
| [Badges](badges.md) | Badge · Tag · Chip |
| [Effects](effects.md) | Shadow · ShadowedRectangle · ColorOverlay · GaussianBlur |
| Auth / Chat / Settings | LoginWindow · ChatBubble · ChatMessageList · SettingsCard, etc. (no dedicated pages yet; see the [cheat sheet](list.md) for the full list) |

> Full list in each `controls/` subdirectory's `qmldir`.
