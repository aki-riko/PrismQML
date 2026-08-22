# PrismQML 重复造轮子整改方案

> 文档状态：调研与整改已完成；D8、D9 经复核保留
> 创建日期：2026-08-22
> 适用范围：`D:\PrismQML\PrismQML`
> 审计方式：静态源码、生产引用、`qmldir` 注册、Git 历史与现有源码门禁核对
> 复核记录：2026-08-23 完成 D6、D8、D9、D10 复核，修正 D10 调用点计数（2→4）并核对实际提交与定向测试

本文把本轮“项目里面有没有重复造轮子”的静态审计结果和执行结果放在同一份记录中。已完成项均保持原有公开 API、交互流程、动画时序、窗口布局、颜色、尺寸和主题行为；保留项明确记录了不宜为形式去重而修改的理由。

## 一、整改目标

完成后应达到以下结果：

1. 删除或明确隔离无生产引用的旧实现，避免维护者误改死代码。
2. 将已经复制到多个组件中的公共算法收敛到单一实现，避免行为继续漂移。
3. 对必须保留的视觉变体、窗口布局变体和公开 API 别名明确所有权，不为形式上的去重破坏现有契约。
4. 每个阶段都有独立的源码门禁、定向运行时验证、提交和回滚点。
5. 不改变原有公开 API、交互流程、动画时序、窗口布局、颜色、尺寸或主题行为；确需改变时必须另行取得明确同意。

## 二、已确认问题清单

| 编号 | 类型 | 目标 | 证据 | 优先级 | 初步处置 |
|---|---|---|---|---|---|
| D1 | 失效重复实现 | `controls/containers/Layout/FlowLayoutGeometry.js` | `FlowLayoutEngine.js` 已持有同类算法；全仓无生产消费者 | P0 | 已完成：删除并补防回流门禁；提交 `599733b4b` |
| D2 | 失效旧实现 | `controls/navigation/_internal/StackedAnimations.qml` | `StackedWidget.qml` 当前使用 `StackedModeAnimations`；旧文件无生产消费者 | P0 | 已完成：删除并补防回流门禁；提交 `599733b4b` |
| D3 | 公共能力复制 | `ViewportMixin.qml`、`ProgressBarImpl.qml`、`ProgressRingImpl.qml`、`Skeleton.qml` | 四处实现 Flickable 查找、视口计算和信号更新 | P1 | 已完成：统一 `ViewportMixin`；提交 `6b20b1035`、`7a9233aa9`、`475516c6a`、`c9209a61c` |
| D4 | 树遍历复制 | `ComboBoxTree.qml`、`ComboBoxMultiTree.qml` | 展开、收集、扁平化和搜索命中规则重复 | P1 | 已完成：共用 `ComboBoxTreeNodes.js`；提交 `67404943d` |
| D5 | 窗口编排复制 | `WindowsFilled.qml`、`WindowsSplit.qml`、`WindowsBarContent.qml` | 页面栈、lazy 信号和 loading 生命周期编排重复 | P1 | 已完成：共用 `WindowsPageStack.qml`；提交 `da637b810`、`c1192e8d4`、`be7780aa4` |
| D6 | 动画后端复制 | 历史上的 `StackedPopUpAnimations.qml`、`StackedPopDownAnimations.qml` | 生命周期和过渡流程相同，差异仅为方向与 easing | P2 | 已完成：统一为 `StackedPopAnimations.qml`，显式配置 PopUp/PopDown；提交 `b26e0559a` |
| D7 | 图表数学复制 | `BarChartGeometry.js`、`LineChartPainter.js`、`LineChartMarkers.qml` | 平均值和 min/max 索引算法同构 | P2 | 已完成：提取 `ChartMath.js`；提交 `d944d11bd` |
| D8 | 重复公开名称 | 多个 `qmldir` 和根 `qmldir` | `Button/ButtonCore`、`Slider/SliderCore`、`CheckIndicator/ToggleCheckIndicator` 均有真实消费者 | P2 | 已决策保留：这是当前公开 API 双名称，不删除、不改名 |
| D9 | 完全相同小 helper | `WindowsFilledStartupTimer.qml`、`WindowsSplitStartupTimer.qml` | 实现相同，但 `objectName` 分别被源码/运行时测试观察 | P3 | 已决策保留：语义化对象名提供诊断边界，合并收益不足以承担合同迁移 |
| D10 | 小型平台绑定复制 | `core/shadow.py`、`core/_window_follower.py`、`window/native_window.py`、`core/_popup_owner.py` | 四处重复 `SetWindowPos` ctypes 签名 | P3 | 已完成：共用 `core/_win32_api.py::bind_set_window_pos`；提交 `0a02b3eec` |
| D11 | HSV 状态转换复制 | `ColorPickerDialog.qml`、`ColorPickerDropdown.qml` | HSV 数学转换同构，生命周期和 alpha 语义不同 | P3 | 已完成：共用 `ColorPickerHsv.js`；提交 `7f6d2643f` |

## 三、明确不作为整改目标的内容

以下目前不判定为重复造轮子：

- `python/core/engine.py` 与 `python/runtime/engine.py`：核心状态与运行时 facade，职责不同。
- `python/core/theme.py` 与 `python/runtime/appearance.py`：主题状态与持久化装配，职责不同。
- `PopupWindowCore.qml` 被 ComboBox、Picker、ColorPicker 等使用：这是正确复用。
- `NavigationPanelCore.qml` 与 `ToggleNavigationBar.qml` 的指示器逻辑：坐标体系、滚动模型和布局契约不同，暂不强行抽象。
- `StackedFadeAnimations`、`StackedSlideAnimations`、`StackedCardAnimations` 等不同动画模式：它们共享接口，但运动模型不同，应保持独立后端。

## 四、执行阶段

### 阶段 P0：清理失效实现

状态：已完成（D1、D2）。

目标：处理 D1、D2。

执行顺序：

1. 读取目标文件、所有 `qmldir`、打包清单、文档和测试引用。
2. 用 `rg` 确认生产源码、示例、测试和构建/发布脚本均无消费者。
3. 检查 Git 历史，确认新实现已经成为当前入口。
4. 先在临时验证副本中移除目标文件，运行最小源码门禁和相关 QML probe。
5. 通过后才删除仓内文件；失败则恢复回滚副本并停止阶段。

验收：

- `FlowLayout` 入口仍通过 `FlowLayoutEngine.js` 工作。
- `StackedWidget` 的所有动画模式和 lazy enter-only 路径仍使用 `StackedModeAnimations`。
- 发布包、sdist/wheel 文件清单中不再包含失效文件。
- 相关定向测试通过，`git diff --check` 通过，未出现 `.artifacts/` 之外的产物。

回滚：恢复删除前文件和对应测试门禁提交，不回滚其他工作树改动。

### 阶段 P1：统一视口与树遍历公共能力

状态：已完成（D3、D4）。

目标：处理 D3、D4。

建议设计：

- 以 `ViewportMixin` 作为唯一视口检测契约，明确“无 Flickable、不可见、contentItem 未就绪、异常”四类边界。
- helper 只负责 Flickable 查找、几何计算和信号生命周期；动画是否暂停由消费者决定。
- 树 helper 只负责节点 ID、路径、展开状态和搜索命中；单选数组、多选 `ListModel`、选择状态计算留在各自组件。

验收：

- 进度条、进度环、Skeleton 在无 Flickable、滚动、尺寸变化、不可见和异常边界下结果一致。
- 单选树和多选树的展开、搜索、空节点、字符串节点和深层节点结果保持原样。
- 不增加重复的 `_findFlickable`、`_updateViewport`、树遍历函数。
- 运行对应最小 QML 测试和真实 QML 进程重启验证。

风险：中高。此阶段最容易因初始化时机或边界默认值变化造成视觉/动画回归，必须先补回归测试再迁移。

回滚：按消费者逐个提交；任一消费者失败时只回滚该消费者迁移，不回退公共 helper 之外的改动。

### 阶段 P2：抽取窗口页面栈与 loading 编排

状态：已完成（D5）。

目标：处理 D5，并复核 `LoadingOverlay.qml` 是否为遗留组件。

建议边界：

- 新 helper 只持有 `StackedWidget`、lazy-loading overlay、宿主信号转发和页面迁移回调。
- `WindowsFilled` 保留左侧 ToggleNavigationBar 和填充式内容布局。
- `WindowsSplit` 保留可展开导航、ContentFrame、Acrylic 和遮罩点击逻辑。
- `WindowsBarContent` 保留紧凑导航、翻译依赖和 hostWindow 为空时的行为。
- 不直接用当前 44 行的 `LoadingOverlay.qml` 替代生产 `QMLPage` overlay，除非先补齐 finishing 生命周期和宿主回调契约。

验收：

- 三种窗口的页面迁移、splash dismiss、Python lazy collapse/expand/finish 事件顺序不变。
- 首次加载、切页、loading 结束和窗口完全重启均通过定向 QML 测试。
- 核对 `LoadingOverlay.qml` 是否仍有真实消费者；若没有，单独提交删除，不和窗口重构混合。
  已核实：无任何 QML 引用它，但 `tests/qml/test_progress_ring_reuse.py` 把它列入
  `RING_CONSUMERS` 并断言 `indeterminateStyle` 与 `spinDuration`，删除必须同批更新该门禁。

风险：高。涉及窗口创建时序、Loader 生命周期和视觉层级，必须单独阶段、单独提交。

### 阶段 P3：参数化动画与纯数学 helper

状态：已完成（D6、D7、D10、D11）；D9 经复核保留。

目标：处理 D6、D7、D10、D11，并对 D9 做保留决策。

执行原则：

- PopUp/PopDown 只共享实现机制，方向和 easing 作为显式运行时配置；不得把两种视觉模式合并成同一 easing。
- `ChartMath.js` 只放无副作用的 `average` 和 `findMinMaxIndices`，不放 Canvas、QML 状态或主题逻辑。
- 启动 timer 合并前必须保留可观测 `objectName` 或迁移现有测试到显式 role/name 属性。
- Win32 声明 helper 必须只在 Windows 路径加载，保持非 Windows 行为不变；四个调用点
  （`shadow.py`、`_window_follower.py`、`native_window.py`、`_popup_owner.py`）必须逐个迁移，
  且不得让 `core/` 反向依赖 `window/`（见 AGENTS.md 1.2 依赖方向铁律）。
- HSV helper 不得吞掉 alpha、信号名或对话框/下拉初始化差异。

验收：

- 各动画模式逐帧输入输出、终态属性和完成信号保持一致。
- 图表空数组、单元素、负数、相同值和多系列输入结果保持一致。
- Windows/非 Windows 平台的导入和启动路径均无回归。

本阶段实际验证：D6 源码门禁 `1 passed`，六种 `StackedWidget` 动画运行时回归
`14 passed`（含 PopUp→PopDown 同源 Loader 复用）；D10 Win32 声明合同与窗口相关定向测试 `100 passed`，Python 架构防回流
门禁 `1 passed`。所有 runner 均报告 `visible_windows=0 / job_active_processes=0`。

### 阶段 P4：公开别名清理决策

状态：已完成（D8 保留）。

目标：处理 D8。

此阶段不改 API，只形成并核实消费者清单：

1. 搜索仓内 QML、Python、示例和文档消费者。
2. 检查发布包导出的模块和历史版本说明。
3. 对每个别名标记为“仍在使用、外部兼容需要、无消费者”。
4. 只有确认无消费者且符合 v1 前删除规则时，才单独提交删除别名。

核实结果：`ButtonCore` 被对话框消费者使用，`SliderCore` 被 `ChartDataZoom` 和示例
使用，`ToggleCheckIndicator` 被 Toggle 内容使用，`CheckIndicator` 仍被其他树控件使用；
四组名称均不是无消费者的死别名，因此本轮保留。

验收：

- 不保留未经证明的 deprecated 别名。
- 删除别名时同步更新 `qmldir`、文档、示例和合同测试。
- 任何外部兼容风险必须在实施前单独确认，不与内部去重混合。

## 五、测试与 Review 门禁

每个阶段只运行与改动直接相关的最小定向测试，不运行未经授权的全仓测试。统一执行：

1. 完全退出并重新启动相关 Python/QML 进程，不假设 Loader、QML cache 或模块缓存仍有效。
2. 运行对应 `tests/tooling` 源码门禁。
3. 运行对应 `tests/qml` 真实 QML 测试或 probe。
4. 检查 `git diff --check`。
5. 检查 `git status --short --ignored`，确认生成物只在 `.artifacts/` 或允许的 `prismqml.egg-info/`。
6. 每个阶段单独 `git commit`，保留可逆提交边界。

## 六、范围边界与未授权动作

- 本方案不改变 `qmldir` 公开名称。
- 本方案不修改 `navigation/_internal/NavigationSmoothScroll.qml` 与
  `tests/qml/test_smooth_scroll_physical_pixels.py`；两者的物理像素改动已由
  `e9ea90284` 落盘，工作树无残留改动。
- 本方案不运行 Nuitka、不打包、不发布、不推送生产环境。

## 七、推荐实施顺序

```text
P0 失效实现清理                 已完成
  -> P1 视口与树遍历公共能力    已完成
  -> P2 窗口页面栈/loading 编排  已完成
  -> P3 动画、图表与小型 helper  已完成
  -> P4 公开别名消费者决策       已完成（保留双名称）
```

当前没有未处理的重复项。后续若出现新的重复候选，应沿用本方案的“真实消费者核对 →
单一归属门禁 → 定向行为验证 → 独立提交”流程，不把 D8/D9 的有意变体重新判定为死代码。
