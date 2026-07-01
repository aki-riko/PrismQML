// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - App 实现 (镜像 Python window/app.py)
#include "prism/App.h"
#include "prism/Registry.h"
#include "prism/ShadowManager.h"

#include <QApplication>
#include <QQmlApplicationEngine>
#include <QQuickWindow>
#include <QSGRendererInterface>
#include <QObject>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>

namespace prism {

// 中转 Qt applicationStateChanged 信号到 App 的 onPause/onResume 回调
class AppLifecycleBridge : public QObject {
    Q_OBJECT
public:
    AppLifecycleBridge(App *owner, QApplication *app, QObject *parent = nullptr)
        : QObject(parent), m_owner(owner) {
        connect(app, &QApplication::applicationStateChanged,
                this, &AppLifecycleBridge::onStateChanged);
    }
public slots:
    void onStateChanged(Qt::ApplicationState state) {
        // Active=前台; Suspended/Hidden/Inactive=后台 (移动端切走/锁屏)
        if (state == Qt::ApplicationActive) {
            if (m_owner->m_onResume) m_owner->m_onResume();
        } else if (state == Qt::ApplicationSuspended || state == Qt::ApplicationHidden) {
            if (m_owner->m_onPause) m_owner->m_onPause();
        }
    }
private:
    App *m_owner;
};

App *App::s_instance = nullptr;

// 在 QApplication 创建前应用 DPI 缩放配置 (镜像 Python config/dpi.py applyDpiScale)。
// 直接读 ~/.prismqml/app.json 的 Window/DpiScale, 不经 ConfigManager(后者依赖 QApplication)。
// DpiScale>0 时设固定缩放(关 Qt 自动 DPI); 0 则跟随系统。
static void applyDpiScaleBeforeApp() {
    const QString path = QDir(QDir::homePath()).filePath(QStringLiteral(".prismqml/app.json"));
    QFile f(path);
    if (!f.open(QIODevice::ReadOnly)) return;
    const QJsonObject root = QJsonDocument::fromJson(f.readAll()).object();
    const int dpiScale = root.value(QStringLiteral("Window")).toObject()
                             .value(QStringLiteral("DpiScale")).toInt(0);
    if (dpiScale > 0) {
        constexpr double kDpiDefault = 100.0;  // 镜像 Python DPI_SCALE_DEFAULT
        qputenv("QT_ENABLE_HIGHDPI_SCALING", "0");
        qputenv("QT_SCALE_FACTOR", QByteArray::number(dpiScale / kDpiDefault));
        qInfo() << "prism::App 应用固定 DPI 缩放:" << dpiScale << "%";
    }
}

App::App(int &argc, char **argv, const QString &importPath) {
    if (s_instance != nullptr) {
        qFatal("prism::App already exists. Only one instance allowed.");
    }
    s_instance = this;

    // 允许 QML 从本地文件读取 (Translator 用 XMLHttpRequest 加载 i18n/*.json)
    // 镜像 Python prismqml/__init__.py: os.environ.setdefault("QML_XHR_ALLOW_FILE_READ","1")
    qputenv("QML_XHR_ALLOW_FILE_READ", "1");

    // 高 DPI 透传 (镜像 Python: PassThrough); 静态方法继承自 QGuiApplication
    QApplication::setHighDpiScaleFactorRoundingPolicy(
        Qt::HighDpiScaleFactorRoundingPolicy::PassThrough);

    // 固定 DPI 缩放配置 (必须在 QApplication 创建前; 镜像 Python applyDpiScale)
    applyDpiScaleBeforeApp();

    // 强制 OpenGL 后端, 规避部分 Windows 驱动 D3D11 device-lost 崩溃
    // (镜像 Python main.py: QQuickWindow.setGraphicsApi(OpenGL))
    QQuickWindow::setGraphicsApi(QSGRendererInterface::OpenGL);

    m_app = std::make_unique<QApplication>(argc, argv);
    m_engine = std::make_unique<QQmlApplicationEngine>();

    m_importPath = resolveImportPath(importPath);

    // 注入装配 (镜像 Python register_types(engine))
    registerTypes(m_engine.get(), m_importPath);

    // 安装 DWM 同步过滤器 (镜像 Python app.py: installDwmSyncFilter())。
    // 消除无边框窗口 resize 撕裂; 非 Windows 内部 no-op。
    ShadowManager::installDwmSyncFilter();

    // 移动端生命周期: 监听应用状态变化 (前台/后台)
    m_lifecycle = std::make_unique<AppLifecycleBridge>(this, m_app.get());
}

App::~App() {
    s_instance = nullptr;
}

void App::onPause(std::function<void()> cb) { m_onPause = std::move(cb); }
void App::onResume(std::function<void()> cb) { m_onResume = std::move(cb); }

Window &App::createWindow(WindowType type) {
    m_windows.push_back(
        std::make_unique<Window>(m_engine.get(), m_importPath, type));
    return *m_windows.back();
}

int App::exec() {
    return m_app->exec();
}

}  // namespace prism

#include "App.moc"
