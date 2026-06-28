// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 注入装配实现 (镜像 Python register_types + _window_builder)
#include "prism/Registry.h"
#include "prism/ThemeManager.h"
#include "prism/ConfigManager.h"
#include "prism/ShadowManager.h"
#include "prism/MicaManager.h"
#include "prism/NativeWindow.h"
#include "prism/ClipboardHelper.h"
#include "prism/WindowHelper.h"
#include "prism/AcrylicHelper.h"
#include "prism/SvgImageProvider.h"
#include "prism/QRCodeGenerator.h"
#include "prism/ScreenEyedropper.h"

#include <QQmlEngine>
#include <QQmlContext>
#include <QProcessEnvironment>

namespace prism {

void registerTypes(QQmlEngine *engine, const QString &importPath) {
    QQmlContext *ctx = engine->rootContext();

    // ==================== context 对象注入 (镜像 register_types) ====================
    ctx->setContextProperty(QStringLiteral("ThemeManager"), ThemeManager::instance());
    ctx->setContextProperty(QStringLiteral("ConfigManager"), ConfigManager::instance());
    ctx->setContextProperty(QStringLiteral("ShadowManager"), ShadowManager::instance());
    ctx->setContextProperty(QStringLiteral("MicaManager"), MicaManager::instance());
    ctx->setContextProperty(QStringLiteral("NativeWindow"), NativeWindow::instance());
    ctx->setContextProperty(QStringLiteral("ClipboardHelper"), ClipboardHelper::instance());
    ctx->setContextProperty(QStringLiteral("WindowHelper"), WindowHelper::instance());
    ctx->setContextProperty(QStringLiteral("AcrylicHelper"), AcrylicHelper::instance());
    ctx->setContextProperty(QStringLiteral("QRCodeGenerator"), QRCodeGenerator::instance());
    ctx->setContextProperty(QStringLiteral("ScreenEyedropperManager"),
                            ScreenEyedropperManager::instance());

    // ==================== image provider 注入 ====================
    // 引擎接管 provider 所有权; 用 new 实例避免单例被 engine 析构二次释放。
    engine->addImageProvider(QStringLiteral("svg"), new SvgImageProvider());
    engine->addImageProvider(QStringLiteral("acrylic"),
                             AcrylicHelper::instance()->imageProvider());
    engine->addImageProvider(QStringLiteral("qrcode"), new QRCodeImageProvider());

    // TODO(后续): IconProvider(Icon) — QML 控件实测不调 Icon. context(用自带
    //   FluentEnums/Icons.qml), 故非必需。Updater/SqlListModel 由应用按需 new。

    // import path (镜像 addImportPath(qml_path().parent))
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
