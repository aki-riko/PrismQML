# 控件总览

PrismQML 提供 180+ QML 类型，覆盖按钮、输入、数据、反馈、弹层、导航等常见场景。
**所有控件自动适配当前[皮肤](../guide/skins.md)**，无需为 Fluent / 新粗野 /
复古票据 / 新拟态分别编写界面。

## 导入方式

大多数控件通过顶层模块导入：

```qml
import PrismQML as Fluent

Fluent.Button { text: "确定" }
Fluent.Card { /* ... */ }
```

!!! note "顶层组件"
    `ComboBox`、`Slider` 已在顶层 `PrismQML` 模块注册。通过模块别名使用
    `Fluent.ComboBox` / `Fluent.Slider`，无需导入 QtQuick.Controls 或内部目录。

## 分类

| 分类 | 主要控件 |
|------|---------|
| [按钮](buttons.md) | Button · CustomButtonCore · CloseButton |
| [输入](inputs.md) | LineEdit · ComboBox · Slider · SpinBox · CheckBox · RadioButton · ToggleSwitch · PinInput |
| [卡片](cards.md) | Card · ExampleCard · Expander |
| [数据](data.md) | TableView · ListView · TreeView · Carousel · Avatar |
| [反馈](feedback.md) | ProgressBar · ProgressRing · Toast · InfoBar · ToolTip · Skeleton |
| [弹层](dialogs.md) | MessageBox · ConfirmDialog · MaskedDialog · FlyoutSheet · ProgressDialog · PopupWindowCore |
| [导航](navigation.md) | NavigationBar · NavigationView · TabWidget · Breadcrumb · PipsPager |
| [容器](containers.md) | FlowLayout · GridLayout · HBoxLayout · VBoxLayout · ScrollArea · Separator · GroupBox · Drawer · Timeline |
| [图表](charts.md) | ChartView（柱状/折线/饼图等） |
| [图标](icons.md) | Icon（内置 Fluent 图标集） |
| [菜单](menus.md) | ContextMenu · MenuBar |
| [标签](badges.md) | Badge · Tag · Chip |
| [特效](effects.md) | Shadow · ShadowedRectangle · ColorOverlay · GaussianBlur |
| 认证 / 聊天 / 设置 | LoginWindow · ChatBubble · ChatMessageList · SettingsCard 等（暂无独立用法页，完整清单见[速查表](list.md)） |

> 完整清单见各 `controls/` 子目录的 `qmldir`。
