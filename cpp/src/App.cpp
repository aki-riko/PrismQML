// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - App 实现 (镜像 Python window/app.py)
#include "prism/App.h"
#include "prism/ConfigContracts.h"
#include "prism/Registry.h"
#include "prism/ShadowManager.h"
#include "prism/Updater.h"
#include "prism/WindowHelper.h"

#include <QApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickWindow>
#include <QSGRendererInterface>
#include <QObject>
#include <QDebug>

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

void configureQmlEnvironment(bool allowFileRead) {
    qputenv(kQmlXhrAllowFileReadEnvironment, allowFileRead ? "1" : "0");
    QQuickWindow::setDefaultAlphaBuffer(true);
}

App::App(int &argc, char **argv, const QString &importPath, bool allowQmlFileRead) {
    if (s_instance != nullptr) {
        qFatal("prism::App already exists. Only one instance allowed.");
    }
    s_instance = this;

    // Translator 用 XMLHttpRequest 加载 i18n/*.json；App 构造是显式初始化边界。
    configureQmlEnvironment(allowQmlFileRead);

    // 高 DPI 透传 (镜像 Python: PassThrough); 静态方法继承自 QGuiApplication
    QApplication::setHighDpiScaleFactorRoundingPolicy(
        Qt::HighDpiScaleFactorRoundingPolicy::PassThrough);

    // 固定 DPI 缩放配置 (必须在 QApplication 创建前; 镜像 Python applyDpiScale)
    applyDpiScaleBeforeApplication();

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
    // QML 托盘菜单依赖 m_engine，必须先于引擎销毁。
    m_systemTrays.clear();
    s_instance = nullptr;
}

void App::onPause(std::function<void()> cb) { m_onPause = std::move(cb); }
void App::onResume(std::function<void()> cb) { m_onResume = std::move(cb); }

Updater *App::enableAutoUpdate(const QString &repo,
                              const QString &currentVersion,
                              const QString &assetKeyword) {
    if (!m_engine) {
        qWarning() << "App::enableAutoUpdate: 引擎未就绪，无法启用自动更新";
        return nullptr;
    }
    // 以最后一次调用为准，重建底层 Updater。
    // App 非 QObject，故 parent 传 nullptr，所有权由 m_updater(unique_ptr) 独占。
    m_updater = std::make_unique<Updater>(repo, currentVersion, assetKeyword, nullptr);
    m_updater->setRequireArtifactDigest(true);
    m_engine->rootContext()->setContextProperty(QStringLiteral("appUpdater"),
                                                m_updater.get());
    return m_updater.get();
}

void App::setApplicationIcon(const QString &icon, bool colored) {
    if (icon.isEmpty()) {
        qWarning() << "App::setApplicationIcon: 图标来源不能为空";
        return;
    }
    m_applicationIcon = icon;
    m_applicationIconColored = colored;
    WindowHelper::instance()->setAppIcon(icon);
    for (const auto &window : m_windows)
        window->setWindowIcon(icon, colored);
}

Window &App::createWindow(WindowType type) {
    m_windows.push_back(
        std::make_unique<Window>(m_engine.get(), m_importPath, type));
    if (!m_applicationIcon.isEmpty())
        m_windows.back()->setWindowIcon(m_applicationIcon,
                                        m_applicationIconColored);
    return *m_windows.back();
}

SystemTrayIcon &App::createSystemTrayIcon(const QString &icon,
                                          const QString &toolTip,
                                          bool menuOnLeftClick) {
    const QString effectiveIcon = icon.isEmpty() ? m_applicationIcon : icon;
    m_systemTrays.push_back(std::make_unique<SystemTrayIcon>(
        effectiveIcon, toolTip, nullptr, m_engine.get(), menuOnLeftClick));
    return *m_systemTrays.back();
}

int App::exec() {
    return m_app->exec();
}

}  // namespace prism

#include "App.moc"
