# PrismQML 重复造轮子整改方案

> 文档状态：方案已落盘，尚未执行代码整改
> 创建日期：2026-08-22
> 适用范围：`D:\PrismQML\PrismQML`
> 审计方式：静态源码、生产引用、`qmldir` 注册、Git 历史与现有源码门禁核对

本文把本轮“项目里面有没有重复造轮子”的静态审计结果整理为可逐阶段执行的整改方案。当前只记录方案，不删除文件、不改业务代码、不改变既有行为或视觉。

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
| D1 | 失效重复实现 | `controls/containers/Layout/FlowLayoutGeometry.js` | `FlowLayoutEngine.js` 已持有同类算法；`test_flow_layout_architecture.py` 明确禁止入口引用它；全仓无生产消费者 | P0 | 先确认发布包/外部消费者，再删除并补死代码门禁 |
| D2 | 失效旧实现 | `controls/navigation/_internal/StackedAnimations.qml` | `StackedWidget.qml` 当前使用 `StackedModeAnimations`；旧文件无生产消费者；Git 历史显示按模式加载已替代它 | P0 | 删除前做全仓与包内容检查，保留回滚提交 |
| D3 | 公共能力复制 | `ViewportMixin.qml`、`ProgressBarImpl.qml`、`ProgressRingImpl.qml`、`Skeleton.qml` | 四处实现 Flickable 查找、视口计算和信号更新，默认值、初始化时机、异常边界已不同 | P1 | 先统一 helper 契约，再迁移三个消费者 |
| D4 | 树遍历复制 | `ComboBoxTree.qml`、`ComboBoxMultiTree.qml` | `_expandAllNodes`、`_collectExpandableNodes`、`_flattenTree`、`_hasMatchingDescendants`、`_toggleExpand` 重复 | P1 | 提取纯树遍历 helper，保留单选/多选输出与选择状态差异 |
| D5 | 窗口编排复制 | `WindowsFilled.qml`、`WindowsSplit.qml`、`WindowsBarContent.qml` | `StackedWidget` 绑定、Python lazy 信号转发、loading overlay 生命周期和页面迁移重复 | P1 | 提取页面栈/loading 编排 helper，不合并不同导航布局 |
| D6 | 动画后端复制 | `StackedPopUpAnimations.qml`、`StackedPopDownAnimations.qml` | 属性、生命周期和过渡流程几乎相同，差异为方向和 easing | P2 | 参数化一个后端，保持现有视觉差异 |
| D7 | 图表数学复制 | `BarChartGeometry.js`、`LineChartPainter.js`、`LineChartMarkers.qml` | 平均值和 min/max 索引算法同构 | P2 | 提取 `ChartMath.js`，只迁移纯函数 |
| D8 | 重复公开名称 | 多个 `qmldir` 和根 `qmldir` | 同一文件以 `Button/ButtonCore`、`Slider/SliderCore`、`CheckIndicator/ToggleCheckIndicator` 等多个名字公开 | P2 | 先盘点外部消费者，确认后再决定保留、重命名或删除别名 |
| D9 | 完全相同小 helper | `WindowsFilledStartupTimer.qml`、`WindowsSplitStartupTimer.qml` | 实现完全相同，仅 `objectName` 和注释不同 | P3 | 可合并为通用启动 timer；需保留测试可观察的 objectName 契约 |
| D10 | 小型平台绑定复制 | `shadow.py`、`_window_follower.py` | `SetWindowPos` ctypes 签名重复 | P3 | 可提取 Windows API 声明 helper，收益低，最后处理 |
| D11 | HSV 状态转换复制 | `ColorPickerDialog.qml`、`ColorPickerDropdown.qml` | `updateColor`、`updateHsvFromColor` 同构，信号和 alpha 语义略有差异 | P3 | 只提取纯 HSV 转换，不合并对话框/下拉生命周期 |

## 三、明确不作为整改目标的内容

以下目前不判定为重复造轮子：

- `python/core/engine.py` 与 `python/runtime/engine.py`：核心状态与运行时 facade，职责不同。
- `python/core/theme.py` 与 `python/runtime/appearance.py`：主题状态与持久化装配，职责不同。
- `PopupWindowCore.qml` 被 ComboBox、Picker、ColorPicker 等使用：这是正确复用。
- `NavigationPanelCore.qml` 与 `ToggleNavigationBar.qml` 的指示器逻辑：坐标体系、滚动模型和布局契约不同，暂不强行抽象。
- `StackedFadeAnimations`、`StackedSlideAnimations`、`StackedCardAnimations` 等不同动画模式：它们共享接口，但运动模型不同，应保持独立后端。

## 四、执行阶段

### 阶段 P0：清理失效实现

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

风险：高。涉及窗口创建时序、Loader 生命周期和视觉层级，必须单独阶段、单独提交。

### 阶段 P3：参数化动画与纯数学 helper

目标：处理 D6、D7、D9、D10、D11。

执行原则：

- PopUp/PopDown 只共享实现机制，方向和 easing 作为显式 required 参数；不得把两种视觉模式合并成同一 easing。
- `ChartMath.js` 只放无副作用的 `average` 和 `findMinMaxIndices`，不放 Canvas、QML 状态或主题逻辑。
- 启动 timer 合并前必须保留可观测 `objectName` 或迁移现有测试到显式 role/name 属性。
- Win32 声明 helper 必须只在 Windows 路径加载，保持非 Windows 行为不变。
- HSV helper 不得吞掉 alpha、信号名或对话框/下拉初始化差异。

验收：

- 各动画模式逐帧输入输出、终态属性和完成信号保持一致。
- 图表空数组、单元素、负数、相同值和多系列输入结果保持一致。
- Windows/非 Windows 平台的导入和启动路径均无回归。

### 阶段 P4：公开别名清理决策

目标：处理 D8。

此阶段先不改 API，只形成消费者清单：

1. 搜索仓内 QML、Python、示例和文档消费者。
2. 检查发布包导出的模块和历史版本说明。
3. 对每个别名标记为“仍在使用、外部兼容需要、无消费者”。
4. 只有确认无消费者且符合 v1 前删除规则时，才单独提交删除别名。

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

## 六、当前不执行项

- 本方案不删除 `FlowLayoutGeometry.js`。
- 本方案不删除 `StackedAnimations.qml`。
- 本方案不改变 `qmldir` 公开名称。
- 本方案不修改现有用户工作树中的 `NavigationSmoothScroll.qml` 和 `test_smooth_scroll_physical_pixels.py`。
- 本方案不运行 Nuitka、不打包、不发布、不推送生产环境。

## 七、推荐实施顺序

```text
P0 失效实现清理
  -> P1 视口与树遍历公共能力
  -> P2 窗口页面栈/loading 编排
  -> P3 动画、图表与小型 helper 参数化
  -> P4 公开别名消费者决策
```

建议先做 P0。它的行为风险最低、收益最明确；P1 和 P2 必须在补齐定向回归后再执行。
