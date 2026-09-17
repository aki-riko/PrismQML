# PrismQML C++ 宿主 - Android 构建指南

> 让 `prism` C++ 宿主在 Android 上构建运行。本文档基于实测约束编写。
> iOS 需 macOS + Xcode，Windows 上无法构建，故本文聚焦 Android。

## 现状与约束（实测）

- **代码层已就绪**：`prism` 库已做平台条件编译（`include/prism/Platform.h`）。
  窗口装饰（阴影/云母/无边框）有 `Q_OS_WIN` 守卫，Android 自动降级为无操作；
  `Window.show()` 在移动端走全屏；`PlatformInfo` 提供触摸适配地基。
- **工具链需另装**（本机当前无）：Qt for Android + Android SDK + NDK + JDK，
  合计约 7GB。下面给出完整步骤。

## 一、Qt for Android

Qt for Android **依赖同版本 desktop Qt**（提供 moc/qmlcachegen 等主机工具）。
构建机必须同时安装同版本的 desktop Qt 与目标 Android kit。

### aqt 安装（注意 6.11.x 的坑）

```bash
# host 是 all_os (Qt 6.8+ 移动/wasm 用 all_os, 非 windows)
python -m aqt install-qt all_os android 6.11.1 android_arm64_v8a --outputdir <qt-install-root>
```

⚠️ **aqt 3.3.0 装不了 6.11.x**（qt.io 改了目录结构，aqt 拼出双重路径
`qt6_6111/qt6_6111/Updates.xml` → 404，官方 issue #1007 未修）。两个办法：
1. **降到 6.10.3**（aqt 可装）：`python -m aqt install-qt all_os android 6.10.3 android_arm64_v8a`
   —— PrismQML 仅需 Qt 6.9+（RectangularShadow），6.10.3 满足。
2. **手动拉 .7z**（参考 `fetch_qt6111.py` 同法，URL 规则见
   `docs/cpp-host-plan.md` §1.1：`<BASE>/<packageName>/<full_version><archive>`，
   android 的 BASE 在 `.../qt6_6111/qt6_6111_android_arm64_v8a`）。

## 二、Android SDK / NDK / JDK

最省事用 Android Studio（自带 SDK Manager + JBR）：
- **JDK**：Android Studio 自带 `jbr`（或装 Temurin JDK 17）。
- **SDK**：通过 Android Studio SDK Manager 装 platform-tools + platform
  (API 34) + build-tools。
- **NDK**：SDK Manager 装 NDK（Qt 6.11 推荐 r26b，以 Qt 文档为准）。

构建脚本不保存个人机器路径，运行前在当前终端设置以下环境变量：

```bat
set "JAVA_HOME=<JDK 17 directory>"
set "ANDROID_SDK_ROOT=<Android SDK directory>"
set "ANDROID_NDK_ROOT=<Android NDK directory>"
set "QT_HOST_PATH=<desktop Qt directory>"
set "QT_ANDROID_CMAKE=<Qt Android kit>\bin\qt-cmake.bat"
set "NINJA=<ninja executable>"
```

`build_android.bat`、`build_android_apk.bat` 使用 arm64 Qt kit；
`build_android_x64.bat` 使用 x86_64 Qt kit。需要自定义构建目录时设置
`PRISM_ANDROID_BUILD_DIR`，否则脚本写入仓库根目录 `.artifacts/cpp/` 下的对应目录。

## 三、构建 prism for Android

Qt for Android 用 `qt-cmake`（封装了 Android 工具链链）。设置上述环境变量后，
在仓库根目录直接运行对应脚本：

```bat
cpp\build_android.bat
cpp\build_android_apk.bat
cpp\build_android_x64.bat
```

也可手工执行等价命令：

```bash
# qt-cmake 在 Qt android 目录的 bin 下
"%QT_ANDROID_CMAKE%" ^
  -S cpp -B .artifacts/cpp/android-arm64 ^
  -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DANDROID_ABI=arm64-v8a ^
  -DQT_ANDROID_BUILD_ALL_ABIS=OFF

cmake --build .artifacts/cpp/android-arm64
```

`qt-cmake` 会自动设 `CMAKE_TOOLCHAIN_FILE` 指向 NDK 的 android.toolchain.cmake
并注入 Qt 的 Android 部署支持。产物 apk 在 `.artifacts/cpp/android-arm64` 下。

### CMakeLists 已就绪点

- `prism` 链接的 Qt 模块（Core/Gui/Qml/Quick/Svg/Widgets/Network/Sql）在
  Qt for Android 均可用。
- 平台专属代码（DWM 等）已 `#ifdef Q_OS_WIN`，Android 编译走降级分支。

## 四、移动端运行时差异（已在代码处理）

| 能力 | 桌面 | Android |
|------|------|---------|
| 窗口 | 无边框 + 三布局 | 全屏单窗口（`Window.show()` 用 FullScreen） |
| 阴影/云母/无边框 | DWM | 降级无操作 |
| 系统托盘 | QSystemTrayIcon | `isAvailable()` 返回 false |
| 单实例 | QSharedMemory | 移动端单实例语义不同（系统管理生命周期） |
| 自动更新 | QNetwork 下载 exe | 禁用（须走应用商店） |
| 触摸 | 鼠标 hover | `PlatformInfo.isTouch=true`, touchTargetSize=48 |

## 五、QML 触摸适配（已完成，见 §六）

引擎 QML 控件原为鼠标桌面设计，移动端适配已按统一规范完成，覆盖
`prismqml/PrismQML` 下所有在**代码**里使用 hover 原语的 QML 文件（公开控件 +
`_internal` 委托，共 92 个文件）。

### 适配约定（`prismqml/PrismQML/Touch.qml` 单例，由 qmldir 注册）

| 规则 | 用法 | 桌面语义（不变式） |
|------|------|-------------------|
| R1 视觉反馈 | `Touch.feedback(hovered, pressed)` | `=== hovered` |
| R2 hover 揭示 | `Touch.reveal(hovered)` | `=== hovered` |
| R3 指针专属 | `!Touch.isTouch && <原表达式>` | `=== <原表达式>` |
| R4 尺寸 | `Touch.target(size)`，或 `Enums.*` token 的 `touchTargetFloor` | `=== size` / 原字面值 |

- **触摸反馈采用"按压驱动"**：Qt 会把触摸按压合成为 hover 且松手后不派发 leave，
  直接采信 `hovered` 会留下残留高亮；因此触摸端 hover 视觉只在按压期间生效。
- **尺寸下限**：`Enums`/`SkinContext` 把 `Touch.minTargetSize`（触摸 48 / 桌面 0）
  注入 `Metrics.touchTargetFloor`，26 个交互 token 以
  `Math.max(原值, root.touchTargetFloor)` 表达；本地字面值控件在消费点包
  `Touch.target(...)`。字形/圆点/指示条/滑轨尺寸不放大。
- **桌面不变式**：非触摸平台（Python 宿主无 `PlatformInfo`，桌面 C++ 宿主
  `isTouch=false`）全部规则退化为原表达式，桌面像素与行为零变化。

### 门禁

```powershell
# 代码级扫描: 每个 hover 文件必须引用 Touch. 或进入带理由的豁免表;
# 同时锁定 Touch 单例注册、交互 token 下限、两个 hover 入参助手的喂入方
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 300 -- .\.venv\Scripts\python.exe -m pytest tests\tooling\test_touch_adaptation_gate.py
# 触摸分支全组件加载（RELEASING.md 规定触摸改动必跑）
.\.venv\Scripts\python.exe scripts\test_process.py --qt-platform offscreen --timeout 180 -- .\.venv\Scripts\python.exe tests\qml\probe_all_components.py --touch
```

### 响应式（宿主注入 `PlatformInfo`）

`PlatformInfo`（isMobile/isCompact/touchTargetSize）由 C++ 宿主注入 QML context，
控件可防御式读取；窄屏底部 Tab 已由 `BottomTabBar` + `WindowsBar` 承担切换。

### 已知触摸尺寸例外（需父级几何配合，本次未抬到 48dp）

这些交互目标的放大必须同时改父级固定几何或弹层宽度，否则会溢出/裁切或互相抢命中，
按 R4 规则"跳过并说明"处理：

| 目标 | 现状 | 阻塞原因 |
|------|------|----------|
| `DatePicker/_internal/CalendarNavButton` | 32×34 | 弹层 `calendarPopupHeight=300` 可用约 276px，桌面已用 34+32+216=282px；抬到 48 会把日历网格挤出弹层 |
| `navigation/PipsPager` 上一个/下一个按钮 | 20×20 | `PipsPagerCore._cellSize=12` 步距下每侧仅约 24px 余量，48px 命中区会与圆点区重叠 |
| `ColorPicker/_internal/ColorPalette` 色块 | 28 | 10 列固定网格 + `palettePopupWidth=360`，28→48 会溢出被裁切 |
| 图表 `ChartBottomLegend` 图例项 | 32 | 图表区只预留固定 32px 图例带，需同时改各图表的预留高度 |
| `controlSize.lineEditClearButtonSize` | 20 | 位于 32px 输入框内，需为该按钮单独做透明命中区扩展 |

其余交互尺寸已在 token 层（`root.touchTargetFloor`）或在消费点（`Touch.target`）抬到 ≥48。

## 六、状态

- ✅ 代码层条件编译就绪，桌面零回归
- ✅ PlatformInfo 触摸适配地基（测试验证）
- ✅ **工具链全装齐**：Qt 6.10.3 android_arm64_v8a + JDK 17 + Android SDK
  (cmdline-tools / platform-tools / android-34+35 / build-tools 34 / NDK r27c)
- ✅ **交叉编译通过**：libprism.a / libprism_demo_arm64-v8a.so（NDK r27c, arm64-v8a）
- ✅ **QML 资源 qrc 打包**：rcc 预编译 2880 个资源(323 qml/29 qmldir/2497 svg/
  20 json + demo pages)嵌入 so（4.9MB→9.7MB）
- ✅ **完整 apk 构建成功**：`prism_demo.apk`（arm64 52MB / x86_64 74MB），
  `cpp/build_android.bat`(arm64) / `build_android_x64.bat`(x86_64) 一键构建。
- ✅ **真机(emulator)运行成功**：x86_64 apk 在 Android emulator(WHPX 加速)端到端
  跑通——Qt platform plugin started → prism::App+ThemeManager(accent #F97316) →
  SqlListModel 查 10 行 → addPage 4 页 → DEMO_OK 窗口创建 → 进程常驻 → 截屏
  320x640/94 色/非黑 80% UI 真实渲染。
- 🟡 触摸适配：导航壳层窄屏底部 Tab 已做（BottomTabBar + WindowsBar 响应式，
  程序化验证 nb/bt visible 切换）；80 控件的触摸态/尺寸细化为渐进工作（PlatformInfo
  地基已备）。
- ✅ **arm64 真机运行成功**：OnePlus PKG110 / Android 16 / arm64-v8a / 1264×2780 /
  density 560（逻辑宽 ≈361dp，走窄屏 compact 分支）。`cpp/build_android_apk.bat`
  → debug keystore + `apksigner` 签名 → `adb install`：`DEMO_OK` + 进程常驻；
  底部 Tab 点击可切换页面（用户页 10 行 SqlListModel 渲染、设置页 skin=fluent）；
  触摸按压期间显示高亮反馈、松手后无 hover 残留。首次运行前必须先修下方
  "资源模块的静态 QML 插件必须显式注册"，否则根窗口创建失败、进程秒退(退出码 2)。
- ✅ **触摸适配完成**：92 个 hover 依赖 QML 文件按 §五 的 R1–R5 规则适配，桌面逐像素
  零变化；门禁为 `tests/tooling/test_touch_adaptation_gate.py` + `probe_all_components.py
  --touch`，另有 `tests/qml/test_touch_adaptation.py` 锁定桌面 token 原值与触摸语义。


### 关键踩坑记录

- **x86 主机 emulator 不支持 arm64 镜像**（新版 emulator 移除 arm 转译）→ 真机
  验证须 x86_64 apk(补装 Qt android_x86_64) + x86_64 系统镜像。
- **apk 必须签名**才能装（release apk 无签名报 INSTALL_PARSE_FAILED_NO_CERTIFICATES）
  → debug keystore + apksigner。
- **QML 模块必须链接对应 Qt target**：WindowsBar 依赖 QtQuick.Effects/Layouts，
  qmlimportscanner 扫不到 qrc/运行时拼接的 import → prism 链接 Qt6::QuickEffects/
  QuickLayouts/QuickControls2, androiddeployqt 据链接依赖打包 QML plugin。
  (QuickShapes 无公开 Config 只有 Private, 不能 find_package。)
- **AVD config sysdir 路径重复**(android-sdk\ 前缀) → 改 config.ini image.sysdir.1。
- **虚拟化"已开"判断**: Hyper-V 运行时 WMI VirtualizationFirmwareEnabled 报 False
  是表象(宿主跑在 hypervisor 上), 实际 WHPX 加速可用。
- **Gradle 必须配代理**：~/.gradle/gradle.properties systemProp.https.proxyHost/Port。
- **compileSdk 要 android-35**：AGP AAR metadata 检查要求。
- **QML 资源用 rcc 显式预编译**：AUTORCC 对 CMake 生成的 .qrc 不可靠。
- **QT_HOST_PATH 必传** desktop Qt 路径(取 moc/rcc 主机工具)。
- **资源模块的静态 QML 插件必须显式注册**：CMake 为 qrc 模块生成
  `prismqml_runtime_qmldir`，其中带 `plugin prismqmlruntimeplugin` +
  `classname PrismQMLRuntimePlugin`；该插件以 `QT_PLUGIN;QT_STATICPLUGIN` 编进
  libprism。桌面/PySide 走磁盘模块的**无插件** qmldir，所以问题只在 qrc 路径暴露：
  Android 链接器会丢弃没有被引用的静态插件注册符号，资源模块加载即报
  `module "PrismQML" plugin "prismqmlruntimeplugin" not found`，`Window::build()`
  失败 → `DEMO_FAIL` → 进程以退出码 2 秒退。修法：宿主入口保留
  `cpp/src/App.cpp` 的 `Q_IMPORT_QML_PLUGIN(PrismQMLRuntimePlugin)`（测试用
  `Q_IMPORT_QML_PLUGIN` 早就这么做了，宿主缺这一步）。
- **Android release 应用丢弃 stderr**：Qt 的 qInfo/qWarning 在真机上默认不可见，
  `log.redirect-stdio` 只对 debuggable 应用生效。`cpp/demo/main.cpp` 在
  `Q_OS_ANDROID` 下安装 `qInstallMessageHandler` 把消息转发到 logcat（tag
  `PrismQML`），否则只会看到"进程秒退"而拿不到 QML 错误。
- **release apk 与 debug keystore 的签名冲突**：换密钥重建后 `adb install -r` 会报
  `INSTALL_FAILED_UPDATE_INCOMPATIBLE`，需先 `adb uninstall <pkg>`；78MB 的 apk 用
  `adb install` 流式安装可能超时，改成 `adb push /data/local/tmp/` + `pm install -r -t`
  更稳。
- **`addPage` 早于 `show()` 会打印"未找到页面容器 page_N"**：此时窗口 QML 尚未
  `build()`，容器还不存在；页面会在首次 `navigateTo` 时正常加载（真机点击 Tab 即渲染），
  该警告不表示页面不可用。
