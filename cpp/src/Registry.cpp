// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 注入装配实现 (镜像 Python register_types)
#include "prism/Registry.h"
#include "prism/ThemeManager.h"

#include <QQmlEngine>
#include <QQmlContext>
#include <QProcessEnvironment>

namespace prism {

void registerTypes(QQmlEngine *engine, const QString &importPath) {
    QQmlContext *ctx = engine->rootContext();

    // 注入 ThemeManager (单例, 与 Python ThemeManager() 单例对齐)
    // 已 probe 验证: 注入后 Enums.qml 的 6 个 ThemeManager 引用全部解析。
    ctx->setContextProperty(QStringLiteral("ThemeManager"), ThemeManager::instance());

    // TODO(阶段2): ShadowManager / ConfigManager / MicaManager / ClipboardHelper /
    //              NativeWindow / QRCodeGenerator / ScreenEyedropperManager / WindowHelper
    // TODO(阶段2): engine->addImageProvider("svg", ...) / ("qrcode", ...)

    // 添加 import path (镜像 Python addImportPath(qml_path().parent))
    // Qt 会扫描 <importPath>/PrismQML/qmldir
    if (!importPath.isEmpty())
        engine->addImportPath(importPath);
}

QString resolveImportPath(const QString &fallback) {
    const QString env = QProcessEnvironment::systemEnvironment()
                            .value(QStringLiteral("PRISMQML_QML_DIR"));
    if (!env.isEmpty())
        return env;
    return fallback;
}

}  // namespace prism
