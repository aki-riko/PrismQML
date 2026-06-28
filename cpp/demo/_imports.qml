// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// import 提示文件: 让 androiddeployqt 的 qmlimportscanner 发现 PrismQML 引擎
// 运行时(qrc/字符串拼接)用到的全部 QML 模块, 确保它们被打进 apk。
// PrismQML 引擎 QML 在 qrc 里且窗口 QML 是 C++ 运行时拼接, scanner 静态扫不到,
// 故用本文件显式声明依赖。不被实例化, 仅供扫描。
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Dialogs
import QtQuick.Controls
import QtQuick.Shapes

Item {}
