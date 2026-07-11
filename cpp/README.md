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

- **Qt 6.9+**（C++，与项目 PySide6 最低版本契约对齐）
  - 模块：Core / Gui / Qml / Quick / Svg / Widgets / Network
- **MSVC**（VS 2022 BuildTools，C++17）
- **CMake** 3.16+
- **Python 3.9+**（仅测试工具；QR 端到端解码依赖见 `tests/requirements.txt`）

## 构建

```bat
set "PRISM_VCVARS64=<Visual Studio vcvars64.bat>"
set "QT_HOST_PATH=<desktop Qt directory>"
cpp\build.bat
```

脚本从自身位置定位 `cpp` 源码目录，不保存个人机器路径。需要自定义 CMake
命令或构建目录时，可设置 `PRISM_CMAKE_COMMAND`、`PRISM_DESKTOP_BUILD_DIR`。
手工执行的等价命令如下：

```bat
call "%PRISM_VCVARS64%"
set "PATH=%QT_HOST_PATH%\bin;%PATH%"
cmake -S cpp -B cpp/build -G "NMake Makefiles" ^
  -DCMAKE_BUILD_TYPE=Release "-DCMAKE_PREFIX_PATH=%QT_HOST_PATH%"
cmake --build cpp/build
```

## 运行测试

测试默认随 `PRISM_BUILD_TESTS=ON` 构建。先把 QR 解码依赖安装到当前项目测试环境，
再确认 CMake 配置日志中的 `Found Python3` 指向同一个解释器：

```powershell
.\.venv\Scripts\python.exe -m pip install -r cpp\tests\requirements.txt
ctest --test-dir cpp\build -N
ctest --test-dir cpp\build -L headless --interactive-debug-mode 0 --output-on-failure --no-tests=error
```

默认 headless 集合为 5 个 C++ 测试程序加 1 个 QR 独立解码测试，共 6 项。
CTest 会给每个目标注入 Qt DLL 路径，并统一通过 `scripts/test_process.py` 启动：
测试主体 timeout 为 60 秒，CTest 外层为 110 秒；Qt 平台固定为 `offscreen`，
Windows 下完整进程树在私有 Desktop 与 Job Object 中运行；标准 DLL/崩溃错误框、
WER UI 被配置为无 UI，UCRT 报告重定向到 stderr。即使测试显式创建窗口，也不会
出现在当前用户桌面；runner 会轮询 Job 内持续可见窗口，检测到时记录 HWND/PID/
镜像并返回 126。timeout 返回 124，隔离或清理失败返回 125；正常退出与超时均确认
Job 中后代进程归零。不要绕过 CTest 直接运行 `prism_test_*.exe`。

Windows 11 的 Mica 用例属于显式原生集合，默认不注册。需要验证时重新配置：

```powershell
cmake -S cpp -B cpp\build -DPRISM_BUILD_NATIVE_TESTS=ON
cmake --build cpp\build
ctest --test-dir cpp\build -L native --interactive-debug-mode 0 --output-on-failure --no-tests=error
```

Mica 使用真实 `windows` 平台插件并在私有 Desktop 中运行，但只创建隐藏 HWND，
不调用 `show()`；测试会同时断言 Qt 与 Win32 原生窗口状态始终不可见，再执行
真实 DWM/Mica/阴影调用。
不支持的 Windows 版本以 CTest `Skipped` 明确报告，其余失败均返回非零退出码。

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

`App` 构造时默认调用 `configureQmlEnvironment(true)`，在创建 QML 引擎前启用
Translator 读取本地 i18n JSON 所需的 QML XHR。若直接创建裸
`QQmlApplicationEngine`，必须先显式调用 `configureQmlEnvironment()`；普通链接或
包含头文件不会修改进程环境。不需要本地翻译读取时可使用
`App app(argc, argv, QString(), false)`。

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

### Updater API 根地址

`Updater` 的 API 根地址优先级为：构造函数或 `setApiBaseUrl()` 的显式值、环境变量
`PRISMQML_UPDATER_API_BASE_URL`、默认 `https://api.github.com`。各候选值会去除首尾
空白和尾部 `/`；空值会继续回退到下一优先级。

```cpp
Updater updater("owner/repo", "v1.0.0", "Setup",
                "https://github.example/api/v3");
```

## 已实现能力

| 类别 | C++ API | 镜像的 Python 源 |
|------|---------|------------------|
| 应用入口 | `App`（createWindow / exec / engine / qapp） | window/app.py |
| 窗口 | `Window`（addPage / setWindowTitle / resize / show / navigateTo），三布局 `WindowType` | window_core.py + _window_builder.py + _page_manager.py |
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
- 零交互门禁：headless CTest `6/6`、Windows native Mica `1/1`；调用者 PATH
  去除 Qt/PySide 后 `prism_test_provider_lifecycle` 仍为 `1/1`。对应运行新增
  `Application Popup 26`、`Application Error 1000`、`WER 1001` 与 crash dump 均为 0。
- demo 真实平台渲染：1823×1256，96 种颜色，accent 色 `#F97316` 像素级命中
  （C++ ThemeManager 注入值流到渲染）。
- `prism_test_store`：Store / Logger / Updater 版本比较 + 对称类型（`Logger` /
  `ActivationReason` / `qml_path` / `WindowCore` / `installDwmSyncFilter` /
  `runInstallerAndQuit` 失败路径）共 68 项断言全部通过。
- `prism_test_sqlmodel`：多 shard fan-out 归并 + keyset 升/降序翻页（逐行 ==
  OFFSET 路径）+ 单库回归共 11 项断言通过；破坏谓词方向可复现 FAIL（区分力坐实）。
- `prism_test_qrcode_gen` + `tests/qr/verify_qr.py`：C++ 生成的 QR PNG 由 opencv
  独立解码还原 == 原文，5 组（URL / 中文 / 特殊符号 / 长文本）全部通过。
- `prism_test_provider_lifecycle`：Acrylic provider 顺序注册到两个真实 QML engine，
  销毁前一引擎后后一引擎仍能读取共享图像状态，连续 10 轮无悬空指针或双重释放。
- QML 加载真实 PrismQML 组件零 `ReferenceError`。

详见 [`docs/cpp-host-plan.md`](../docs/cpp-host-plan.md)。
