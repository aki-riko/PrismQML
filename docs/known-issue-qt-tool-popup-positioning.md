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
| `prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPositionHelper.qml` | `calculatePosition(targetGlobalPosition)` / `calculateArrowPosition()`，坐标改由 `TipPopup` 在 `Item` 上下文解析后传入 |
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

使用本文第三节同一组 `Qt.Tool` 输入，在独立 Windows 进程中验证：首次显示和移动锚点后的 `dx=dy=0`；修复前首次显示为 `dx=-170,dy=-504`。定向合同测试 `tests/qml/test_popup_position_tracking.py` 与 `tests/tooling/test_qml_architecture_part3.py` 当前均通过（38 passed）。

**offscreen 平台不能验收本问题**：`QT_QPA_PLATFORM=offscreen` 下该偏差**恒定存在**（修复前后都是 `dx=-170,dy=-504`），因为该平台没有真实的 `Qt.Tool` 原生窗口语义。只有在真实桌面平台（`--qt-platform windows` 或 `QT_QPA_PLATFORM=windows`）才能观察到修复效果。

---

## 十、关联缺陷：预热（prewarm）切断弹层的位置绑定

排查定位问题时另发现一个**独立**缺陷，症状同样是"弹层跑到错误位置"，但成因、触发条件、影响面都不同，**不要与本问题混为一谈**。

### 症状

弹层不是偏一点，而是**永久停在屏幕左上角 `(0,0)`**（实测 `dx=-1240, dy=-582`）。Gallery 的 TeachingTip 就命中这一条：用户必须先把鼠标滑到按钮上再点击，而**首次交互是悬停**正是触发条件。

### 触发条件（精确）

1. 调用方在 `show()` **之前**先触发过一次 `prewarm()`（例如 `TipPopup` 自带的三条 hover 连接：`hovered` / `containsMouse` / `activeFocus`）；
2. 且这次 `prewarm()` 是该实例的**第一次**（`_prewarmed` 为 `false`）。

`prewarm()` 有守卫 `if (!target || (_prewarmed && ...)) return`，而 `show()` 会把 `_prewarmed` 置 `true`，所以**每个实例只会坏一次**，坏的那次正好是用户第一次看到它的那次。因此"手动调 `show()` 的探针"**测不出来**——必须先悬停。

### 根因

`_prewarmWindow()` 为了把窗口停到屏幕外避免闪现，直接给窗口属性赋值：

```js
var savedX = window.x          // 读到的是 _animX 的当前值（首次为 0）
window.x = _prewarmCoordinate  // -32000，直接赋值 → 移除声明式绑定
window.show(); window.hide()
window.x = savedX              // 写回值 → 绑定不会回来，窗口 x 从此固定
```

而 `TipPopupWindow` 的位置**完全依赖绑定**：

```qml
x: popupControl._animX
y: popupControl._animY
```

QML 中对该属性做任何命令式赋值都会**移除绑定**。绑定一旦被移除，此后 `show()` 里再怎么更新 `_animX/_animY`，窗口都不再跟随，于是停在 `prewarm` 时的值 `(0,0)`。

### 证据

真实桌面平台、同一份 QML，先悬停再显示（`_animX/_animY` 已是正确值，窗口却不动）：

```
after-hover   : prewarmed=True popup=(0,0) animX=0.0 animY=0.0
after-show    : popup=(0,0)   animX=1240.0 animY=582.0   ← 值对了，窗口不跟随
nohover       : popup=(1240,582)                          ← 正确
```

该缺陷自 `e690e49c0`（2026-08-06，`perf: 延迟创建 TipPopup 原生窗口`）引入，与本文档第一至九节的定位修复**无关**：在定位修复前后逐位相同的 `(0,0)`。

### 修复

`prewarm()` 里对**主弹层**改用绑定恢复：

```js
_prewarmWindow(_popupWindow)
_popupWindow.x = Qt.binding(function() { return control._animX })
_popupWindow.y = Qt.binding(function() { return control._animY })
if (_arrowWindow) _prewarmWindow(_arrowWindow)
```

箭头窗口（`TipPopup` 的 `arrowWindowLoader`）没有 `x/y` 绑定——它的位置由 `showAt(position)` 与 `_applyTrackedPosition()` 直接赋值驱动——所以**必须继续走原来的直接恢复**，不能被顺手改成绑定。`_prewarmWindow()` 因此保持原样，只服务箭头窗口。

合同测试：`test_tip_popup_prewarm_restores_position_as_bindings`（同时锁定箭头窗口不得被改成绑定）。

### 排查提示

如果再次遇到"弹层位置不对"，先分清是哪一类：

| 判别项 | 本问题（Qt.Tool 映射） | 预热切断绑定 |
|---|---|---|
| 偏差量 | 水平 −170、垂直 −504（= 窗口高度） | 直接落在 `(0,0)` |
| 触发窗口类型 | 仅 `Qt.Tool` 宿主 | 任意宿主 |
| 触发条件 | 无（显示即错） | 首次交互是悬停 |
| 手动调 `show()` 的探针 | 能复现 | **测不出来**，必须先悬停 |
