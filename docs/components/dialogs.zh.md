# 弹层

对话框、浮层、弹出窗口。

## MessageBox 消息对话框

```qml
import PrismQML as Fluent

Fluent.MessageBox {
    title: "确认"
    content: "确定要执行该操作吗？"
    // 内置确定/取消按钮，文案可用 confirmText / cancelText 自定义
}
```

## 变体

| 控件 | 说明 |
|------|------|
| `OverlayDialogCore` | 无内置主体的全屏遮罩基类；高级自定义弹层可直接在其中声明内容 |
| `DialogBoxCore` | 可定制对话框基类（footer / 主体内容由子类组装） |
| `MaskedDialog` | 带遮罩的模态对话框 |
| `FlyoutSheet` | 浮层面板 |
| `ProgressDialog` | 进度对话框 |
| `ConfirmDialog` | 确认对话框（支持 messageAlignment） |
| `PopupWindowCore` | 通用弹出窗口（菜单/下拉/tooltip 的底层载体） |

## FlyoutSheet 浮层面板

`FlyoutSheet` 使用独立窗口承载可替换内容；自定义主体通过 `contentComponent` 提供，
并可用 `open(target)` 定位到触发控件。`deleteOnClose` 默认为 `true`，关闭时销毁面板；
若需要复用同一实例，设为 `false`。

```qml
Item {
    Component {
        id: flyoutBody
        Item {
            implicitWidth: 320
            implicitHeight: 180
            // Panel body content 面板主体内容
        }
    }
    Fluent.FlyoutSheet {
        contentComponent: flyoutBody
        onAccepted: console.log("已确认")
    }
}
```

`OverlayDialogCore` 统一负责遮罩、事件拦截、开关动画状态和覆盖目标重定向。派生组件只应通过内部 `_prepareOpen()` 钩子恢复自身布局，不应重复实现 `open()` 生命周期。

## 桌面通知

```python
from prismqml.python.runtime.notification import showDesktopNotification
showDesktopNotification(title="提醒", message="你有新消息")
```

## 皮肤适配

新粗野下：所有弹层粗黑边 + 硬阴影（NeoShadow，跟随开合动画的 opacity/scale）；对话框白面黑边。
