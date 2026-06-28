// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Window 实现 (镜像 Python _window_builder.py 的字符串拼接 + loadData)
#include "prism/Window.h"

#include <QQmlEngine>
#include <QQmlComponent>
#include <QObject>
#include <QUrl>
#include <QDir>
#include <QDebug>

namespace prism {

Window::Window(QQmlEngine *engine, const QString &importPath, WindowType type)
    : m_engine(engine), m_importPath(importPath), m_type(type) {
    build();
}

Window::~Window() {
    if (m_root)
        m_root->deleteLater();
}

// 镜像 Python _escape_qml: 转义用户字符串防 QML 注入
QString Window::escapeQml(const QString &text) {
    QString t = text;
    t.replace(QLatin1String("\\"), QLatin1String("\\\\"));
    t.replace(QLatin1String("\""), QLatin1String("\\\""));
    t.replace(QLatin1String("\n"), QLatin1String("\\n"));
    t.replace(QLatin1String("\r"), QLatin1String("\\r"));
    t.replace(QLatin1String("\t"), QLatin1String("\\t"));
    t.replace(QLatin1String("{"), QLatin1String("\\u007B"));
    t.replace(QLatin1String("}"), QLatin1String("\\u007D"));
    return t;
}

// 镜像 Python _WINDOW_TYPE_QML_NAMES
QString Window::qmlComponentName(WindowType type) {
    switch (type) {
        case WindowType::Split:  return QStringLiteral("WindowsSplit");
        case WindowType::Bar:    return QStringLiteral("WindowsBar");
        case WindowType::Filled: return QStringLiteral("WindowsFilled");
    }
    return QStringLiteral("WindowsBar");
}

void Window::build() {
    // PrismQML 模块根目录 = importPath/PrismQML (as_posix 风格的 file url)
    QString qmlDir = QDir(m_importPath).filePath(QStringLiteral("PrismQML"));
    qmlDir = QDir::fromNativeSeparators(qmlDir);  // 反斜杠 -> 正斜杠

    const QString component = qmlComponentName(m_type);

    // 镜像 _window_builder 的 window_qml 拼接 (阶段1: 不含导航项/页面容器)
    const QString qml = QStringLiteral(
        "import QtQuick\n"
        "import \"file:///%1\"\n"
        "import \"file:///%1/_internal\"\n"
        "\n"
        "%2 {\n"
        "    id: window\n"
        "    objectName: \"mainWindow\"\n"
        "    width: %3\n"
        "    height: %4\n"
        "    windowTitle: \"%5\"\n"
        "    lazyLoading: false\n"
        "    navigationItems: []\n"
        "    bottomNavigationItems: []\n"
        "}\n"
    ).arg(qmlDir, component)
     .arg(m_width).arg(m_height)
     .arg(escapeQml(m_title));

    auto *comp = new QQmlComponent(m_engine);
    comp->setData(qml.toUtf8(), QUrl(QStringLiteral("inline-prism-window")));

    if (comp->isError()) {
        qWarning() << "prism::Window 加载失败:";
        for (const auto &e : comp->errors())
            qWarning().noquote() << "  " << e.toString();
        comp->deleteLater();
        return;
    }

    m_root = comp->create();
    if (!m_root) {
        qWarning() << "prism::Window create() 返回空";
        for (const auto &e : comp->errors())
            qWarning().noquote() << "  " << e.toString();
    }
    comp->setParent(m_root ? m_root : nullptr);  // 组件随根对象释放
}

void Window::setWindowTitle(const QString &title) {
    m_title = title;
    if (m_root)
        m_root->setProperty("windowTitle", title);
}

void Window::resize(int width, int height) {
    m_width = width;
    m_height = height;
    if (m_root) {
        m_root->setProperty("width", width);
        m_root->setProperty("height", height);
    }
}

void Window::show() {
    if (m_root) {
        // WindowsCore 根类型是 QtQuick Window: 设 visible 显示
        m_root->setProperty("visible", true);
    }
}

}  // namespace prism
