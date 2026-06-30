# C++ Gallery — 让纯 C++ 用户看到完整组件画廊

> **状态: 已完成 (2026-06)**。QML 可安装模块 + cpp/gallery 入口 + 13 页可移植化 +
> 宿主对齐(DPI/OpenGL/mica/shadow/图标/异步懒加载/splash/selectable)均已落地并验证;
> 修复图标下划线 bug(2140 图标) + 安装树 INSTALL_INTERFACE 消费 bug。
> 端到端验证: 独立项目 find_package(prism) → 编译 → 运行 → import PrismQML 全链路通。

## 目标
纯 C++ 用户（无 Python、只 `find_package(prism)`）能 `cmake build` 跑出和 Python 版一样的
完整组件画廊（13 页：按钮/输入/卡片/图表/菜单…），不依赖 Python、不依赖源码树相对路径。

## 现状与根因（已探查坐实）
- C++ 库 `prism` 已有完整 install/export（find_package 可用），**但 QML 组件没 install** —— C++
  用户拿不到 `import PrismQML`。这是核心缺口。
- Python 侧已把 QML 源打进 wheel（package_data），靠 addImportPath 扫源码，能分发。
- PrismQML 引擎内部 323 个 QML，**249 个用相对 import 互相引用**（实现细节，不动）。
- 13 个 gallery 页面（examples/pages/）是**外部使用者**，却也用了相对路径 import +
  相对 icon 路径（`../../prismqml/...`）→ 换宿主/换目录就断。
- **2 个真实缺口**：`ToolTip`（qmldir 里被注释 `#ToolTip`）、`FlipView` 本体未在顶层
  qmldir 导出 → 纯 `import PrismQML` 拿不到，FeedbackPage/CarouselPage 受影响。

## 方案（收窄、低风险，不重构内部 249 相对 import）

### 第 1 步：C++ install 补 QML 模块（核心）
- cpp/CMakeLists.txt 的 install 段加：把 `prismqml/PrismQML/` 整目录 install 到
  `<prefix>/qml/PrismQML/`（QML + qmldir + svg + js + qsb 全套）。
- prismConfig.cmake 暴露 QML import 路径变量（如 `prism_QML_DIR`），用户 addImportPath 即得。
- 效果：纯 C++ 用户 find_package(prism) 后 engine.addImportPath(prism_QML_DIR) → `import PrismQML` 可用。

### 第 2 步：补 2 个缺口组件的顶层导出
- qmldir 取消 `#ToolTip` 注释（或确认 Tooltip 正确导出名），补 `FlipView` 导出。
- 验证 Python 侧不受影响（只是新增导出，不改已有）。

### 第 3 步：gallery 页面改为可移植（共享一份，复用 examples/pages）
- 13 个 examples/pages/*.qml：相对 import `"../../prismqml/PrismQML/controls/..."` →
  删除（组件已由 `import PrismQML` 覆盖），保留/添加 `import PrismQML`。
- iconPath：`Qt.resolvedUrl("../../prismqml/.../icons/fluent/X.svg")` → 改用模块内
  icon 访问（`Enums.icon.*` 或 `qrc`/模块相对），不依赖源码树位置。
- 保证改后 **Python gallery 仍跑通**（examples/main.py）+ **C++ gallery 能加载**。

### 第 4 步：C++ Gallery demo
- 新增 cpp gallery 入口（或扩展现有 demo）：用 `w.addPage()` 加载 13 个 examples/pages 页面
  + 对应图标/标题（对照 examples/main.qml 的 navItems）。
- pagePath 机制支持指向 examples/pages（桌面磁盘 + 可选 qrc 打包）。

### 第 5 步：验证（双宿主 + 多平台）
- Python：examples/main.py gallery 全 13 页正常（回归）。
- C++：新 gallery 桌面跑通，13 页都能加载渲染（offscreen 加载无 QML 错 + 真实窗口抽查）。
- CI：build-all.yml 桌面三平台编译通过（QML install 不破坏现有构建）。

## 决策点（plan 中待定）
- gallery 页面**共享一份**（已选）：改 examples/pages 本身为可移植，C++ 与 Python 都加载它。
  风险：改动影响 Python gallery，需两侧都回归。

## 不做（避免过度工程）
- 不把内部 323 QML 重构成 qt_add_qml_module / 不动 249 个内部相对 import。
- 不做 iOS/Android 的 gallery 打包（先桌面双宿主跑通；移动 qrc 打包可后续）。
