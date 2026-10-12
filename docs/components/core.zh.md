# 核心与工具

根模块中的平台能力与辅助 singleton。它们不绘制独立控件，供其他 QML 组件共享行为。

## Touch 触摸能力

`Touch` 根据宿主注入的 `PlatformInfo` 暴露 `isTouch`、`isMobile`、`isCompact` 和
`minTargetSize`。桌面端 `minTargetSize` 为 `0`，因此使用它抬高交互尺寸不会改变桌面布局。

```qml
import PrismQML as Fluent

height: Fluent.Touch.target(Enums.controlSize.inputHeight)
readonly property bool active: Fluent.Touch.feedback(hovered, pressed)
visible: Fluent.Touch.reveal(hovered)
```

方法说明：

- `feedback(hovered, pressed)`：桌面端返回 hover 状态；触摸端以按压状态作为反馈，避免合成
  hover 在松手后残留。
- `reveal(hovered)`：触摸端恒为 `true`，桌面端跟随 `hovered`，用于让触摸设备仍能访问
  hover 才出现的入口。
- `target(desktopSize)`：返回不小于触摸最小目标尺寸的交互尺寸。

触摸端不应依赖 hover tooltip；提示组件会根据 `Touch.isTouch` 关闭这类入口。

## WheelEventUtils 滚轮增量

`WheelEventUtils` 统一处理 Qt 滚轮事件的系统方向设置。`verticalDelta(event)` 和
`horizontalDelta(event)` 在没有有效 `angleDelta` 时返回 `0`，当事件的 `inverted` 为
`true` 时反转对应轴的增量。

```qml
var dy = Fluent.WheelEventUtils.verticalDelta(event)
var dx = Fluent.WheelEventUtils.horizontalDelta(event)
```

## AccessibilityHelper 无障碍辅助

`AccessibilityHelper` 将 `Enums.accessibility` 令牌转换为 Qt `Accessible` 角色，并集中
处理名称和描述文本，避免组件重复维护映射。

```qml
Accessible.role: AccessibilityHelper.roleValue(
    Enums.accessibility.role_button
)
Accessible.name: AccessibilityHelper.resolveName(
    explicitName, visibleText, toolTipText
)
Accessible.description: AccessibilityHelper.describe([
    hintText, shortcutText
])
```

方法说明：

- `roleValue(role)`：返回对应的 Qt 无障碍角色；未知令牌返回 `Accessible.NoRole`。
- `namePart(name)`：从 `主名称|附加信息` 中取出主名称。
- `describe(parts)`：过滤空值并用 `. ` 拼接描述片段。
- `resolveName(explicitName, visibleText, toolTipText)`：按显式名称、可见文本、提示文本
  的顺序选择第一个非空名称。
