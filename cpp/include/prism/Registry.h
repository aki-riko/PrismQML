// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 注入装配 (镜像 Python core/utils.py register_types)
#pragma once

#include <QString>

class QQmlEngine;

namespace prism {

// registerTypes - 向 QML 引擎注入 context 对象 + import path
// 镜像 Python register_types(engine): setContextProperty + addImageProvider + addImportPath
//
// 阶段 1: 仅注入 ThemeManager (已验证最小可行集) + addImportPath。
// 其余 8 个注入对象 (ShadowManager/ConfigManager/MicaManager/Clipboard/
// NativeWindow/QRCode/ScreenEyedropper/WindowHelper) + 2 个 imageProvider
// (svg/qrcode) 留待后续阶段补齐 (见 docs/cpp-host-plan.md 第八节映射表)。
void registerTypes(QQmlEngine *engine, const QString &importPath);

// 解析 PrismQML 模块的 import path 父目录 (镜像 Python qml_path().parent)。
// 优先用环境变量 PRISMQML_QML_DIR; 否则用传入的 fallback。
QString resolveImportPath(const QString &fallback = QString());

// qml_path - 获取 QML module 根目录 (镜像 Python core/utils.py qml_path)。
// 返回 `module PrismQML` 所在目录本身 (= resolveImportPath 的父路径下的 PrismQML 子目录);
// relative 非空时返回该目录下的子路径。import path 应指向本目录的父 (见 register_types)。
QString qml_path(const QString &relative = QString());

}  // namespace prism
