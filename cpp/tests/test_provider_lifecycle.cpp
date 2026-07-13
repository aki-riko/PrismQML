// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ImageProvider 双引擎生命周期回归。
#include "prism/AcrylicHelper.h"
#include "prism/Accessors.h"
#include "prism/ConfigManager.h"
#include "prism/Registry.h"
#include "TestProcess.h"

#include <QColor>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QGuiApplication>
#include <QImage>
#include <QQmlEngine>
#include <QTemporaryDir>
#include <memory>

using namespace prism;

static constexpr int kLifecycleCycles = 10;

static bool providerFactoriesAreEngineScoped() {
    std::unique_ptr<SvgImageProvider> svgA(get_svg_provider());
    std::unique_ptr<SvgImageProvider> svgB(get_svg_provider());
    std::unique_ptr<QRCodeImageProvider> qrA(get_qrcode_provider());
    std::unique_ptr<QRCodeImageProvider> qrB(get_qrcode_provider());
    return svgA != svgB && qrA != qrB;
}

static AcrylicImageProvider *acrylicProvider(QQmlEngine &engine) {
    return dynamic_cast<AcrylicImageProvider *>(
        engine.imageProvider(QStringLiteral("acrylic")));
}

static bool writeAcrylicState(QQmlEngine &engine, int cycle, int &imageId) {
    AcrylicImageProvider *provider = acrylicProvider(engine);
    if (!provider)
        return false;
    QImage image(8, 8, QImage::Format_ARGB32);
    image.fill(QColor(cycle % 255, 32, 64, 255));
    const int previousId = provider->currentImageId();
    provider->setImage(image);
    imageId = provider->currentImageId();
    return imageId > previousId;
}

static bool readAcrylicState(QQmlEngine &engine, int expectedId) {
    AcrylicImageProvider *provider = acrylicProvider(engine);
    if (!provider || provider->currentImageId() != expectedId)
        return false;
    QSize actualSize;
    const QImage image = provider->requestImage(QString(), &actualSize, QSize());
    return !image.isNull() && actualSize == QSize(8, 8);
}

static bool runLifecycleCycle(int cycle) {
    int imageId = 0;
    {
        QQmlEngine engineA;
        registerTypes(&engineA, QString());
        if (!writeAcrylicState(engineA, cycle, imageId))
            return false;
    }
    QQmlEngine engineB;
    registerTypes(&engineB, QString());
    return readAcrylicState(engineB, imageId);
}

static bool runLifecycleSuite(const QString &configPath) {
    if (!providerFactoriesAreEngineScoped()) {
        qCritical() << "FAIL: SVG/QRCode provider factory returned a singleton";
        return false;
    }
    for (int cycle = 0; cycle < kLifecycleCycles; ++cycle) {
        if (!runLifecycleCycle(cycle)) {
            qCritical() << "FAIL: provider lifecycle cycle" << cycle;
            return false;
        }
    }
    if (ConfigManager::instance()->getConfigPath() != configPath) {
        qCritical() << "FAIL: ConfigManager did not use isolated path";
        return false;
    }
    return true;
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QTemporaryDir testDirectory(
        QDir::tempPath() + QStringLiteral("/prism-provider-lifecycle-XXXXXX"));
    if (!testDirectory.isValid()) {
        qCritical() << "FAIL: provider lifecycle temporary directory";
        return 2;
    }
    const QString configPath =
        testDirectory.filePath(QStringLiteral("config/app.json"));
    qputenv(kConfigFilePathEnvironment, QFile::encodeName(configPath));
    QGuiApplication app(argc, argv);
    if (!runLifecycleSuite(configPath))
        return 1;
    if (!testDirectory.remove()) {
        qCritical() << "FAIL: provider lifecycle temporary directory cleanup";
        return 1;
    }
    qInfo() << "PROVIDER_LIFECYCLE_PASSED" << kLifecycleCycles;
    return 0;
}
