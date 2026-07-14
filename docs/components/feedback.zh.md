# 反馈

进度、通知、提示、骨架屏等反馈控件。

## 进度

```qml
import PrismQML as Fluent

Fluent.ProgressBar { value: 65 }      // 进度条
Fluent.ProgressRing { value: 75 }     // 进度环
```

`Progress` 支持 `type_bar` / `type_bar_filled` / `type_ring`，以及不定态（indeterminate）、暂停/错误状态。

## Toast 轻提示

```python
from prismqml import showDesktopSuccess, showDesktopError

showDesktopSuccess("操作成功")
showDesktopError("出错了")
```

## InfoBar 信息条

```qml
Fluent.InfoBar {
    severity: "success"     // info / success / warning / error
    title: "操作成功"
    message: "信息条内容"
    duration: 0             // 0 = 常驻不自动关闭
}
```

## Tooltip 悬停提示

所有继承 `Widget` 的控件可通过 `toolTipText` 添加悬停提示，并用
`toolTipPosition` 选择 `Enums.position.top/right/bottom/left`。普通控件默认显示在上方；
标题或标签旁的 `HintIcon` 默认显示在右侧，使用统一的水平、垂直内边距。

```qml
Fluent.HintIcon {
    toolTipText: "这里显示补充说明"
    // 默认值；需要时也可改为 top / bottom / left
    toolTipPosition: Fluent.Enums.position.right
}
```

## Skeleton 骨架屏

加载占位，支持 `shape_rounded` / `shape_rect` / `shape_circle`。

## 皮肤适配

新粗野下：进度条白轨道黑边 + 橙填充；InfoBar 白底黑边硬阴影 + 高饱和语义色条；Tooltip 黑边硬阴影。语义色（成功绿/危险红/警告琥珀）在 neo 下用高饱和版本。
