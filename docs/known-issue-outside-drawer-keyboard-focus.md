# 已知问题：外侧抽屉（`mode_outside`）里的输入控件无法获得键盘焦点

> 状态：**已修复**（引擎侧改窗口类型，`flags` 由 Tool 改为 `Qt.Window`）
> 发现场景：Kaleidos 语音房控制面板（`Drawer(mode_outside)`）标题行里的成员搜索框，点击后不进焦、无法输入
> 影响面：任何 `mode_outside` 的 `Drawer` 内容里的键盘输入控件（`LineEdit` / `TextEdit` / `ComboBox` 搜索、快捷键编辑器等）

---

## 一、现象

外侧抽屉打开后，抽屉里的单行输入框（例如 `Fluent.LineEdit { inputType: type_search }`）：

- 鼠标点击**没有任何反应**：不出现聚焦边框，placeholder 不消失；
- 键盘输入**完全丢失**（字符进不到输入框）；
- 用 `forceActiveFocus()` 也无效，`textInput.activeFocus` 始终为 `false`。

同一个 `LineEdit` 放在普通窗口里（甚至放在同一进程的另一个普通窗口里）一切正常。

---

## 二、归因结论（已确证）

**本次真实 Windows 验收中，问题定位为外侧抽屉原生 HWND 无法取得激活焦点。**

`DrawerOutsideWindow.qml` 原先把窗口声明为 `Qt.Tool | Qt.FramelessWindowHint`。Windows 平台下
Qt 会为 Tool 窗口加上 `WS_EX_TOOLWINDOW` 扩展样式；在该 Qt/Windows 配置下观察到它无法被激活，于是：

- `QWindow::active` / `QGuiApplication::focusWindow()` 永远拿不到该窗口；
- QML 场景图里没有"当前焦点窗口"，`Item::forceActiveFocus()` 全部变成空操作；
- 窗口内**任何** `TextInput`（含 PrismQML `LineEdit` 内部的）都无法取得 `activeFocus`，键盘事件也无处投递。

### 证据链（真实 Windows 平台，单因素）

同一个外侧抽屉窗口，只切换窗口类型：

| 窗口类型 | flags | exstyle | TOOLWINDOW | active | app focusWindow | 点击输入框后 `activeFocus` | 键入 |
|---|---|---|---|---|---|---|---|
| Tool（修复前） | 2059 | `0x00080080` | **是** | false | `null` | false | 丢失 |
| `Qt.Window`（修复后） | 2049 | `0x00080000` | 否 | true | `outsideDrawerWindow` | **true** | 正常 |

隔离探针（`QQuickWindow` 直建，同一进程，仅改 flags）：

| flags | `activeFocusItem()` | 子 `TextInput` 的 `forceActiveFocus()` |
|---|---|---|
| `Tool` / `Tool\|Window` / `Tool\|Frameless` / `Tool\|Window\|Frameless` | 恒为 `None` | **无效** |
| `Window\|Frameless` | 正常 | 生效 |

分水岭就是窗口类型里的 Tool；`FramelessWindowHint`、`StayOnTop`、`transparent` 都不影响。

### 业务侧端到端验证

Kaleidos `ChatPanel` 真实路径（点开语音工作区 → 外侧抽屉 → 成员搜索框）：

```
修复前: after click -> activeFocusItem: None | ti.activeFocus: False | field.focused: False
        field.text after typing: ''

修复后: appFocusWindow=outsideDrawerWindow | ti.activeFocus: True
        field.text after typing: 'JELLY'
        workspace.memberSearchText: JELLY      ← 过滤链路真的被驱动
        count tag: 0 位成员
        field.text after backspace: 'JELL'
```

---

## 三、修复

`prismqml/PrismQML/controls/containers/Drawer/_internal/DrawerOutsideWindow.qml`：

```qml
// 修复前
flags: Qt.Tool | Qt.FramelessWindowHint
// 修复后
flags: Qt.Window | Qt.FramelessWindowHint
```

窗口"被宿主拥有"的层级语义本来就由 `transientParent: control._hostWindow` 承担（原生 `GW_OWNER`
链路），窗口类型不必也不该用 Tool 表达，因此本次改动没有丢掉任何抽屉层级行为：

- 抽屉仍然是宿主的被拥有窗口，仍与宿主同属一个 owner 组，模态/系统对话框层级不改；
- 原生 z 序仍由 `WindowHelper.registerWindowFollower(..., above_host=true)` 逐帧提交，与窗口类型无关；
- owner 关系仍保持抽屉与宿主的归属；任务栏 / Alt-Tab 是否出现必须在目标 Windows Shell 环境单独确认，不能由本合同测试推导。

同时**没有**改成"显露时主动 `requestActivate()`"：抢焦点必须由用户点击触发，避免打开抽屉就打断
宿主窗口的输入。

源码合同：`tests/qml/test_drawer_outside_native.py::test_outside_window_uses_a_window_type_that_can_take_keyboard_focus`
真实 Windows 验收：`tests/qml/test_drawer_outside_focus.py::test_outside_drawer_text_input_accepts_focus_and_keyboard_input_on_windows`
（锁定窗口类型，并继续禁止在显露阶段主动请求激活）。

---

## 四、回归验证

```
tests/qml/test_drawer_outside_native.py
tests/qml/test_drawer_conventions.py
tests/qml/test_gallery_container_drawers.py
→ 22 passed
```

（几何与生命周期测试经 `scripts/test_process.py --qt-platform offscreen` 启动；窗口类型本身属于原生语义，
焦点行为使用显式可视 Windows 验收入口完成。）

---

## 五、排查提示

- **不要用 `QT_QPA_PLATFORM=offscreen` 验收本问题**：offscreen 下窗口的激活/焦点对象语义不真实，
  修复前后都测不出差别，必须在真实桌面平台观察 `active` / `activeFocusItem()` / 实际键入。
- 判据优先级：`QGuiApplication.focusWindow()` + `activeFocusItem()` + **实际键入后的文本** >
  `textInput.activeFocus`（在不可激活的窗口上它可能被上一轮残留为 `true`，不代表键盘事件真的进得来）。
- 定位"某个输入控件点不动"时，先读该窗口的 Win32 `GWL_EXSTYLE`：出现 `WS_EX_TOOLWINDOW` 就基本
  可以判定为本文这一类问题。
- 同类已知坑：`docs/known-issue-qt-tool-popup-positioning.md`（Tool 窗口上的坐标映射退化）。
  两者都源自 Tool 窗口类型在 Windows 上的原生语义缺失，但症状与判据不同，不要混为一谈。
