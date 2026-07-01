# PrismQML C++ 宿主层 (prism)

> 让 **C++ 应用**以与 Python 对称的 API 调用同一套 PrismQML QML 引擎。
> 与 PySide6 宿主平行：同一套 QML 控件、主题 token、皮肤、i18n 全部复用，
> 仅宿主语言不同。C++ 由此成为和 Python 平等的一等宿主。

## 这是什么

PrismQML 原本是 PySide6 + QML 的多皮肤 UI 引擎。本目录提供一个 **C++ 宿主库
`prism`**，使纯 C++/Qt 应用也能驱动这套引擎——不依赖 Python 解释器，可进而
覆盖 Qt 支持的所有平台（桌面 / 移动 / WASM / 嵌入式）。

QML 层（`prismqml/PrismQML/` 下 322 个组件）对宿主的耦合极窄：仅通过若干
`setContextProperty` 注入对象访问后端，**无一个 `qmlRegisterType`**。C++ 宿主
只需提供同名 context 对象即可，QML 无法区分背后是 Python 还是 C++。

## 依赖

- **Qt 6.11.1**（C++，msvc2022_64；与项目 PySide6 的 Qt 版本对齐）
  - 模块：Core / Gui / Qml / Quick / Svg / Widgets / Network
- **MSVC**（VS 2022 BuildTools，C++17）
- **CMake** 3.16+

## 构建

```bat
:: 激活 MSVC 环境 + 指向 Qt
call "...\VC\Auxiliary\Build\vcvars64.bat"
set "QTDIR=D:\Qt\6.11.1\msvc2022_64"
set "PATH=%QTDIR%\bin;%PATH%"

cmake -S cpp -B cpp/build -G "NMake Makefiles" ^
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=%QTDIR%
cmake --build cpp/build
```

或直接运行 `cpp/build.bat`（已封装上述步骤）。

## 运行 demo / gallery

```bash
export PATH="$QTDIR/bin:$PATH"
./cpp/build/prism_demo.exe       # 4 页最小 demo
./cpp/build/prism_gallery.exe    # 13 页完整组件画廊
```

> 开发树下 **无需设环境变量** —— CMake 在编译期注入了源码树的 QML/页面默认路径
> (`PRISM_QML_DIR_DEFAULT` 等)，`import PrismQML` 与页面加载自动解析。
> 如需覆盖 (如分发后指向别处)，可设 `PRISMQML_QML_DIR`(QML 模块父目录) /
> `PRISM_GALLERY_PAGES` / `PRISM_DEMO_PAGES`，优先级高于编译期默认。

## 快速开始（对称 API）

```cpp
#include <prism/App.h>
using namespace prism;

int main(int argc, char **argv) {
    App app(argc, argv);
    setSkin(Skin::Fluent);            // 一行切换设计语言 (Fluent / Neobrutalism)
    setAccentColor("#0078d4");        // 主题色, 实时流到 QML 控件

    Window &w = app.createWindow(WindowType::Bar);
    w.setWindowTitle("我的应用");
    w.resize(1200, 800);
    w.setSplash(true, "", "我的应用", "加载中...");  // 启动画面(可选, 首屏就绪自动淡出)
    w.addPage("pages/HomePage.qml", "Home", "首页");
    w.addPage("pages/SettingsPage.qml", "Settings", "设置", NavPosition::Bottom);
    // 纯功能项(点击只触发回调不切页, 如底部头像): selectable=false
    w.addPage("", "Person", "用户", NavPosition::Bottom, /*selectable=*/false);
    w.show();
    return app.exec();
}
```

与 Python 端逐行对照：

```python
app = App()
setSkin(Skin.NEOBRUTALISM)
window = app.create_window(WindowType.BAR)
window.setWindowTitle("我的应用"); window.resize(1200, 800)
window.addPage(HomePage, "Home", "首页")
window.show(); app.exec()
```

<!-- PLACEHOLDER_README2 -->

## 已实现能力

| 类别 | C++ API | 镜像的 Python 源 |
|------|---------|------------------|
| 应用入口 | `App`（createWindow / exec / engine / qapp） | window/app.py |
| 窗口 | `Window`（addPage / setWindowTitle / resize / show / navigateTo），三布局 `WindowType` | window_base.py + _window_builder.py + _page_manager.py |
| 主题 | `setTheme/getTheme` `isDark` `ThemeManager` | core/theme.py |
| 皮肤 | `setSkin/getSkin`（Fluent / Neobrutalism） | core/theme.py |
| 主题色 | `setAccentColor/getAccentColor/accentQColor` | core/theme.py |
| 配置 | `ConfigManager`（JSON 持久化 ~/.prismqml/app.json） | config/config_manager.py |
| 窗口阴影 | `ShadowManager`（Win32 DWM） | core/shadow.py |
| 云母 | `MicaManager`（Win11 DWM backdrop） | window/mica_window.py |
| 无边框 | `NativeWindow`（WS_CAPTION + WM_NCCALCSIZE 拦截） | window/native_window.py |
| 亚克力 | `AcrylicHelper`（截屏模糊） | window/mica_window.py |
| 剪贴板 | `ClipboardHelper` | providers/clipboard.py |
| 应用图标 | `WindowHelper`（setAppIcon，SVG 多尺寸） | core/window_helper.py |
| SVG 渲染 | `SvgImageProvider`（image://svg） | providers/svg_provider.py |
| 状态管理 | `Store`（define/get/set/watch/batch） | state/store.py |
| 日志 | `prism::log` + `Logger` 类（debug/info/warning/error + Qt 重定向） | core/logger.py |
| 系统托盘 | `SystemTrayIcon` + `MessageIcon` / `ActivationReason` 枚举 | window/system_tray.py |
| 单实例 | `SingleInstance` | core/single_instance.py |
| 自动更新 | `Updater`（检查/下载 + 语义版本比较 + `runInstallerAndQuit` 安装并重启） | core/updater.py |
| 屏幕取色 | `ScreenEyedropperManager`（全屏覆盖窗点击取色） | providers/screen_eyedropper.py |
| 数据模型 | `SqlListModel`（QtSql + 分页 + LRU 缓存 + keyset 游标 + `DbRouter` 多 shard fan-out） | models/sql_list_model.py |
| 二维码 | `QRCodeGenerator`（完整编码后端，nayuki qrcodegen / MIT，`available=true`） | providers/qrcode_generator.py |
| DWM 同步 | `installDwmSyncFilter`（无边框窗口 resize 防撕裂，桌面 Windows） | core/shadow.py |

### 平台相关的诚实降级（非 Windows 按 `#ifdef` no-op，无功能缺口）
- `installDwmSyncFilter` / `Updater::runInstallerAndQuit` 的 Windows 专属路径
  （DwmFlush 同步、ShellExecuteW 提权安装）在非 Windows 平台按平台条件编译降级：
  DWM 撕裂与 UAC 提权在这些平台物理不存在，非功能缺失。
- `is_rust_accelerated` 诚实返回 false：C++ 数据层是 Qt 原生 QtSql，非 Rust
  `prismqml_rs`（PyO3 Python ABI，C++ 无法复用）；keyset / 多 shard fan-out 已用
  QtSql 原生等价实现（内存归并 + 全局排序），语义等价，适用 <100M 行场景。

> **API 覆盖度：Python `prismqml.__all__` 的 64 个公开符号已 100% 在 C++ 侧提供**
> 实质实现，功能经单元测试验证：
> - QR 编码后端接入 nayuki qrcodegen（MIT），端到端解码验证（opencv 独立解码
>   还原 == 原文，覆盖 URL / 中文 / 特殊符号 / 长文本）；
> - `SqlListModel` keyset 游标与多 shard fan-out 用 QtSql 原生实现并测试坐实
>   （keyset 翻页逐行 == OFFSET 路径；多 shard 归并全局排序正确）；
> - `Updater::runInstallerAndQuit` 补齐安装器调起 + 退出重启；
> - `WindowCore` / `Logger` / `ActivationReason` / `qml_path` / `installDwmSyncFilter`
>   建为与 Python 逐字对称的同名实体，单测验证可用。

## 作为库集成

先安装（QML 组件、头文件、库、CMake config 一并装好）：

```bash
cmake --install cpp/build --prefix <你的安装前缀>
```

其他 CMake 项目消费时，`find_package(prism)` 会导出库目标 + QML 组件目录变量
`prism_QML_DIR`。**纯 C++ 用户不需要源码树、不需要 Python**：

```cmake
find_package(prism REQUIRED)          # 自动转发 Qt6 依赖
qt_add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE prism::prism)
# 把安装的 QML 组件目录传给运行时, 使 import PrismQML 可解析
target_compile_definitions(myapp PRIVATE PRISM_QML_DIR="${prism_QML_DIR}")
```

```cpp
#include <prism/App.h>
#include <prism/Window.h>
int main(int argc, char **argv) {
    prism::App app(argc, argv);
    app.engine()->addImportPath(PRISM_QML_DIR);   // = prism_QML_DIR, 含 PrismQML/ 子目录
    prism::Window &w = app.createWindow(prism::WindowType::Bar);
    w.setWindowTitle("我的应用");
    w.show();
    return app.exec();
}
```

> 已端到端验证：`make install` → 独立项目 `find_package(prism)` → 编译 → 运行 →
> `import PrismQML` 全链路打通(消费程序无需源码树)。

## 平台说明

- **桌面（Windows / macOS / Linux）**：全部能力可用。DWM 阴影 / Mica / 无边框
  为 Windows 原生；非 Windows 平台对应 `#ifdef` 降级为无操作。
- **移动 / WASM**：窗口装饰（托盘 / 云母 / 无边框 / 单实例 / 自动更新）在这些平台
  物理不存在，按平台条件编译降级；触摸适配需另行处理（控件原为鼠标桌面设计）。

## 验证状态

- Qt 6.11.1 + MSVC 全量编译链接通过（含 nayuki qrcodegen 第三方源）。
- demo 真实平台渲染：1823×1256，96 种颜色，accent 色 `#F97316` 像素级命中
  （C++ ThemeManager 注入值流到渲染）。
- `prism_test_store`：Store / Logger / Updater 版本比较 + 对称类型（`Logger` /
  `ActivationReason` / `qml_path` / `WindowCore` / `installDwmSyncFilter` /
  `runInstallerAndQuit` 失败路径）共 68 项断言全部通过。
- `prism_test_sqlmodel`：多 shard fan-out 归并 + keyset 升/降序翻页（逐行 ==
  OFFSET 路径）+ 单库回归共 11 项断言通过；破坏谓词方向可复现 FAIL（区分力坐实）。
- `prism_test_qrcode_gen` + `tests/qr/verify_qr.py`：C++ 生成的 QR PNG 由 opencv
  独立解码还原 == 原文，5 组（URL / 中文 / 特殊符号 / 长文本）全部通过。
- QML 加载真实 PrismQML 组件零 `ReferenceError`。

详见 [`docs/cpp-host-plan.md`](../docs/cpp-host-plan.md)。

