// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// NativeWindow QML consumer test support. NativeWindow QML 消费者测试辅助。
#pragma once

#include <QByteArray>
#include <QCoreApplication>
#include <QEvent>
#include <QEventLoop>
#include <QObject>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QStringList>
#include <QTimer>
#include <QUrl>
#include <QVariantList>
#include <functional>

namespace prism::test {

inline constexpr int kNativeWindowQmlLoadTimeoutMs = 5000;
inline constexpr int kNativeWindowAnimationWaitMs = 400;

inline const QByteArray kNativeWindowFakeQml = QByteArrayLiteral(R"QML(
import QtQml
QtObject {
    property var finalizeOutcomes: []
    property int finalizeCalls: 0
    property int detachCalls: 0
    function finalizeAttach(window) {
        finalizeCalls += 1
        if (finalizeCalls > finalizeOutcomes.length)
            return false
        return finalizeOutcomes[finalizeCalls - 1]
    }
    function detach(window) {
        detachCalls += 1
        return true
    }
}
)QML");

inline const QByteArray kWindowsCoreConsumerQml = QByteArrayLiteral(R"QML(
import PrismQML
WindowsCore {
    visible: false
    shadowMode: Enums.windowShadow.mode_none
    property int readyCount: 0
    onNativeHookReady: readyCount += 1
}
)QML");

struct QmlCreationResult {
    QObject *object = nullptr;
    QQmlComponent::Status status = QQmlComponent::Null;
    QStringList errors;
};

struct WindowsCoreConsumerState {
    bool initializationDone = false;
    bool showAnimationStarted = false;
    bool opacityReady = false;
    bool missingFinalizeMethod = false;
    int readyCount = 0;
};

inline void waitForQml(std::function<bool()> predicate, int timeoutMs) {
    if (predicate())
        return;
    QEventLoop loop;
    QTimer poll;
    poll.setInterval(10);
    QObject::connect(&poll, &QTimer::timeout, [&]() {
        if (predicate())
            loop.quit();
    });
    poll.start();
    QTimer::singleShot(timeoutMs, &loop, &QEventLoop::quit);
    loop.exec();
}

inline QStringList componentErrors(const QQmlComponent &component) {
    QStringList errors;
    for (const QQmlError &error : component.errors())
        errors.append(error.toString());
    return errors;
}

inline QmlCreationResult createNativeWindowFake(
    QQmlEngine &engine, const QVariantList &outcomes) {
    QQmlComponent component(&engine);
    component.setData(
        kNativeWindowFakeQml,
        QUrl(QStringLiteral("inline:p7h-cpp-native-window-fake.qml")));
    waitForQml(
        [&]() { return component.status() != QQmlComponent::Loading; },
        kNativeWindowQmlLoadTimeoutMs);
    QmlCreationResult result;
    result.status = component.status();
    result.errors = componentErrors(component);
    result.object = component.create(engine.rootContext());
    if (result.object)
        result.object->setProperty("finalizeOutcomes", outcomes);
    return result;
}

inline QmlCreationResult createWindowsCoreConsumer(QQmlEngine &engine) {
    QQmlComponent component(&engine);
    component.setData(
        kWindowsCoreConsumerQml,
        QUrl(QStringLiteral("inline:p7h-cpp-native-window.qml")));
    waitForQml(
        [&]() { return component.status() != QQmlComponent::Loading; },
        kNativeWindowQmlLoadTimeoutMs);
    QmlCreationResult result;
    result.object = component.create(engine.rootContext());
    if (result.object)
        result.object->setProperty("visible", true);
    waitForQml([&]() {
        return result.object &&
               result.object->property("_dwmInitializationDone").toBool() &&
               result.object->property("opacity").toDouble() >= 0.99;
    }, kNativeWindowAnimationWaitMs);
    result.status = component.status();
    result.errors = componentErrors(component);
    return result;
}

inline WindowsCoreConsumerState inspectWindowsCoreConsumer(
    QObject *object, const QStringList &messages) {
    WindowsCoreConsumerState state;
    for (const QString &message : messages) {
        state.missingFinalizeMethod |=
            message.contains(QStringLiteral("finalizeAttach")) &&
            (message.contains(QStringLiteral("TypeError")) ||
             message.contains(QStringLiteral("not a function")) ||
             message.contains(QStringLiteral("is not a function")));
    }
    if (!object)
        return state;
    state.initializationDone =
        object->property("_dwmInitializationDone").toBool();
    state.showAnimationStarted =
        object->property("_showAnimationStarted").toBool();
    state.opacityReady = object->property("opacity").toDouble() >= 0.99;
    state.readyCount = object->property("readyCount").toInt();
    return state;
}

class QtMessageCapture {
public:
    explicit QtMessageCapture(QStringList &messages) {
        s_messages = &messages;
        m_previous = qInstallMessageHandler(handleMessage);
    }

    ~QtMessageCapture() {
        qInstallMessageHandler(m_previous);
        s_messages = nullptr;
    }

    QtMessageCapture(const QtMessageCapture &) = delete;
    QtMessageCapture &operator=(const QtMessageCapture &) = delete;

private:
    static void handleMessage(QtMsgType, const QMessageLogContext &,
                              const QString &message) {
        if (s_messages)
            s_messages->append(message);
    }

    inline static QStringList *s_messages = nullptr;
    QtMessageHandler m_previous = nullptr;
};

inline void destroyQmlObject(QObject *object) {
    if (!object)
        return;
    object->deleteLater();
    QCoreApplication::sendPostedEvents(object, QEvent::DeferredDelete);
    QCoreApplication::processEvents();
}

}  // namespace prism::test
