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
#include "prism/PlatformInfo.h"

#include <QQmlEngine>
#include <QQmlContext>
#include <QProcessEnvironment>
#include <QDir>

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
    // 移动端触摸适配地基 (QML 防御式可选读取 isMobile/isCompact/touchTargetSize)
    ctx->setContextProperty(QStringLiteral("PlatformInfo"), PlatformInfo::instance());

    // ==================== image provider 注入 ====================
    // 引擎接管 provider 所有权(析构时 delete); svg/qrcode 用独立 new 实例。
    engine->addImageProvider(QStringLiteral("svg"), new SvgImageProvider());
    engine->addImageProvider(QStringLiteral("qrcode"), new QRCodeImageProvider());
    // acrylic: AcrylicHelper 单例与 engine 共享同一 provider(grabAndBlur 写/QML 读)。
    // 所有权契约: engine 拥有并在析构时 delete; AcrylicHelper 单例【永不析构】
    // (Meyers 单例)故不会二次释放; 引擎销毁后不再调 grabAndBlur(app 退出阶段)。
    engine->addImageProvider(QStringLiteral("acrylic"),
                             AcrylicHelper::instance()->imageProvider());

    // IconProvider: register_icon_provider(engine) 可注入 "Icon" context, 但
    // 默认【不】注入 — QML 控件用自带 FluentEnums/Icons.qml 不依赖它, 且注入名为
    // "Icon" 的 context property 与 QML Icon 组件类型可能歧义。应用如需可显式调
    // prism::register_icon_provider(engine)。Updater/SqlListModel/TableListModel 按需 new。

    // import path (镜像 addImportPath(qml_path().parent))
    if (!importPath.isEmpty())
        engine->addImportPath(importPath);
}

QString resolveImportPath(const QString &fallback) {
    const QString env = QProcessEnvironment::systemEnvironment()
                            .value(QStringLiteral("PRISMQML_QML_DIR"));
    if (!env.isEmpty())
        return env;
    if (!fallback.isEmpty())
        return fallback;
#if defined(Q_OS_ANDROID) || defined(Q_OS_IOS)
    // 移动端: QML 打进 qrc, import path 指向资源根
    return QStringLiteral("qrc:/");
#else
    // 桌面兜底: 编译期注入的 QML 源/安装目录(CMake 定义 PRISM_QML_DIR_DEFAULT),
    // 使未设 PRISMQML_QML_DIR 环境变量时 import PrismQML 仍可解析(开发树/安装树通用)。
#  ifdef PRISM_QML_DIR_DEFAULT
    {
        const QString def = QStringLiteral(PRISM_QML_DIR_DEFAULT);
        if (!def.isEmpty() && QDir(def).exists())
            return def;
    }
#  endif
    return fallback;
#endif
}

// qml_path - QML module 根目录 (镜像 Python qml_path)。import path 父目录 + "/PrismQML"。
QString qml_path(const QString &relative) {
    const QString parent = resolveImportPath();
    QString base;
    if (parent.isEmpty()) {
        base = QStringLiteral("PrismQML");
    } else if (parent.endsWith(QLatin1Char('/')) || parent.endsWith(QLatin1Char('\\'))) {
        base = parent + QStringLiteral("PrismQML");
    } else {
        base = parent + QStringLiteral("/PrismQML");
    }
    if (relative.isEmpty())
        return base;
    return base + QLatin1Char('/') + relative;
}

}  // namespace prism
