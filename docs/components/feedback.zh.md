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

QML 桌面通知支持在显示前原子传入 `options`，避免通知已经定位后再追加按钮或切换布局：

```qml
Component {
    id: openFolderAction
    Fluent.Button {
        text: "打开目录"
        width: parent ? parent.width : implicitWidth
    }
}

Fluent.Button {
    text: "显示导出通知"
    onClicked: Fluent.NotificationManager.desktop.success(
        "导出成功",
        "00:14\nC:/recordings/clip.mp4",
        0,
        Fluent.Enums.notification.posBottomRight,
        {
            "orient": Qt.Vertical,
            "customContent": openFolderAction,
            "closable": true,
            "screen": Window.window.screen
        }
    )
}
```

Toast 与 InfoBar 的通用选项包括 `orient`、`customContent`、`closable`、
`feature`、`progress`、`completeDuration`、`backgroundColorLight` 和
`backgroundColorDark`；桌面 InfoBar 还支持 `icon`、`radius`。`screen` 用于选择目标显示器。
窗口会按该显示器的 `availableGeometry` 定位，自动避开任务栏，并在内容尺寸或工作区变化后重新排布。

桌面通知支持完整九宫格位置，按行从左到右依次为：
`posTopLeft` / `posTop` / `posTopRight`、`posLeft` / `posCenter` / `posRight`、
`posBottomLeft` / `posBottom` / `posBottomRight`。贴边位置与工作区边缘保持 8 个逻辑像素，
中间行和中间列则分别按工作区垂直、水平中心定位。Python 的 `Position` 枚举使用同一顺序。

Python helper 也支持同一组可序列化选项（QML `Component` 类型的 `customContent` 除外）：

```python
from PySide6.QtCore import Qt
from prismqml import showDesktopSuccess

showDesktopSuccess(
    "导出成功",
    "00:14\nC:/recordings/clip.mp4",
    duration=0,
    options={"orient": Qt.Vertical, "closable": False},
)
```

### 贴着宿主窗口外侧

InfoBar/Toast 的最后一个可选参数是通知模式。传入
`Enums.notification.mode_window_outside` 后，`parent` 所属窗口会成为宿主，通知在
宿主外沿创建为独立窗口：

```qml
Fluent.Button {
    text: "在窗口左上外侧显示 Toast"
    onClicked: Fluent.NotificationManager.toast.info(
        Window.window,
        "提示",
        "贴着窗口左侧顶部出现",
        0,
        Fluent.Enums.notification.posTopLeft,
        Fluent.Enums.notification.mode_window_outside
    )
}
```

`posTopLeft` / `posTopRight` 从宿主侧边顶部向下堆叠，`posLeft` / `posRight` 从垂直中心
向下堆叠，`posBottomLeft` / `posBottomRight` 从底部向上堆叠；`posTop` 从上沿中间向上，
`posBottom` 从下沿中间向下。`posCenter` 没有对应外沿，会被拒绝。宿主窗口移动、缩放、
隐藏或最小化时，外侧通知会同步或关闭；同边窗口外 Drawer 的占位会自动计入间距。

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
