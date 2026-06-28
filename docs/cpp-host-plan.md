# PrismQML C++ 宿主层预研报告

> 目标：让同一套 PrismQML QML 引擎不被 Python 限制，通过 C++ 宿主层覆盖
> 所有 Qt 支持的平台（桌面 / 移动 iOS·Android / WASM / 嵌入式），且 C++ 侧
> 1:1 接入 Python 现有全部能力，不舍弃任何组件。
>
> 本报告所有结论均经真实编译运行验证（非纸面推断）。

## 实现进度（持续更新）

预研结论之后已落地为可用的 C++ 宿主库 `prism`（见 `cpp/`，README 在 `cpp/README.md`）：

- ✅ **阶段 1**：App / Window / ThemeManager 对称 API 跑通（QML 加载、主题注入生效）。
- ✅ **阶段 2**：8 个注入对象补齐（ConfigManager / ShadowManager / MicaManager /
  NativeWindow / Clipboard / WindowHelper / Acrylic / SvgImageProvider），
  QML `ReferenceError` 清零，DWM 阴影 / NativeWindow.attach 真实生效。
- ✅ **阶段 3**：Window.addPage 导航 + 页面懒加载管理；真实平台渲染验证
  （1823×1256，accent 色像素级命中）。
- ✅ **阶段 4**：Store / Logger / SystemTrayIcon / SingleInstance 应用框架能力；
  单元测试 `prism_test_store` 全通过。
- ✅ **阶段 5**：CMake 安装导出（`find_package(prism)`）+ README + 本文档。
- ✅ **阶段 6**：桌面补齐——Updater（语义版本比较 + GitHub releases）/
  ScreenEyedropperManager（全屏取色）/ QRCodeGenerator（接口完整，编码降级）/
  SqlListModel（QtSql 分页 + LRU，真实 SQLite 250 行测试通过）。测试 26 断言全 PASS。
- ⬜ **按需**：完整 QR 编码器 / SqlListModel keyset 游标·多 shard（Rust FFI）/
  TableListModel / Updater 静默安装——边界明确，需求驱动。
- 🟡 **阶段 7 移动端（代码层就绪，真机构建待环境）**：
  - Platform.h 平台条件编译宏 + Window 移动端全屏 + PlatformInfo 触摸适配地基
    （isMobile/isTouch/touchTargetSize/isCompact），均测试验证。
  - prism_mobile_verify 库坐实移动分支语法/类型正确（桌面编译器强制 PRISM_MOBILE）。
  - ResponsivePage 范本 + 真机 grab 坐实 PlatformInfo 响应式生效（触摸按钮 71px>桌面 47px）。
  - 修复 navigateTo 编程式导航不触发懒加载的真 bug。
  - cpp/ANDROID.md 完整构建指南。
  - ⬜ 真机 apk：需 Qt for Android + SDK + NDK + JDK（~7GB），本机无移动工具链未装。
  - ⬜ 引擎 QML 控件触摸适配（导航壳改底部 Tab、80 控件触摸态）：触及引擎存量 +
    开放式设计，地基已备，待产品决策后实施。

**结论**：C++ 桌面一等宿主完整可交付；移动端代码层就绪并验证，真机构建与 QML 控件
触摸适配待工具链环境与设计决策。

## 一、预研结论（已坐实）

### 1.1 工具链
- **编译器**：MSVC 14.44.35207（VS 2022 BuildTools，本机已装，无需安装）
- **Qt C++ SDK**：Qt 6.10.3 msvc2022_64，经 `aqtinstall` 装于 `D:\Qt`
  - 注：项目当前用 PySide6 / Qt 6.11.1，但 **aqt 3.3.0 无法安装 6.11.x**
    （qt.io 在 6.11.0 改了目录结构，去掉 `qt6_611x/` 层，aqt 拼出双重路径
    `qt6_6111/qt6_6111/Updates.xml` → 404，官方 issue #1007 仍 Open 无修复）。
  - **已解决 6.11.1**：不靠 aqt，从 qt.io 手动拉 .7z 分包装于
    `D:\Qt\6.11.1\msvc2022_64`（与 PySide6 精确对齐，正式版用这个）。
    正确 URL = `<BASE>/qt.qt6.6111.win64_msvc2022_64/<full_version><archive>`
    （规则从 aqt 源码 archives.py:493-499 读出；脚本 `cpp_probe/fetch_qt6111.py`）。
    `qmake -query QT_VERSION` 坐实 6.11.1，MSVC 编译 + 组件加载 PROBE_OK 通过。
  - 两版本并存：`D:\Qt\6.10.3`（aqt 装，对照）+ `D:\Qt\6.11.1`（手动，对齐 PySide6）。
- **验证**：MSVC + Qt 6.10.3 **及 6.11.1** + CMake(NMake) 编译、链接、运行、
  加载真实 PrismQML 组件全部通过。

### 1.2 耦合面（决定 C++ 适配成本的核心）
PrismQML 的 QML 层对后端的耦合**极窄且干净**：

- **注入项共 11 个**（来自 `prismqml/python/core/utils.py` 的 `register_types`）：
  - 9 个 `setContextProperty`：ThemeManager / QRCodeGenerator / MicaManager /
    AcrylicHelper / NativeWindow / ScreenEyedropperManager / ShadowManager /
    WindowHelper（+ register_types 外的 ConfigManager / ShadowManager 等窗口层注入）
  - 2 个 `addImageProvider`：qrcode、acrylic
  - 1 个 `addImportPath`
- **没有任何 `qmlRegisterType`**：所有 QML 类型都是纯 .qml 文件（靠 qmldir），
  C++ 宿主**无需注册任何类型**，只需提供同名 context 对象。
- **322 个 QML 控件没有一个直接引用 `ThemeManager.`**：全部经 `Enums` 单例
  间接访问。后端耦合点收敛到**唯一一处 Enums.qml**（6 个属性引用）。

### 1.3 决定性实验（真实运行证据）
用最小 C++ probe（QQmlEngine + QQmlComponent）加载真实 PrismQML 组件：

| 实验 | ThemeManager ReferenceError | 组件创建 | Enums.accentColor 解析值 |
|------|------|------|------|
| 零注入加载 Enums/Button/ShadowedRectangle | 6 | ✅ PROBE_OK | 取不到（报错兜底） |
| 注入 C++ ThemeManager（6 个 Q_PROPERTY） | **0** | ✅ PROBE_OK | **#0078d4**（C++ 提供值原样生效） |

**结论**：C++ 的 `setContextProperty` + `Q_PROPERTY` 与 Python 的
`setContextProperty` + `@Property` 对 QML **完全等价**，QML 层无法区分背后是
Python 还是 C++。C++ 1:1 接入在原理与实测两个层面都成立。

### 1.4 最小可行集
让控件正常显示主题，**C++ 侧只需实现 ThemeManager 一个对象**。其余 8 个注入
对象是窗口/特效/工具功能，可**渐进式**补齐——组件即使完全无注入也不崩溃
（QML 容错），只是相关属性失真。这意味着 C++ 适配可以小步验证、逐步推进。

## 二、架构：一套引擎，多宿主

```
            ┌──────────────────────────────────────┐
            │   QML 控件层 (322 文件) — 全平台共享     │  ← 源码不动
            │   Enums / token / i18n / 控件 / 特效    │
            └────────────────┬─────────────────────┘
                             │ 11 个注入项 (context + provider)
            ┌────────────────┴─────────────────────┐
            │                                        │
   ┌────────▼─────────┐                  ┌──────────▼──────────┐
   │  Python 宿主      │                  │   C++ 宿主 (新建)     │
   │  PySide6          │                  │   Qt C++             │
   │  桌面三平台 ✅     │                  │  桌面+移动+WASM+嵌入式 │
   └──────────────────┘                  └─────────────────────┘
```

C++ 宿主一旦做出，**本身即覆盖所有 Qt 支持的平台**。"全平台兼容" =
做一个 C++ 宿主 + 解决各平台部署链路，**不需要为每个平台单独做引擎**。

## 三、平台能力天花板（必须正视的矛盾）

"C++ 全平台 + 不舍弃任何组件" 在桌面可 100% 达成，但移动/WASM 有**物理天花板**
（非 C++ 能力不足，是平台本身无此概念）：

| 组件/能力 | 桌面(Win/Mac/Linux) | 移动(iOS/Android) | WASM |
|---|---|---|---|
| ThemeManager / Config / Store / 控件 / 特效 | ✅ | ✅ | ✅ |
| DWM 阴影 / Mica 云母 / 无边框窗口 | ✅ | ❌ 无窗口概念 | ❌ |
| SystemTray 系统托盘 | ✅ | ❌ | ❌ |
| single_instance 单实例 | ✅ | ❌ 无意义 | ❌ |
| Updater 自动更新 | ✅ | ❌ 禁止(须走商店) | ❌ |
| 屏幕取色 ScreenEyedropper | ✅ | ❌ | ❌ |

**正确做法 = 平台条件编译**：同一套 C++ 宿主，桌面分支接入全部能力，移动/WASM
分支自动降级（全屏窗口、无托盘、无自更新）。"不舍弃组件" 在**桌面**可全做到。

### 触摸适配（移动端真大头，实测数据）
这套控件为鼠标桌面设计，移动端须改造（非 C++ 能解决，是交互范式差异）：
- hover/悬停效果：**80 个**控件依赖（占 25%），触摸屏无悬停
- MouseArea：113 个（须评估换 TapHandler，当前仅 6 个用 TapHandler）
- ToolTip：24 个（触摸端触发不了）；鼠标滚轮：28 个（须换 Flickable）
- 手势（Pinch/Swipe）：当前仅 1 个，移动端核心手势几乎为零
- 侧边导航 BAR/SPLIT 须重做为底部 Tab/抽屉；46 处硬编码像素须响应式

## 四、路线与工作量（单人估算）

| 阶段 | 内容 | 工时 |
|---|---|---|
| 1. C++ 注入层 | 9 个 context 对象 + qrcode/acrylic provider + i18n 加载。ThemeManager 已预研验证 | 8–10d |
| 2. C++ 窗口/App 层 | App + 三种 Window + PageManager + 注入装配；平台条件编译 | 8–10d |
| 3. 桌面三平台跑通 | Win/Mac/Linux 与 Python 行为对齐 + probe 等价冒烟测试 | 4–5d |
| 4. 移动端部署 + 触摸适配 | Qt for iOS/Android 构建 + QML 打包 + 触摸态/导航/响应式改造 | 10–15d |
| 5. WASM（可选） | Qt for WebAssembly + 配置走 IndexedDB | 5–8d |
| 6. CMake 统一构建 + CI | 替代 abi3 wheel，多平台产物 | 3–5d |

- **桌面全平台兼容（阶段 1–3）：约 4–5 周** ← 性价比最高的第一里程碑，
  做完即得不依赖 Python 的全桌面 C++ 引擎。
- **加移动端（阶段 4）：再 2–3 周**，触摸适配是硬骨头。
- **全平台（含 WASM）：约 8–11 周**。

## 五、风险点
1. **窗口层（~3000 行）** 是最大头：三布局 + 懒加载 + 无边框原生窗口。
2. **平台 ctypes 代码** 散落 11 个文件（dpi/shadow/mica/native_window/
   single_instance/updater），逐处换原生 API，Win/Mac/Linux 三分支。
3. **nativeEventFilter（DWM 同步）**（shadow.py:370）须重做 `QAbstractNativeEventFilter`。
4. **AUMID/任务栏**：单实例 + 任务栏图标，历史踩过合并坑，需小心。
5. **Qt 版本**：6.11.x 当前 aqt 装不了；CI 建议用官方在线安装器或锁定 6.10.x。

## 六、预研产物
- `cpp_probe/`：可编译运行的最小 C++ 宿主 probe（CMake + main.cpp + build.bat）
  - 已验证：加载真实 PrismQML 组件、注入 C++ ThemeManager、主题值生效
- 工具链：`D:\Qt\6.10.3\msvc2022_64` + MSVC BuildTools

## 七、建议的下一步
**从阶段 1–3（桌面全平台 C++ 宿主）做起**，分里程碑推进，每阶段真机验证后再进。
移动端（阶段 4）在桌面宿主稳定后启动，触摸适配单独立项评估。

<!-- PLACEHOLDER_API -->

## 八、C++ API 对等映射（目标：镜像 Python 门面，两边对称）

> 设计原则：C++ 侧提供与 Python **同名同形**的门面类/自由函数，使两边示例
> 几乎一行对一行。Python 公开符号共 67 个（`prismqml.__all__`）。
>
> **关键认知**：Python 的 `App` 大半是对 Qt `QApplication` 的转发；C++ 门面
> 内部直接持有/转发 `QGuiApplication`，那些转发方法零成本。真正要新建的是
> PrismQML 在 Qt 之上的**增量**（窗口层 / 主题皮肤 / 状态模型 / 平台特效）。

### 8.1 应用 / 窗口（核心，最大头）

| Python | C++ 镜像签名（建议） | 备注 |
|---|---|---|
| `App(argv)` | `prism::App app(argc, argv);` | 内部建 `QGuiApplication` + `QQmlApplicationEngine`，构造时调 `register_types` 等价装配 |
| `app.create_window(WindowType.BAR)` | `prism::Window& app.createWindow(WindowType::Bar);` | 三布局 SPLIT=0/BAR=1/FILLED=2 |
| `app.exec()` | `app.exec();` | 转发 `QGuiApplication::exec` |
| `app.engine()` | `app.engine()` → `QQmlApplicationEngine*` | |
| `app.quit/exit/clipboard/screens/...` | 直接用 `QGuiApplication`/`qApp` | **Qt 已有，免实现** |
| `window.setWindowTitle(str)` | `window.setWindowTitle(QString)` | |
| `window.resize(w,h)` | `window.resize(int,int)` | |
| `window.addPage(interface, icon, text, position="top", selectedIcon="", selectable=True)` | `window.addPage(PageFactory, QString icon, QString text, Position=Top, QString selectedIcon={}, bool selectable=true)` | ⚠️ Python 的 `interface` 可传「类（懒加载）或实例」；C++ 无鸭子类型 → 用 `std::function<QObject*()>` 工厂 或 `QQmlComponent*` 对等懒加载 |
| `window.show/showNormal/showMinimized/showMaximized` | 同名 | |
| `window.showSplash(icon,title,subtitle)` | 同名 | |
| `window.showMessage/showInfo/showWarning/showError(...)` | 同名 | 应用内通知 |
| `WindowType` `WindowCore` `NavigationItem` | `enum class WindowType` / `prism::WindowCore` / `prism::NavigationItem` | |

### 8.2 主题 / 皮肤（预研已验证注入模式）

| Python | C++ 镜像签名 | 备注 |
|---|---|---|
| `setTheme(Theme)` / `getTheme()` | `prism::setTheme(Theme)` / `Theme prism::getTheme()` | `enum class Theme { Light, Dark, Auto }` |
| `setSkin(Skin)` / `getSkin()` | `prism::setSkin(Skin)` / `Skin prism::getSkin()` | `enum class Skin { Fluent, Neobrutalism }` |
| `isDark()` | `bool prism::isDark()` | |
| `setAccentColor(str)` / `getAccentColor()` | `prism::setAccentColor(QString)` / `QString` | |
| `accentQColor()` | `QColor prism::accentQColor()` | |
| `getThemeManager()` | `prism::ThemeManager* getThemeManager()` | **已 probe 验证**：6 个 Q_PROPERTY 注入后 Enums 全解析、accentColor 生效 |

### 8.3 状态 / 数据模型（Rust 加速，C++ FFI 更顺）

| Python | C++ 镜像 | 备注 |
|---|---|---|
| `Store` | `prism::Store` | 响应式状态，watch/batch |
| `TableListModel` / `SqlListModel` | `QAbstractListModel` 派生 | |
| `DbRouter` / `is_rust_accelerated()` | 同名 | 底层 `prismqml_rs`（Rust）；C++ 直接 FFI，比 Python 绑定更自然 |

### 8.4 平台特效 / 窗口装饰（条件编译，桌面专属）

| Python | C++ 镜像 | 平台 |
|---|---|---|
| `ShadowManager` / `getShadowManager()` / `installDwmSyncFilter()` | 同名；C++ 调 DWM 比 Python ctypes 干净 | Win/Mac |
| `MicaManager` / `get_mica_manager()` | 同名 | Win 11 |
| `AcrylicHelper` / `AcrylicImageProvider` | 同名 | Win |

### 8.5 系统集成（桌面专属）

| Python | C++ 镜像 | 备注 |
|---|---|---|
| `SystemTrayIcon` / `MessageIcon` / `ActivationReason` / `createSystemTrayIcon()` | 同名；封装 `QSystemTrayIcon` | 移动端降级 |
| `SingleInstance` | 同名 | 移动端无意义 |
| `Updater` | 同名 | 移动端禁用（须走商店） |

### 8.6 工具 / Provider（多为薄封装）

| Python | C++ 镜像 | 备注 |
|---|---|---|
| `Icon` `IconCore` `make_icon` `make_theme_icon` `paint_icon` `resolveIconColor` | 同名 | SVG 图标渲染 |
| `IconProvider` / `register_icon_provider` / `get_icon_provider` | 同名 | image provider |
| `QRCodeGenerator` / `QRCodeImageProvider` / getters | 同名 | |
| `SvgImageProvider` / `get_svg_provider` | 同名 | image://svg |
| `ScreenEyedropperManager` | 同名 | 桌面专属 |
| `ClipboardHelper` / `get_clipboard_helper` | 封装 `QClipboard` | |
| `Logger` / `getLogger` / `debug/info/warning/error/exception` | `prism::log::info(...)` 等 | |
| `qml_path` / `register_types` / `init_style` | 内部装配函数，C++ 门面构造时调用 | |

### 8.7 对称示例（目标效果）

```cpp
// C++ —— 与 Python README 那段一行对一行
#include <prismqml/App.h>
using namespace prism;

int main(int argc, char** argv) {
    App app(argc, argv);
    setSkin(Skin::Neobrutalism);              // 一行切换设计语言
    Window& w = app.createWindow(WindowType::Bar);
    w.setWindowTitle("我的应用");
    w.resize(1200, 800);
    w.addPage(makeHomePage, "Home", "首页");   // 工厂 lambda 对等懒加载
    w.show();
    return app.exec();
}
```



