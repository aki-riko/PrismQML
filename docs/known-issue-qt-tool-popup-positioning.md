# 已知问题：`Qt.Tool` 窗口上 `TipPopup` 定位整体偏移

> 状态：**已修复并验证**（引擎侧采用方向 A；保留本文作为回归证据与排查记录）
> 发现场景：ConfigPilot 的桌宠悬浮窗（`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`）里把余额气泡改成 `TeachingTip`
> 版本：PrismQML `0.4.2.26`（提交 `05babada7` 附近）

---

## 一、现象

在带 `Qt.Tool` 标志的窗口内，把一个 `TipPopup` / `TeachingTip` / `Flyout` 锚到**窗口内的局部 Item**上时，弹层整体落位偏移：

- 水平偏 `−170px`（与窗口宽度、target 位置相关）
- 垂直偏 `−504px`（**恰好等于窗口高度**）

在**普通窗口**（无 `Tool`）下同一段代码落位**完全正确**。

### 影响面

任何"把弹层锚在 Tool 窗口内局部 Item 上"的调用都会中招。只有 target 恰好**覆盖整个窗口**时看不出来（那时它的坐标数值与窗口本身相同）。

---

## 二、归因结论（已确证）

**不是调用方的用法错误，也不是 `calculatePosition()` 公式错误，而是 Qt 在该窗口上的坐标映射退化了。**

`target.mapToGlobal(0, 0)` 在 `Qt.Tool` 窗口上返回的坐标不等于 target 的真实全局位置，表现为：

- **x**：塌成窗口原点（同时 target 的宽度参与计算时等效于 0）
- **y**：少掉一个**窗口高度**

### 证据链（单因素剥离，每场景独立进程）

| 场景 | 窗口标志 | dx | dy |
|---|---|---|---|
| 0 | 普通窗口 | **+0** | **+0** |
| 1 | `FramelessWindowHint` | **+0** | **+0** |
| 2 | `FramelessWindowHint \| WindowStaysOnTopHint` | **+0** | **+0** |
| 3 | `FramelessWindowHint \| WindowStaysOnTopHint \| Qt.Tool` | **−170** | **−504** |
| 4 | 同 3，另加 `color: transparent` | −170 | −504 |

**分水岭是 `Qt.Tool`**：`Frameless`、`StayOnTop`、`transparent` 都不影响。

窗口尺寸 `340x504`，锚点全局坐标 `(1208, 964)`，弹层 `324x84`，按引擎公式期望 `(1208, 868)`：

```
场景 2 实测 (1208, 868)  → dx=+0   dy=+0
场景 3 实测 (1038, 364)  → dx=-170 dy=-504
```

反推场景 3：`1038 = 1200(窗口x) − 162(弹层宽/2)`、`targetPos.y = 460 = 964 − 504`。

### 引擎内部中间量（同一探针在两场景下取值相同且都错）

```
场景0 / 场景3 均为：local=(0,4)  win=(1200,600)  global=(1200,604)  calc=(1200,508)
正确值应为        ：mapToItem(null)=(8,364)     mapToGlobal=(1208,964)
```

注意 `local` 拿到的不是场景坐标（应为 `(8,364)`），而是 `(0, target.y)` 形态的无效值。

---

## 三、最小复现

### 1. 复现用 QML（单文件，改 `flags` 即可切换场景）

```qml
import QtQuick
import QtQuick.Window
import PrismQML as Fluent

Window {
    id: win
    width: 340; height: 504
    x: 1200; y: 600
    visible: true
    color: "#202020"
    // ↓ 场景 3：加上 Qt.Tool 即复现；注释掉则定位正确
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool

    Item {
        id: panel
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
        height: 144

        Item {
            id: anchor
            objectName: "theAnchor"
            anchors.horizontalCenter: parent.horizontalCenter
            y: 4
            width: 324
            height: 1

            Fluent.TeachingTip {
                id: tip
                objectName: "tip"
                target: anchor
                anchorPosition: Fluent.Enums.teachingTip.anchor_bottom
                viewWidth: 324
                viewHeight: 84
                duration: Fluent.Enums.duration.persistent
                Fluent.Label { text: "probe" }
            }
        }
    }
}
```

### 2. 驱动脚本

```python
# 期望值按 TipPositionHelper.calculatePosition() 的 anchor_bottom 分支计算:
#   x = targetGlobal.x + target.width/2 - popup.width/2
#   y = targetGlobal.y - popup.height - (tailSize + 4)      # tailSize = 8
import os, sys
os.environ["QML_DISABLE_DISK_CACHE"] = "1"
from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

app = QGuiApplication(sys.argv)
from prismqml import register_types           # 或复用调用方的引擎装配
engine = QQmlEngine(); register_types(engine)

component = QQmlComponent(engine)
component.setData(open("repro.qml", encoding="utf-8").read().encode("utf-8"), QUrl())
root = component.create()
tip = root.findChild(QObject, "tip")
anchor = root.findChild(QQuickItem, "theAnchor")
tip.metaObject().invokeMethod(tip, "show")
QTest.qWait(900)

popup = tip.property("_popupWindow")
g = anchor.mapToGlobal(QPointF(0, 0))
expect_x = g.x() + anchor.width() / 2 - popup.width() / 2
expect_y = g.y() - popup.height() - 12
print("实测=(%d,%d) 期望=(%.0f,%.0f) dx=%+.0f dy=%+.0f"
      % (popup.x(), popup.y(), expect_x, expect_y,
         popup.x() - expect_x, popup.y() - expect_y))
# 场景 3 输出: 实测=(1038,364) 期望=(1208,868) dx=-170 dy=-504
```

---

## 四、已排除的可能（不要重复排查）

| 假设 | 排除依据 |
|---|---|
| `calculatePosition()` 公式写错 | 普通窗口场景 `dx=dy=0`，同一份公式 |
| `PopupPositionTracker` 覆盖了位置 | 它复用同一个 `calculatePosition()`；给它加上"尺寸变化也重算"的加固后偏差**一点没变** |
| QML 磁盘缓存导致改动未生效 | 设 `QML_DISABLE_DISK_CACHE=1` 后偏差**完全不变** |
| `transparent` / `Frameless` / `StayOnTop` 影响 | 逐项剥离，均 `dx=dy=0` |
| target 未完成布局（尺寸为 0） | 探针显示 `posHelper.target.width=324`、全局 `(1238,800)`，输入本身正确 |
| 换成 `mapToItem(targetWindow.contentItem, ...)` 可绕开 | 实测仍错 |
| 换成 `mapToItem(null, ...)` 取场景坐标可绕开 | 实测仍错 |
| 父链（面板锚定窗口底部）导致 | 最简场景（anchor 直接是窗口子项，无中间面板）同样复现 |

---

## 五、修复方向与取舍

### 方向 A：把坐标解析从 `QtObject` 移到 `Item` 上下文（**已实施**）

`TipPositionHelper` 是 `QtObject`。实测在**正确的对象上下文**里对同一个 anchor 调 `mapToItem(null)` 得到的是**正确值 `(8,364)`**，而 helper 内部拿到的是无效值 `(0,4)`。

因此已把 `_resolveTargetGlobalPosition()` 挪进 `TipPopup`（`Item`）里算，再把结果传给 helper；同时先显示透明原生表面，再解析坐标，绕开了弹层创建前的 Qt.Tool 映射退化。

另一条相关观察：通过 `var` 类型的 `target` 访问 `target.Window.window` 这类 attached property，在 `QtObject` 里并不可靠（实测取不到窗口），这也支持"挪到 Item 上下文"的方向。

### 方向 B：不再依赖跨对象映射，由调用方提供锚点全局矩形（未采用）

给 `TipPopup` 增加可选属性（如 `anchorGlobalRect`），由调用方在自己的上下文里算好并传入。彻底绕开引擎内部的映射调用。

### 方向 C：在 `Qt.Tool` 上加一个专用修正（未采用）

在 `mapToGlobal` 结果上按"窗口高度/半宽"补偿。**不推荐**：补偿量依赖窗口几何，属于把缺陷固化。

---

## 六、业务侧绕法（**已验证有效**）

**去掉 `Qt.Tool`**：用 `Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint` 组合，实测 `dx=dy=0`。

需要真机确认的副作用：
- 是否出现在任务栏 / Alt-Tab；
- 是否抢焦点（可评估 `Qt.WindowDoesNotTransferFocus`、`Qt.WindowDoesNotAcceptFocus` 等标志）。

ConfigPilot 侧当时的折中（**已回滚，未采用**）是保留 `Qt.Tool` 并给锚点加 `anchors.horizontalCenterOffset: panelWidth/2` 抵消水平偏差——**只能补水平、补不了那个"窗口高度"的垂直偏差，因此判定不可用**。

---

## 七、排查方法学（避免重复踩的坑）

这次排查有两轮错误结论都源于**测量方法**，不是被测代码：

1. **不要在同进程内连续创建多个顶层窗口做对照**：会让坐标互相污染，出现"同一场景时对时错"。**每个场景独立进程**才稳。
2. **不要把 `mapToScene`（场景坐标）与 `popup.x/y`（屏幕坐标）直接相减**：`sprite.mapToScene()` 与 `popup.y` 属于不同坐标空间。
3. **不要用 PySide 的 `QObject.children()` / `findChild()` 判断 QML 父子关系**：QML 里 `Item.parent`（visual parent）与 `QObject::parent` 可以不同，据此会得出"子项没被 reparent"的假象（`default property alias x: inner.data` 实际是正常工作的）。
4. **判据优先级**：真实渲染截图 > 属性回读（QML 侧算、Python 侧读）> Python 侧对象遍历。
5. 用 `QTest.qWait` 而不是裸 `processEvents` 驱动 QML 动画（offscreen 平台后者不推进动画）。

---

## 八、相关代码位置

| 文件 | 作用 |
|---|---|
| `prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPositionHelper.qml` | `calculatePosition()` / `calculateArrowPosition()`，目前用 `target.mapToGlobal(0,0)` |
| `prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml` | `posHelper` 装配、`_targetWindow`、`show()` / `_applyTrackedPosition()` |
| `prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPopupWindow.qml` | 原生弹层窗口（`x: popupControl._animX`） |
| `prismqml/PrismQML/controls/utils/_internal/PopupPositionTracker.qml` | 逐帧跟随，`_updatePosition()` 内也用 `target.mapToGlobal(0,0)` |

现有合同测试：`tests/qml/test_popup_position_tracking.py`、`tests/tooling/test_qml_architecture_part3.py`（修改上述文件后至少跑这两个）。

---

## 九、关联背景

ConfigPilot 想把桌宠余额气泡（原为内联自绘）换成 `TeachingTip` 以获得框架一致的视觉与富内容能力。为此已先完成两项前置：

- `TipPopup` 支持声明式自定义内容（`default property alias contentData` + `TipContentMover` 显式 reparent）—— **已完成并验证**；
- `TipPopup.viewWidth/viewHeight` 公开可配（默认值保持历史行为）—— **已完成并验证**。

定位问题已在引擎侧修复。ConfigPilot 侧的改造 patch 可在完成真机副作用确认后继续应用。

### 修复验证

使用本文第三节同一组 `Qt.Tool` 输入，在独立 Windows 进程中验证：首次显示和移动锚点后的 `dx=dy=0`；修复前首次显示为 `dx=-170,dy=-504`。定向合同测试 `tests/qml/test_popup_position_tracking.py` 与 `tests/tooling/test_qml_architecture_part3.py` 当前均通过（37 passed）。
