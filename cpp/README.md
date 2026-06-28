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

## 运行 demo

```bash
export PATH="$QTDIR/bin:$PATH"
export PRISMQML_QML_DIR="<repo>/prismqml"   # 指向 PrismQML 模块的父目录
./cpp/build/prism_demo.exe
```

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
    w.addPage("pages/HomePage.qml", "Home", "首页");
    w.addPage("pages/SettingsPage.qml", "Settings", "设置");
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
| 日志 | `prism::log`（debug/info/warning/error + Qt 重定向） | core/logger.py |
| 系统托盘 | `SystemTrayIcon` | window/system_tray.py |
| 单实例 | `SingleInstance` | core/single_instance.py |

### 尚未移植（按需补充）

- `Icon` / `IconProvider`：QML 控件用自带 `FluentEnums/Icons.qml`，不经 context，
  故 C++ 渲染不依赖它；仅当 C++ 代码需查图标值时才需补。
- `QRCodeGenerator` / `ScreenEyedropperManager`：特定功能模块。
- `Updater`：自动更新（移动端禁用）。
- 数据模型 `TableListModel` / `SqlListModel` / `DbRouter`：底层 Rust（`prismqml_rs`），
  C++ 可直接 FFI，比 Python 绑定更自然。

## 作为库集成

安装后其他 CMake 项目可直接消费：

```cmake
find_package(prism REQUIRED)        # 自动转发 Qt6 依赖
target_link_libraries(myapp PRIVATE prism::prism)
```

```bash
cmake --install cpp/build --prefix <你的安装前缀>
```

## 平台说明

- **桌面（Windows / macOS / Linux）**：全部能力可用。DWM 阴影 / Mica / 无边框
  为 Windows 原生；非 Windows 平台对应 `#ifdef` 降级为无操作。
- **移动 / WASM**：窗口装饰（托盘 / 云母 / 无边框 / 单实例 / 自动更新）在这些平台
  物理不存在，按平台条件编译降级；触摸适配需另行处理（控件原为鼠标桌面设计）。

## 验证状态

- Qt 6.11.1 + MSVC 全量编译链接通过。
- demo 真实平台渲染：1823×1256，96 种颜色，accent 色 `#F97316` 像素级命中
  （C++ ThemeManager 注入值流到渲染）。
- `prism_test_store`：Store 11 项断言 + Logger 全部通过。
- QML 加载真实 PrismQML 组件零 `ReferenceError`。

详见 [`docs/cpp-host-plan.md`](../docs/cpp-host-plan.md)。

