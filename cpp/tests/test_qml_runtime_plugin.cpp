// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML runtime plugin integration test.
// PrismQML 运行时插件集成测试。

#include <QApplication>
#include <QEventLoop>
#include <QFile>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQmlError>
#include <QPluginLoader>
#include <QUrl>
#include <QTimer>
#include <QtQml/qqmlextensionplugin.h>

#include <memory>
#include <cstdio>

Q_IMPORT_QML_PLUGIN(PrismQMLRuntimePlugin)

namespace {

int fail(const QQmlComponent &component, const char *message) {
    std::fprintf(stderr, "%s\n", message);
    for (const QQmlError &error : component.errors()) {
        const QByteArray text = error.toString().toUtf8();
        std::fprintf(stderr, "%s\n", text.constData());
    }
    std::fflush(stderr);
    return 1;
}

}  // namespace

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    if (!QFile::exists(QStringLiteral(":/qt/qml/PrismQML/qmldir"))) {
        std::fprintf(stderr, "Embedded PrismQML qmldir is not registered\n");
        return 1;
    }

    bool pluginRegistered = false;
    for (const QStaticPlugin &plugin : QPluginLoader::staticPlugins()) {
        const QString className =
            plugin.metaData().value(QStringLiteral("className")).toString();
        if (className == QStringLiteral("PrismQMLRuntimePlugin")) {
            pluginRegistered = true;
            break;
        }
    }
    if (!pluginRegistered) {
        std::fprintf(stderr,
                     "PrismQMLRuntimePlugin is absent from the static plugin registry\n");
        return 1;
    }

    {
        QQmlEngine engine;
        const QString resourceImportPath = QStringLiteral("qrc:/qt/qml");
        if (!engine.importPathList().contains(resourceImportPath)) {
            const QByteArray paths = engine.importPathList().join(QLatin1Char(';')).toUtf8();
            std::fprintf(stderr, "Missing default QML resource import path: %s\n",
                         paths.constData());
            return 1;
        }
        QQmlComponent component(&engine);
        component.setData(R"QML(
import QtQuick
import PrismQML

Item {
    readonly property bool runtimeReady:
        typeof ThemeManager !== "undefined"
        && typeof PlatformInfo !== "undefined"
        && Enums.fontFamily.length > 0

    LineEdit {
        id: input
        placeholderText: "Runtime probe"
    }
}
)QML", QUrl(QStringLiteral("inline:PrismQMLRuntimeProbe")));
        if (component.status() == QQmlComponent::Loading) {
            QEventLoop loop;
            QTimer timeout;
            timeout.setSingleShot(true);
            QObject::connect(&component, &QQmlComponent::statusChanged,
                             &loop, &QEventLoop::quit);
            QObject::connect(&timeout, &QTimer::timeout,
                             &loop, &QEventLoop::quit);
            timeout.start(10'000);
            while (component.status() == QQmlComponent::Loading
                   && timeout.isActive()) {
                loop.exec();
            }
        }

        if (component.isError())
            return fail(component, "PrismQML runtime component failed to compile");

        std::unique_ptr<QObject> object(component.create());
        if (!object)
            return fail(component, "PrismQML runtime component failed to instantiate");
        if (!object->property("runtimeReady").toBool())
            return fail(component, "PrismQML runtime context was not injected");
        if (!engine.rootContext()->contextProperty(QStringLiteral("ThemeManager")).isValid())
            return fail(component, "ThemeManager is absent from the engine root context");
        if (!engine.rootContext()->contextProperty(QStringLiteral("PlatformInfo")).isValid())
            return fail(component, "PlatformInfo is absent from the engine root context");
        object.reset();
    }
    return 0;
}
