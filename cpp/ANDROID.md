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
本仓库已装 desktop `D:\Qt\6.11.1\msvc2022_64`，需补 android_arm64_v8a。

### aqt 安装（注意 6.11.x 的坑）

```bash
# host 是 all_os (Qt 6.8+ 移动/wasm 用 all_os, 非 windows)
python -m aqt install-qt all_os android 6.11.1 android_arm64_v8a --outputdir D:\Qt
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

设环境变量：
```
ANDROID_SDK_ROOT=C:\Users\<you>\AppData\Local\Android\Sdk
ANDROID_NDK_ROOT=%ANDROID_SDK_ROOT%\ndk\<version>
JAVA_HOME=<jdk path>
```

## 三、构建 prism for Android

Qt for Android 用 `qt-cmake`（封装了 Android 工具链链）：

```bash
# qt-cmake 在 Qt android 目录的 bin 下
D:\Qt\6.11.1\android_arm64_v8a\bin\qt-cmake ^
  -S cpp -B cpp/build-android ^
  -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DANDROID_ABI=arm64-v8a ^
  -DQT_ANDROID_BUILD_ALL_ABIS=OFF

cmake --build cpp/build-android
```

`qt-cmake` 会自动设 `CMAKE_TOOLCHAIN_FILE` 指向 NDK 的 android.toolchain.cmake
并注入 Qt 的 Android 部署支持。产物 apk 在 `build-android` 下。

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

## 五、QML 触摸适配（待完善，见 §六）

引擎 QML 控件原为鼠标桌面设计，移动端需适配：
- 80 个控件依赖 hover（触摸无害降级，但缺触摸反馈）
- 导航壳层 BAR/SPLIT 为侧边栏，窄屏需改底部 Tab/抽屉
- 控件用固定像素尺寸，触摸目标偏小（应 ≥48px）

**适配地基已就绪**：`PlatformInfo`（isMobile/isCompact/touchTargetSize）已注入
QML context，控件可防御式读取做响应式：
```qml
// QML 控件可这样响应式适配 (PlatformInfo 由 C++ 宿主注入)
height: (typeof PlatformInfo !== "undefined" && PlatformInfo.isTouch)
        ? PlatformInfo.touchTargetSize : 32
```

## 六、状态

- ✅ 代码层条件编译就绪，桌面零回归
- ✅ PlatformInfo 触摸适配地基（测试验证）
- ⬜ 真机 apk 构建（需上述 ~7GB 工具链，本机未装）
- ⬜ QML 控件触摸适配（引擎 QML 改动，独立工作量；地基已备）
