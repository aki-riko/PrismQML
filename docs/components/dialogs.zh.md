# 弹层

对话框、浮层、弹出窗口。

## Dialog 对话框

```qml
import PrismQML as Fluent

Fluent.Dialog {
    title: "确认"
    // 内容 + 操作按钮
}
```

## 变体

| 控件 | 说明 |
|------|------|
| `OverlayDialogCore` | 无内置主体的全屏遮罩基类；高级自定义弹层可直接在其中声明内容 |
| `DialogBox` | 标准对话框（标题 + 内容 + 操作区） |
| `MaskedDialog` | 带遮罩的模态对话框 |
| `FlyoutSheet` | 浮层面板 |
| `ProgressDialog` | 进度对话框 |
| `ConfirmDialog` | 确认对话框（支持 messageAlignment） |
| `PopupWindow` | 通用弹出窗口（菜单/下拉/tooltip 的底层载体） |

`OverlayDialogCore` 统一负责遮罩、事件拦截、开关动画状态和覆盖目标重定向。派生组件只应通过内部 `_prepareOpen()` 钩子恢复自身布局，不应重复实现 `open()` 生命周期。

## 桌面通知

```python
from prismqml import showDesktopNotification
showDesktopNotification(title="提醒", message="你有新消息")
```

## 皮肤适配

新粗野下：所有弹层粗黑边 + 硬阴影（NeoShadow，跟随开合动画的 opacity/scale）；对话框白面黑边。
