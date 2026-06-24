# 控件总览

PrismQML 提供 170+ QML 类型，覆盖按钮、输入、数据、反馈、弹层、导航等全部常见场景。**所有控件自动适配当前[皮肤](../guide/skins.md)**——无需为 Fluent / 新粗野分别编写。

## 导入方式

大多数控件通过顶层模块导入：

```qml
import PrismQML as Fluent

Fluent.Button { text: "确定" }
Fluent.Card { /* ... */ }
```

!!! warning "与 QtQuick 同名的控件"
    `ComboBox`、`Slider` 等与 QtQuick.Controls 原生类型同名，未在顶层 `PrismQML` 模块导出，
    需按子模块目录导入：`import "../prismqml/PrismQML/controls/inputs"`。

## 分类

| 分类 | 主要控件 |
|------|---------|
| [按钮](buttons.md) | Button · CustomButton · ToolButton |
| [输入](inputs.md) | LineEdit · ComboBox · Slider · SpinBox · CheckBox · RadioButton · ToggleSwitch · PinInput |
| [卡片](cards.md) | Card · ExampleCard · Expander |
| [数据](data.md) | TableView · ListView · TreeView · Carousel · Avatar |
| [反馈](feedback.md) | ProgressBar · ProgressRing · Toast · InfoBar · Tooltip · Skeleton |
| [弹层](dialogs.md) | Dialog · FlyoutSheet · MaskedDialog · ProgressDialog · PopupWindow |
| [导航](navigation.md) | NavigationBar · NavigationView · TabWidget · Breadcrumb · PipsPager |
| [容器](containers.md) | Layout · ScrollArea · Separator · GroupBox · Drawer · Timeline |
| [图表](charts.md) | ChartView（柱状/折线/饼图等） |
| [图标](icons.md) | Icon（内置 Fluent 图标集） |
| [菜单](menus.md) | Menu · MenuBar |
| [标签](badges.md) | Badge · Tag · Chip |
| [特效](effects.md) | NeoShadow · ShadowedRectangle · ColorOverlay · GaussianBlur |

> 完整清单见各 `controls/` 子目录的 `qmldir`。
