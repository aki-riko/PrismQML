# 平滑滚动：视图重测内容不再取消越界回弹

> 影响版本：`0.5.0.33` → `0.5.0.34`
> 缺陷形态：列表（尤其变高 delegate 的聊天/消息列表）滚到边界后继续滚滚轮，
> 不是「越界一段再弹回」，而是**几乎不动、直接钉在边界**。

---

## 1. 缺陷与根因

`SmoothScrollHelper` 的滚轮越界路径本身是对的：逐帧把 `contentY` 写成越界值，
Qt 也确实不夹紧程序化写入（`StopAtBounds` / `DragAndOvershootBounds` 两种行为都实测过）。

问题出在**视图重新测量内容**的那一刻：

1. 滚轮进入外移腿，`contentY` 正常写到越界（例如 `-46`）；
2. ListView 复用 delegate 后重测，`contentHeight` 抖动几像素，Qt 重新布局并
   **自行把 `contentY` 写回边界**；
3. `SmoothScrollOvershootGuard.isRevoked()` 把这次写入判成「视图夹掉了我们的越界」，
   于是 `interruptOutwardLeg(current, true)`：
   * 立即把动画值钉回边界（`_syncing = true` → `setImmediate`，无动画）；
   * `revokedBoundary = outwardBoundary`，**本输入串内该边界不再外移**；
4. 连续滚轮的空闲间隔够不到 `Enums.scroll.input_burst_gap`（120ms），边界一直不解锁。

即：**引擎把「视图自身的重测量」误判成「视图拒绝了我们的越界」**。

真实 Kaleidos `ChatPanel` 实测（修复前）：越界只有 3 帧、峰值 7px，`revoked = -1`。

---

## 2. 修复

在 `SmoothScrollOvershootGuard` 中按视图自己声明的越界策略分流：

```qml
function allowsOvershoot() {
    if (!scrollHelper.target
            || scrollHelper.target.boundsBehavior === undefined) return false
    return scrollHelper.target.boundsBehavior !== Flickable.StopAtBounds
}
```

* **非 `StopAtBounds` 策略（声明允许某类越界）**：视图重测写回对应边界时重锚当前外移腿，
  把动画起点和目标一起相对新边界调整，并逐帧限制在 `_maxOvershoot` 范围内；连续输入仍由原
  bounce timer 管理，不会重开一条外移腿。
* **`StopAtBounds`（禁止越界）**：写入被夹掉就是拒绝，**保留原严格撤销语义**。
  `TextEditCore`、基础 `Flickable`、`TreeWidget`、`SelectorBar`、`TabBar` 和
  `ChatMessageList` 等不受影响。

这个分界不是启发式猜测：`boundsBehavior` 是视图对越界的显式声明，`HorizontalScrollMixin`
本来就会为了越界把 `StopAtBounds` 主动改成 `DragAndOvershootBounds`，本规则与该既有设计一致。

---

## 3. 覆盖范围

`SmoothScrollHelper` 是唯一滚动实现，因此所有「声明允许越界」的滚动面一次性受益：

| 组件 | 目标 boundsBehavior | 结果 |
|------|--------------------|------|
| `Fluent.ListView` → `DataWidgetContent` | DragAndOvershootBounds | 受益 |
| `Fluent.ChatMessageList` → `ChatMessageViewport` | StopAtBounds | 严格撤销，不变 |
| `Fluent.ScrollArea`（Default/List/Grid） | 继承 Qt 默认（DragAndOvershoot） | 受益 |
| `Fluent.ListWidget` | DragAndOvershootBounds | 受益 |
| `TimelineCore` | DragAndOvershootBounds + 视觉超出层 | 受益（原本已免疫） |
| `HorizontalScrollMixin`（横向轴） | 强制 DragAndOvershootBounds | 受益 |
| `containers/Flickable` | StopAtBounds | 严格撤销，不变 |
| `TextEditCore` / `TreeWidget` / `SelectorBar` / `TabBar` | StopAtBounds | 严格撤销，不变 |

Kaleidos `ChatPanel` 使用 `Fluent.ListView`（`DataWidgetContent`），不使用 PrismQML 的
`ChatMessageList`；其 91px 真实滚轮结果验证的是 `DataWidgetContent` 的允许越界路径。

---

## 4. 验证

### 4.1 引擎门禁

```powershell
cd D:\PrismQML\PrismQML
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 1800 -- `
  .\.venv\Scripts\python.exe scripts\run_test_shards.py --full-suite --timeout 1200 --supervisor-timeout 1500
```

结果：完整分片 **4223 passed, 2 skipped, 0 failed**（22 个分片）；QML probe **194 OK / 0 错误 / 7 required 跳过**；headless CTest **10/10**。

### 4.2 测试判据修正（重要）

`test_scroll_area_wheel_keeps_one_bounce_while_bounds_move` 原判据统计「越界期间的方向反转」，
而该目标的 Flickable 是 `DragAndOvershootBounds`（Qt 默认），修复后视图每次重测写回边界都会
被计成一次反转 —— 度量的是视图自己的写入，不是抖动。这与 Gitora 当年 `test_timeline_conventions`
踩过的假阳是同一类问题。

现判据改为直接度量契约本身：

* 连续垂直滚轮期间 `_isOutwardBounceV` 只从 `false` 进入 `true` 一次；
* 垂直顶部/底部与水平左侧/右侧目标在 `DragOverBounds`、`OvershootBounds`、`DragAndOvershootBounds` 下，边界大幅缩短后重锚值及后续每帧仍不超过新边界加 `_maxOvershoot`；
* 峰值不超过 `_maxOvershoot`；
* 支持越界的目标 `revokedBoundary == 0`（不得因自身重测被撤销边界）；
* 滚轮停止后收敛回边界。

列表插入导致 `originY/originX` 变化的专项场景尚未加入这组边界缩短测试。

新增 `test_stop_at_bounds_view_revokes_overshoot_when_bounds_move`：在真正的
`StopAtBounds` 目标上锁死严格撤销契约（边界内移后必须撤销，同向输入不得重新发布）。

### 4.3 下游实测

Kaleidos `ChatPanel` 的 `Fluent.ListView` 真实组件（真滚轮事件、真 delegate 回收抖动）：

| 引擎状态 | 越界峰值 | 形态 | `revokedBoundary` |
|---------|---------|------|-------------------|
| `0.5.0.32` | 4px / 2 帧 | 直接钉在边界 | `-1` |
| `0.5.0.34`（发布版） | 7px / 19 帧 | 锯齿：涨到 7px 就被下一次重测重置回边界 | `0` |
| `0.5.0.35`（本次修复） | **64px / 53 帧** | 连续外移后平滑返回边缘 | `0` |

即 `0.5.0.34` 只修掉了「边界被永久撤销」，位移仍长不出来；根因见第 6 节。

Kaleidos 客户端 `tests/client/im` + `tests/client/ui`：**1521 passed, 2 failed**，
两处失败在未改引擎时同样失败（`test_card_padding_contract`、
`test_progress_ring_reuse` 的源码合同断言），属既有问题。

---

## 5. 残留与后续

* 视图重测写回边界的那一帧仍会短暂显示视图自己的取值（下一帧恢复位移）。
  真实聊天列表上该写入出现在位移还很小的时候，差异只有几像素；位移长大后再发生重测时，
  该帧仍可能显示数十像素的跳变。彻底消除需要让列表面也走 `Timeline` 的视觉超出层
  （`_visualOvershootEnabled` + `_visualOvershootOffset`），属于独立议题。
* 引擎发布不会自动更新下游 venv，Kaleidos 需显式升 `prismqml` 并重新打包。

---

## 6. `0.5.0.35`：重测改写不得重置进行中的位移

### 6.1 缺陷

`0.5.0.34` 的 `rebaseOutwardFrame()` 最终调用 `_applyPositionRebase()`，后者
`driver.setImmediate(position)` 把**动画位置吸附回视图写回的边缘值**，再 `moveTo(nextTarget)`
重新起跑。重测频繁时（真实聊天列表每 2~6 帧抖一次 `contentHeight`）动画每次都被拉回起点，
外移腿永远长不过几像素 —— 用户看到的就是「滚到顶直接弹回」。

### 6.2 修复

外移腿的重锚改为锚定**实时动画值**（`_rebaseLiveOutwardLeg`）：

* 保留 `_smoothY`，在同一轮内把它重新发布回 `contentY`，使视图的写入不被渲染；
* 目标未变时不调用 `moveTo`，进行中的动画不重启、进度不丢；
* 目标真的变了（边界移动）才重新瞄准，且发布值仍夹在 `[edge ± _maxOvershoot]` 内；
* 返回腿仍走原来的 `_applyPositionRebase`（采纳外部位置），语义不变。

净改动只有 `_internal/SmoothScrollOvershootGuard.qml` 一个源文件：
`rebaseOutwardFrame()` 不再采纳视图写回值，新增 `_rebaseLiveOutwardLeg()`。

### 6.3 回归门禁

新增 `test_supported_overshoot_keeps_excursion_across_repeated_view_rewrites`：
在允许越界的目标上发起外移腿，并像重测中的列表那样反复把轴写回边缘，断言

* 外移腿存活期间位移**不得回落到边缘**（回落即是从零重启的形态）；
* 峰值必须超过一次滚轮步长的 30%。

实测：修复前 2/2 失败（位移从 5 回落到 2），修复后 3/3 通过。

### 6.4 门禁结果

```powershell
cd D:\PrismQML\PrismQML
.\.venv\Scripts\python.exe scripts/test_process.py --qt-platform offscreen --timeout 2400 -- `
  .\.venv\Scripts\python.exe -m pytest -q -rx --full-suite tests/qml -p no:cacheprovider
```

**1361 passed, 1 skipped, 0 failed**（含时间线 17 项与滚动条 28 项）。
