// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTray/SingleInstance 运行时烟测 (需 QApplication)
#include "prism/App.h"
#include "prism/ConfigManager.h"
#include "prism/SystemTray.h"
#include "prism/SingleInstance.h"
#include "prism/WindowHelper.h"
#include "../src/IconPath_p.h"
#include "../src/WindowFollower_p.h"
#include "TestProcess.h"

#include <QApplication>
#include <QAction>
#include <QColor>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QGuiApplication>
#include <QImage>
#include <QIcon>
#include <QMenu>
#include <QSystemTrayIcon>
#include <QPoint>
#include <QScreen>
#include <QTemporaryDir>
#include <QUrl>
#include <QVariantMap>
#include <QStringList>

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; ++g_failed; } \
} while (0)

static void testIconPathUrlMatrix() {
    using prism::detail::resolveIconPath;
    const QStringList fileUrls = {
        QStringLiteral("file:///C:/Icons/A%20B/%23mark%25.png"),
        QStringLiteral("file://server/share/A%20B/%23mark.png"),
        QStringLiteral("file:///home/user/A%20B/%23mark%25%3F.svg"),
    };
    bool fileUrlsMatchQt = true;
    for (const QString &source : fileUrls)
        fileUrlsMatchQt &= resolveIconPath(source) == QUrl(source).toLocalFile();
    CHECK(fileUrlsMatchQt, "file URLs follow QUrl::toLocalFile");
    CHECK(resolveIconPath(QStringLiteral("qrc:///icons/A%20B.svg"))
              == QStringLiteral(":/icons/A B.svg"),
          "qrc variants normalize");
}

static void testRealEncodedIcon() {
    using prism::detail::resolveIconPath;
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prismqml-p7k-XXXXXX"));
    const QString path = directory.filePath(QStringLiteral("图 标#百分%.png"));
    QImage image(8, 8, QImage::Format_ARGB32);
    image.fill(QColor(QStringLiteral("#d02040")));
    CHECK(directory.isValid() && image.save(path), "real encoded icon fixture saved");
    const QString source = QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);
    CHECK(resolveIconPath(source) == QUrl(source).toLocalFile(),
          "real encoded icon follows QUrl contract");
    CHECK(!QIcon(resolveIconPath(source)).isNull(),
          "real encoded icon loads after resolution");

    QGuiApplication::setWindowIcon(QIcon());
    prism::WindowHelper::instance()->setAppIcon(source);
    CHECK(!QGuiApplication::windowIcon().isNull(),
          "WindowHelper loads real encoded icon");

    prism::SystemTrayIcon tray;
    tray.setIcon(source);
    QSystemTrayIcon *nativeTray = tray.findChild<QSystemTrayIcon *>();
    CHECK(nativeTray && !nativeTray->icon().isNull(),
          "SystemTrayIcon loads real encoded icon");
}

static void testApplicationIconFacade(prism::App &app) {
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prismqml-app-icon-XXXXXX"));
    const QString path = directory.filePath(QStringLiteral("application.png"));
    QImage image(16, 16, QImage::Format_ARGB32);
    image.fill(QColor(QStringLiteral("#2060d0")));
    CHECK(directory.isValid() && image.save(path),
          "App application icon fixture saved");

    const QString source = QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);
    app.setApplicationIcon(source, false);
    CHECK(app.applicationIcon() == source && !app.applicationIconColored(),
          "App stores application icon state");
    CHECK(!QGuiApplication::windowIcon().isNull(),
          "App publishes the shared Qt icon");

    prism::Window &window = app.createWindow();
    window.show();
    CHECK(window.rootObject()
              && window.rootObject()->property("windowIcon").toString() == source
              && !window.rootObject()->property("windowIconColored").toBool(),
          "App-created window inherits the application icon");

    prism::SystemTrayIcon &tray = app.createSystemTrayIcon();
    QSystemTrayIcon *nativeTray = tray.findChild<QSystemTrayIcon *>();
    CHECK(nativeTray && !nativeTray->icon().isNull(),
          "App-created tray inherits the application icon");
}

static void testWindowRestoresLazyLoading(prism::App &app) {
    prism::ConfigManager *config = prism::ConfigManager::instance();
    config->setLazyLoading(false);
    CHECK(config->waitForPersistence(), "关闭懒加载配置持久化完成");
    prism::Window &eagerWindow = app.createWindow();
    eagerWindow.show();
    CHECK(eagerWindow.rootObject() &&
              !eagerWindow.rootObject()->property("lazyLoading").toBool(),
          "C++ Window 消费已提交的关闭懒加载配置");

    config->setLazyLoading(true);
    CHECK(config->waitForPersistence(), "开启懒加载配置持久化完成");
    prism::Window &lazyWindow = app.createWindow();
    lazyWindow.show();
    CHECK(lazyWindow.rootObject() &&
              lazyWindow.rootObject()->property("lazyLoading").toBool(),
          "C++ Window 消费已提交的开启懒加载配置");
}

static void testAvailableScreenGeometry() {
    QScreen *screen = QGuiApplication::primaryScreen();
    CHECK(screen, "WindowHelper geometry has a primary screen");
    if (!screen)
        return;

    const QRect expected = screen->availableGeometry();
    const QPoint center = screen->geometry().center();
    const QVariantMap actual = prism::WindowHelper::instance()
                                   ->availableScreenGeometryAt(center.x(), center.y());
    CHECK(actual.value(QStringLiteral("x")).toInt() == expected.x()
              && actual.value(QStringLiteral("y")).toInt() == expected.y()
              && actual.value(QStringLiteral("width")).toInt() == expected.width()
              && actual.value(QStringLiteral("height")).toInt() == expected.height(),
          "WindowHelper returns QScreen availableGeometry");

    const QRect expectedFull = screen->geometry();
    const QVariantMap actualFull = prism::WindowHelper::instance()
                                       ->screenGeometryAt(center.x(), center.y());
    CHECK(actualFull.value(QStringLiteral("x")).toInt() == expectedFull.x()
              && actualFull.value(QStringLiteral("y")).toInt() == expectedFull.y()
              && actualFull.value(QStringLiteral("width")).toInt() == expectedFull.width()
              && actualFull.value(QStringLiteral("height")).toInt() == expectedFull.height(),
          "WindowHelper returns full QScreen geometry");
}

static void testDroppedFolderPathValidation() {
    QTemporaryDir directory(
        QDir::tempPath() + QStringLiteral("/prismqml-folder-drop-XXXXXX"));
    const QString folderPath = directory.filePath(QStringLiteral("拖 放#百分%"));
    const QString filePath = directory.filePath(QStringLiteral("not-a-folder.txt"));
    CHECK(directory.isValid() && QDir().mkpath(folderPath),
          "real dropped folder fixture created");
    QFile file(filePath);
    CHECK(file.open(QIODevice::WriteOnly), "real dropped file fixture created");
    file.close();

    prism::WindowHelper *helper = prism::WindowHelper::instance();
    CHECK(helper->resolveDroppedFolderPath(QUrl::fromLocalFile(folderPath))
              == QDir::cleanPath(QFileInfo(folderPath).absoluteFilePath()),
          "WindowHelper accepts one real local folder URL");
    QUrl queryUrl = QUrl::fromLocalFile(folderPath);
    queryUrl.setQuery(QStringLiteral("source=drop"));
    QUrl fragmentUrl = QUrl::fromLocalFile(folderPath);
    fragmentUrl.setFragment(QStringLiteral("section"));
    CHECK(helper->resolveDroppedFolderPath(queryUrl).isEmpty()
              && helper->resolveDroppedFolderPath(fragmentUrl).isEmpty(),
          "WindowHelper rejects ambiguous local folder URLs");
    CHECK(helper->resolveDroppedFolderPath(QUrl::fromLocalFile(filePath)).isEmpty(),
          "WindowHelper rejects a regular file URL");
    CHECK(helper->resolveDroppedFolderPath(
              QUrl::fromLocalFile(directory.filePath(QStringLiteral("missing"))))
              .isEmpty(),
          "WindowHelper rejects a missing folder URL");
    CHECK(helper->resolveDroppedFolderPath(
              QUrl(QStringLiteral("https://example.com/folder"))).isEmpty(),
          "WindowHelper rejects a remote URL");
    CHECK(helper->resolveDroppedFolderPath(
              QUrl(QStringLiteral("file://server/share"))).isEmpty(),
          "WindowHelper rejects a network file URL before lookup");
    CHECK(helper->resolveDroppedFolderPath(
              QUrl(QStringLiteral("file:////?/C:/Windows"))).isEmpty(),
          "WindowHelper rejects a device-style file URL before lookup");
}

static void testWindowFollowerGeometry() {
    using namespace prism::detail;
    const WindowFollowerRect host{100, 120, 700, 520};
    const WindowFollowerRect left = followerRect(host, 180, 120, WindowFollowerLeft);
    const WindowFollowerRect right = followerRect(host, 180, 120, WindowFollowerRight);
    const WindowFollowerRect top = followerRect(host, 180, 120, WindowFollowerTop);
    const WindowFollowerRect bottom = followerRect(host, 180, 120, WindowFollowerBottom);
    CHECK(left.left == -80 && left.top == 120 && left.right == 100 && left.bottom == 520,
          "WindowHelper 左侧跟随使用候选原生 RECT");
    CHECK(right.left == 700 && right.top == 120 && right.right == 880 && right.bottom == 520,
          "WindowHelper 右侧跟随使用候选原生 RECT");
    CHECK(top.left == 100 && top.top == 0 && top.right == 700 && top.bottom == 120,
          "WindowHelper 顶部跟随使用候选原生 RECT");
    CHECK(bottom.left == 100 && bottom.top == 520 && bottom.right == 700 && bottom.bottom == 640,
          "WindowHelper 底部跟随使用候选原生 RECT");

    const WindowFollowerRect extentLeft = followerRectForExtent(
        host, 60, WindowFollowerLeft);
    const WindowFollowerRect extentRight = followerRectForExtent(
        host, 60, WindowFollowerRight);
    const WindowFollowerRect extentTop = followerRectForExtent(
        host, 60, WindowFollowerTop);
    const WindowFollowerRect extentBottom = followerRectForExtent(
        host, 60, WindowFollowerBottom);
    CHECK(extentLeft.left == 40 && extentLeft.top == 120
              && extentLeft.right == 100 && extentLeft.bottom == 520,
          "WindowHelper 左侧动画帧原子更新完整 RECT");
    CHECK(extentRight.left == 700 && extentRight.top == 120
              && extentRight.right == 760 && extentRight.bottom == 520,
          "WindowHelper 右侧动画帧原子更新完整 RECT");
    CHECK(extentTop.left == 100 && extentTop.top == 60
              && extentTop.right == 700 && extentTop.bottom == 120,
          "WindowHelper 顶部动画帧原子更新完整 RECT");
    CHECK(extentBottom.left == 100 && extentBottom.top == 520
              && extentBottom.right == 700 && extentBottom.bottom == 580,
          "WindowHelper 底部动画帧原子更新完整 RECT");

    QList<QPair<qulonglong, qulonglong>> promotions;
    const QList<qulonglong> followers{21, 22};
    const WindowFollowerPromotionResult promotion = promoteWindowFollowerGroup(
        qulonglong{11}, followers,
        [&promotions](qulonglong window, qulonglong insertAfter) {
            promotions.append({window, insertAfter});
            return true;
        });
    const QList<QPair<qulonglong, qulonglong>> expectedPromotions{
        {11, 0}, {21, 11}, {22, 21}};
    CHECK(promotion.hostPromoted && promotion.followersPlaced
              && promotions == expectedPromotions,
          "WindowHelper 鼠标激活先提升宿主再连续排列全部附属窗口");

    QList<qulonglong> activations;
    promotions.clear();
    const WindowFollowerActivationResult activation = activateWindowFollowerGroup(
        qulonglong{11}, followers,
        [&activations](qulonglong window) {
            activations.append(window);
            return true;
        },
        [&promotions](qulonglong window, qulonglong insertAfter) {
            promotions.append({window, insertAfter});
            return true;
        });
    CHECK(activation.hostActivated && activation.hostPromoted
              && activation.followersPlaced && activations == QList<qulonglong>{11}
              && promotions == expectedPromotions,
          "WindowHelper 点击窗口组时由宿主接管激活并立即排列全部附属窗口");

    activations.clear();
    promotions.clear();
    const WindowFollowerActivationResult activationFailure =
        activateWindowFollowerGroup(
            qulonglong{11}, followers,
            [&activations](qulonglong window) {
                activations.append(window);
                return false;
            },
            [&promotions](qulonglong window, qulonglong insertAfter) {
                promotions.append({window, insertAfter});
                return true;
            });
    CHECK(!activationFailure.hostActivated && !activationFailure.hostPromoted
              && !activationFailure.followersPlaced
              && activations == QList<qulonglong>{11} && promotions.isEmpty(),
          "WindowHelper 宿主激活失败时保留系统默认路径");
}

static void testTrayCheckableActionContract() {
    using prism::SystemTrayIcon;
    using prism::TrayActionOptions;

    SystemTrayIcon tray;
    bool triggered = false;
    TrayActionOptions options;
    options.actionId = QStringLiteral("desktop_lyrics");
    options.checkable = true;
    options.checked = true;
    options.toolTip = QStringLiteral("显示或隐藏桌面歌词");
    tray.addAction(QStringLiteral("显示桌面歌词"),
                   [&triggered]() { triggered = true; }, options);

    QSystemTrayIcon *nativeTray = tray.findChild<QSystemTrayIcon *>();
    QMenu *menu = nativeTray ? nativeTray->contextMenu() : nullptr;
    QAction *action = menu && menu->actions().size() == 1 ? menu->actions().constFirst()
                                                          : nullptr;
    CHECK(action && action->objectName() == QStringLiteral("desktop_lyrics"),
          "SystemTray actionId reaches native QAction");
    CHECK(action && action->isCheckable() && action->isChecked(),
          "SystemTray checkable/checked initial state reaches native QAction");
    CHECK(action && action->toolTip() == QStringLiteral("显示或隐藏桌面歌词"),
          "SystemTray tooltip reaches native QAction");
    CHECK(tray.setActionChecked(QStringLiteral("desktop_lyrics"), false)
              && action && !action->isChecked(),
          "SystemTray setActionChecked synchronizes existing action");
    CHECK(!tray.setActionChecked(QStringLiteral("missing"), true),
          "SystemTray setActionChecked reports unknown actionId");
    if (action)
        action->trigger();
    CHECK(triggered, "SystemTray checkable action keeps callback contract");
}

static QObject *findTrayAction(QObject *menu, const QString &actionId) {
    if (!menu)
        return nullptr;
    const QList<QObject *> children = menu->findChildren<QObject *>();
    for (QObject *child : children) {
        if (child->property("actionId").toString() == actionId)
            return child;
    }
    return nullptr;
}

static void testPrismTrayMenuContract(prism::App &app) {
    using prism::SystemTrayIcon;
    using prism::TrayActionOptions;

    SystemTrayIcon &tray = app.createSystemTrayIcon(
        QString(), QStringLiteral("Prism tray test"), false);
    CHECK(tray.usesPrismMenu(),
          "App-owned SystemTrayIcon uses PrismQML SystemTrayMenu");

    bool triggered = false;
    TrayActionOptions options;
    options.actionId = QStringLiteral("styled_action");
    options.icon = QStringLiteral("MusicNote2");
    options.shortcut = QStringLiteral("Ctrl+M");
    options.checkable = true;
    options.checked = true;
    options.toolTip = QStringLiteral("PrismQML styled action");
    tray.addAction(QStringLiteral("Styled action"),
                   [&triggered]() { triggered = true; }, options);

    QObject *menu = tray.findChild<QObject *>(QStringLiteral("prismSystemTrayMenu"));
    QObject *action = findTrayAction(menu, options.actionId);
    QSystemTrayIcon *nativeTray = tray.findChild<QSystemTrayIcon *>();
    CHECK(menu && action, "PrismQML tray menu creates the configured action");
    CHECK(nativeTray && nativeTray->contextMenu() == nullptr,
          "PrismQML tray menu replaces the native QMenu surface");
    CHECK(action && action->property("checked").toBool(),
          "PrismQML tray action receives initial checked state");
    CHECK(tray.setActionChecked(options.actionId, false)
              && action && !action->property("checked").toBool(),
          "setActionChecked synchronizes the PrismQML action");
    CHECK(tray.setActionEnabled(options.actionId, false)
              && action && !action->property("enabled").toBool(),
          "setActionEnabled synchronizes the PrismQML action");
    CHECK(QMetaObject::invokeMethod(
              menu, "actionTriggered", Qt::DirectConnection,
              Q_ARG(QString, options.actionId)) && triggered,
          "PrismQML action signal routes to the C++ callback");
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    prism::App app(argc, argv);
    using namespace prism;

    qInfo() << "=== Icon path URL contract ===";
    testIconPathUrlMatrix();
    testRealEncodedIcon();
    testApplicationIconFacade(app);
    testWindowRestoresLazyLoading(app);
    testAvailableScreenGeometry();
    testDroppedFolderPathValidation();
    testWindowFollowerGeometry();
    testTrayCheckableActionContract();
    testPrismTrayMenuContract(app);

    qInfo() << "=== SystemTray 烟测 ===";
    // 构造 + addAction + addSeparator 不崩 (QApplication 下 QMenu 正常)
    {
        SystemTrayIcon tray(QString(), QStringLiteral("测试托盘"));
        bool clicked = false;
        tray.addAction(QStringLiteral("打开"), [&clicked]() { clicked = true; });
        tray.addSeparator();
        tray.addAction(QStringLiteral("退出"), nullptr);
        CHECK(true, "SystemTrayIcon 构造+addAction+addSeparator 无崩溃");
        CHECK(true, QStringLiteral("isAvailable=%1(环境相关)")
                        .arg(SystemTrayIcon::isAvailable()).toUtf8().constData());
    }

    qInfo() << "=== SingleInstance 烟测 ===";
    {
        // 首个实例: 不应判定为 running
        SingleInstance si(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(!si.isRunning(), "首个实例 isRunning=false");

        // 第二个同 id 实例: 应判定为 running
        SingleInstance si2(QStringLiteral("prism_test_singleton_xyz"));
        CHECK(si2.isRunning(), "第二实例 isRunning=true");
    }

    qInfo() << "";
    if (g_failed == 0)
        qInfo() << "ALL_TESTS_PASSED";
    else
        qCritical() << "TESTS_FAILED:" << g_failed;

    // 不进事件循环, 直接返回 (烟测不需要)
    return g_failed == 0 ? 0 : 1;
}
