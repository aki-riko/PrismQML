// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - App 实现 (镜像 Python window/app.py)
#include "prism/App.h"
#include "prism/Registry.h"

#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QDebug>

namespace prism {

App *App::s_instance = nullptr;

App::App(int &argc, char **argv, const QString &importPath) {
    if (s_instance != nullptr) {
        qFatal("prism::App already exists. Only one instance allowed.");
    }
    s_instance = this;

    // 允许 QML 从本地文件读取 (Translator 用 XMLHttpRequest 加载 i18n/*.json)
    // 镜像 Python prismqml/__init__.py: os.environ.setdefault("QML_XHR_ALLOW_FILE_READ","1")
    qputenv("QML_XHR_ALLOW_FILE_READ", "1");

    // 高 DPI 透传 (镜像 Python: PassThrough)
    QGuiApplication::setHighDpiScaleFactorRoundingPolicy(
        Qt::HighDpiScaleFactorRoundingPolicy::PassThrough);

    m_app = std::make_unique<QGuiApplication>(argc, argv);
    m_engine = std::make_unique<QQmlApplicationEngine>();

    m_importPath = resolveImportPath(importPath);

    // 注入装配 (镜像 Python register_types(engine))
    registerTypes(m_engine.get(), m_importPath);
}

App::~App() {
    s_instance = nullptr;
}

Window &App::createWindow(WindowType type) {
    m_windows.push_back(
        std::make_unique<Window>(m_engine.get(), m_importPath, type));
    return *m_windows.back();
}

int App::exec() {
    return m_app->exec();
}

}  // namespace prism
