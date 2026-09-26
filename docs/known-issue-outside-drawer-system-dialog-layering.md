# 已知问题：外置抽屉（外侧 `Drawer`）压在系统对话框之上

> 状态：**已修复并验证**（引擎侧改为"宿主正上方"锚点，`0.5.0.24`）
> 发现场景：Kaleidos 悬浮宠物抽屉里点击"上传图片"，弹出的系统文件对话框被抽屉右侧盖住
> 影响面：任何 `mode_outside` 的 `Drawer` + 从抽屉内触发的系统对话框（`FileDialog` / 消息框等）

---

## 一、现象

外侧抽屉打开时，从抽屉内容里打开系统文件对话框，对话框虽然拿到了前台焦点，但抽屉窗口仍然**画在对话框之上**，把对话框右侧整片区域盖住；对话框关闭后一切正常。

关键点：抽屉窗口是宿主的**被拥有窗口**（`transientParent` 已指向宿主，`GW_OWNER` 实测等于宿主 HWND），系统对话框同样被宿主拥有。Windows 的"被拥有窗口始终在拥有者之上"只约束抽屉与宿主的关系，不约束两个同级被拥有窗口之间的先后，所以胜负完全取决于谁最后改过 z 序。

---

## 二、归因结论（已确证）

`WindowHelper.registerWindowFollower(..., above_host=True)` 原先把它翻译成 **`SetWindowPos(follower, HWND_TOP, ...)`**，也就是把抽屉丢到**整个普通窗口带的最顶部**，而不是"宿主正上方"。`_window_follower.py` 里三条几何提交路径都复现同一取值：

- `register()`（首次显露）
- `update_geometry()`（宿主几何/激活/可见性变化，外侧抽屉每帧提交）
- `sync_host_rect()`（宿主移动、缩放过程中的 `WM_MOVING/WM_SIZING/WM_WINDOWPOSCHANGING`）

宿主被系统对话框抢走激活时会触发 `Drawer` 的 `onActiveChanged → _scheduleOutsideHostSync → _updateOutsideWindowGeometry()`，于是抽屉在对话框已经显示之后又被抬到顶部，正好复现截图里的状态。

补充实测（Win32 语义）：`SetWindowPos(w, after)` 把 `w` 放在 `after` 的**下方**（`after` 是"排在 w 前面的窗口"）。因此"宿主正上方"的正确锚点是 `GetWindow(host, GW_HWNDPREV)`（宿主当前的前一个窗口），把抽屉插到它下面即可，永远不越过已经位于宿主之上的窗口。

---

## 三、修复

`prismqml/python/core/_window_follower.py`：

- 新增 `_follower_stack_anchor()`：`above_host=True` 时返回 `GetWindow(host_hwnd, GW_HWNDPREV)`；
  宿主之上没有窗口时返回 `HWND_TOP`（此时窗口带顶部就是宿主正上方）；宿主的前一个窗口已经是该抽屉自身时返回 `None`；
- `insert_after = None` 表示"保持当前层级"，`_set_native_window_geometry()` 据此附加 `SWP_NOZORDER`，避免 `SetWindowPos(hwnd, hwnd)` 这种自引用；
- `above_host=False`（默认）语义不变，仍然是"宿主下方"。

行为影响：外侧抽屉不再抢到整个桌面的最顶层，而是稳定停在宿主正上方；其它应用的窗口、系统对话框、以及宿主上方的瞬态弹层都会继续压在抽屉之上。宿主被用户点击激活时仍由 `activate_window_group()` 把"宿主 + 附属窗口"整组提到最前，交互没有变化。

---

## 四、验证证据

探针脚本（本地临时产物，未提交）：`.artifacts/temp/zorder_visual_probe.py`、`.artifacts/temp/drawer_dialog_layering_probe.py`。

### 1. 单因素层级探针（宿主 + 外侧附属窗口 + 同进程对话框窗口）

`updateWindowFollowerGeometry(host, follower, RIGHT, above_host=True)` 之后：

| 版本 | dialog 相对 follower | follower 相对 host |
|---|---|---|
| 修复前 | **dialog below follower（抽屉盖住对话框）** | follower above host |
| 修复后 | dialog above follower | follower above host |

修复后 `GetWindow(follower, GW_HWNDPREV)` 直接等于对话框窗口 —— 抽屉正好落在对话框与宿主之间。

### 2. 真实系统文件对话框 + 真实 QML 外侧抽屉

探针用 `QQmlApplicationEngine` 起一个宿主窗口 + `PrismQML.Drawer(mode=outside)`，再从抽屉内打开 `QtQuick.Dialogs.FileDialog`，并用 `GetWindow(GW_HWNDPREV)` 链实测 z 序（探针进程需为前台进程，否则系统对话框会进入 topmost 带、`HWND_TOP` 抬升会被前台保护拒绝）：

| 版本 | 打开对话框 | 点击抽屉 | 宿主 resize | 抽屉几何同步 |
|---|---|---|---|---|
| 修复前 | dialog_above_drawer = **false** | false | false | false |
| 修复后 | dialog_above_drawer = true | true | true | true |

两轮 `drawer_above_host` 均为 true。
