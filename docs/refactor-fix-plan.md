# PrismQML 重构修复落盘计划

> 分支：`fix/refector`
> 创建日期：2026-07-08

本文记录本轮全仓重构修复的执行顺序、验证门槛和提交边界。每一步必须先修完、验证通过、单独提交，再进入下一步。

## 执行规则

- 修改前先读目标文件。
- v1.0.0 前不保留废弃 API 或兼容别名。
- 每一步只改当前步骤范围内的文件。
- 每一步完成后运行对应验证命令。
- 验证失败必须先分析根因，禁止继续叠加修改。
- 每个完成步骤都单独提交。

## Step 1 - QML 硬规范快修

范围：
- 移除不必要的 `QtQuick.Controls` import。
- 把组件内部 enum 迁入全局 `Enums` 入口。
- 同步更新迁移后的 enum 引用。

目标文件：
- `prismqml/PrismQML/controls/inputs/ImageCropper.qml`
- `prismqml/PrismQML/controls/containers/Layout/RowFit.qml`
- `prismqml/PrismQML/controls/inputs/Search/LocalSearchBar.qml`
- `prismqml/PrismQML/Enums.qml`
- 必要时更新对应的 `PrismEnums/*` 分类文件

验证：
- `rg -n "^\\s*import\\s+QtQuick\\.Controls\\b|^\\s*enum\\s+[A-Za-z_]" prismqml/PrismQML -g "*.qml"`
- `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe tests\qml\probe_all_components.py`
- `.\.venv\Scripts\python.exe -m pytest`

### Step 1 执行记录

- 状态：已完成。
- 变更：`RowFit` 对齐模式迁移到 `Enums.orient.align_*`；`LocalSearchBar` 搜索弹窗模式迁移到 `Enums.input.search_popup_*`；`ImageCropper` 移除未使用的 `QtQuick.Controls` import。
- 静态扫描：组件内部 `enum`、旧 `RowFit.*` 和 `LocalSearchBar.PopupMode.*` 引用已清零。
- 已知例外：`controls/containers/Widget.qml` 仍使用 `QtQuick.Controls.Popup` / `Popup.Window` 承载内部 tooltip，属于 PrismQML 内部基础设施级 Popup，后续单独评估，不并入本快修步骤。
- QML probe：`169 OK / 7 失败 / 5 跳过`，7 个失败均为 required property 单独实例化的既有基线。
- Pytest：`116 passed`。

## Step 2 - Python 文件头合规

范围：
- 给缺少 PrismQML MIT 规范文件头的包内 Python 文件补齐头部。
- 测试和脚本文件单独处理，除非当前步骤必须触碰。

目标文件：
- header 扫描报告中的 `prismqml/python/**` 包内文件。

验证：
- header 扫描中包内文件遗漏数为 0。
- `.\.venv\Scripts\python.exe -m compileall prismqml\python tests`
- `.\.venv\Scripts\python.exe -m pytest`

## Step 3 - 静默异常清理

范围：
- 把包内宽泛或静默的 `except ...: pass` 改成有日志、有理由的处理。
- 真正可忽略的清理失败要收窄异常类型并写明原因。

优先目标：
- `prismqml/python/core/input_focus_filter.py`
- `prismqml/python/config/dpi.py`
- `prismqml/python/core/single_instance.py`
- `prismqml/python/models/sql_list_model.py`
- `prismqml/python/window/_page_manager.py`
- `prismqml/python/window/_window_builder.py`

验证：
- 静态扫描不再出现包内 `except Exception: pass` 或裸 `except`。
- `.\.venv\Scripts\python.exe -m compileall prismqml\python tests`
- `.\.venv\Scripts\python.exe -m pytest`

## Step 4 - Window Builder 模块化

范围：
- 从 `_window_builder.py` 拆出生成 QML 的拼装逻辑。
- 保持 `WindowCore` 公开行为不变。

目标文件：
- `prismqml/python/window/_window_builder.py`
- 新增 `prismqml/python/window/` 下的私有 helper 模块。

验证：
- `_window_builder.py` 尽量降到 500 行以下，超长函数明显缩短。
- `.\.venv\Scripts\python.exe -m pytest tests\test_core.py tests\qml\test_splash_default_mount.py tests\qml\test_splash_timing.py`
- 若 QML probe 数量变化，必须跑基线 worktree 对比。

## Step 5 - TableWidget 模块化

范围：
- 拆分 900+ 行表格组件。
- 保持现有类 QTableWidget API 不变。

目标文件：
- `prismqml/PrismQML/controls/data/Table/TableWidget.qml`
- 新增 `Table/_internal` 下的 QML/JS helper。

验证：
- `TableWidget.qml` 降到 700 行以下，最好降到 500 行以下。
- `.\.venv\Scripts\python.exe -m pytest tests\qml\test_list_widget.py tests\test_carousel_item_delegate.py`
- QML probe 基线对比。

## Step 6 - ChartView 模块化

范围：
- 拆分图表类型渲染、legend、tooltip、viewport、dataZoom。
- 保持现有 `ChartView` API 和示例不变。

目标文件：
- `prismqml/PrismQML/controls/data/Chart/ChartView.qml`
- 现有或新增 `Chart/_internal` 文件。

验证：
- `ChartView.qml` 降到 700 行以下，最好降到 500 行以下。
- QML probe 基线对比。
- Gallery 图表示例加载无新增 QML 警告。

## Step 7 - SqlListModel 模块化

范围：
- 从 `SqlListModel` 拆出 SQL 解析、keyset 谓词生成和页缓存管理。
- 保持 Python/QML 公共 API 与 Rust 加速行为不变。

目标文件：
- `prismqml/python/models/sql_list_model.py`
- 新增 `prismqml/python/models/` 下的私有 helper 模块。

验证：
- `sql_list_model.py` 降到 700 行以下，最好降到 500 行以下。
- `.\.venv\Scripts\python.exe -m pytest tests\test_core.py tests\test_providers.py`
- 可用时补跑 C++/Rust 相关 SQL model 测试。
