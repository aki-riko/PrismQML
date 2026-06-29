// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// androiddeployqt 的 qmlimportscanner 扫描 qml-root-path(cpp/) 下的 .qml 找 import,
// 据此决定打包哪些 Qt QML 模块(qmldir/qmltypes 进 android_rcc_bundle.rcc)。
// PrismQML 引擎 QML 在自建 qrc + 窗口 QML 是 C++ 运行时字符串拼接, scanner 静态
// 扫不到这些 import → 不打包对应模块 → 运行时 "module not installed"。
// 本文件显式声明引擎用到的全部 Qt QML 模块, 让 scanner 发现并打包。仅供扫描, 不实例化。
import QtQuick
import QtQuick.Window
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Shapes
import QtQuick.Dialogs

Item {}
