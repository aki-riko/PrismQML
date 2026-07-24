// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML runtime plugin for externally-owned QQmlEngine instances.
// 为 QtQuickView 等外部持有的 QQmlEngine 自动完成 PrismQML 注入。

#include "prism/Registry.h"

#include <QQmlEngineExtensionPlugin>
#include <QtQml/qqml.h>
#include <QtQml/qqmlmoduleregistration.h>

void qml_register_types_PrismQML() {
    qmlRegisterModule("PrismQML", 1, 0);
}

static const QQmlModuleRegistration prismQMLRegistration(
    "PrismQML", qml_register_types_PrismQML);

class PrismQMLRuntimePlugin final : public QQmlEngineExtensionPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlEngineExtensionInterface_iid)

public:
    void initializeEngine(QQmlEngine *engine, const char *uri) override {
        Q_UNUSED(uri);
        prism::registerTypes(engine, QString());
    }
};

#include "QmlRuntimePlugin.moc"
