// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 工具类实现: Clipboard / WindowHelper / Acrylic
// 镜像 Python providers/clipboard.py + core/window_helper.py + mica_window.py(Acrylic)
#include "prism/ClipboardHelper.h"
#include "prism/WindowHelper.h"
#include "prism/AcrylicHelper.h"
#include "IconPath_p.h"
#include "WindowFollower_p.h"

#include <QCoreApplication>
#include <QGuiApplication>
#include <QClipboard>
#include <QDir>
#include <QIcon>
#include <QImage>
#include <QMutexLocker>
#include <QPixmap>
#include <QPainter>
#include <QPoint>
#include <QSvgRenderer>
#include <QScreen>
#include <QUrl>
#include <QWindow>
#include <QFileInfo>
#include <QDebug>
#include <utility>

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

namespace prism {

// ==================== ClipboardHelper (镜像 clipboard.py) ====================
ClipboardHelper *ClipboardHelper::instance() {
    static ClipboardHelper *s = new ClipboardHelper();
    return s;
}
void ClipboardHelper::copy(const QString &text) {
    if (QClipboard *cb = QGuiApplication::clipboard())
        cb->setText(text);
}
QString ClipboardHelper::paste() {
    if (QClipboard *cb = QGuiApplication::clipboard())
        return cb->text();
    return QString();
}

// ==================== WindowHelper (镜像 window_helper.py) ====================
WindowHelper *WindowHelper::instance() {
    static WindowHelper *s = new WindowHelper();
    return s;
}

// 解析路径为本地文件路径 (镜像 _resolveIconPath)
QString WindowHelper::resolveIconPath(const QString &icon) {
    return detail::resolveIconPath(icon);
}

QString WindowHelper::resolveDroppedFolderPath(const QUrl &folderUrl) const {
    if (!folderUrl.isValid() || !folderUrl.isLocalFile()
        || !folderUrl.host().isEmpty()) {
        return {};
    }
    const QString localPath = folderUrl.toLocalFile();
    const QString normalizedPath = QDir::fromNativeSeparators(localPath);
    if (localPath.isEmpty() || localPath.contains(QChar::Null)
        || normalizedPath.startsWith(QLatin1String("//"))) {
        return {};
    }
    const QFileInfo fileInfo(localPath);
    if (!fileInfo.isAbsolute() || !fileInfo.exists() || !fileInfo.isDir())
        return {};
    return QDir::cleanPath(fileInfo.absoluteFilePath());
}

void WindowHelper::setAppIcon(const QString &icon) {
    if (icon.isEmpty())
        return;
    const QString path = resolveIconPath(icon);
    if (path.isEmpty()) {
        qWarning() << "prism::WindowHelper 无法解析图标路径:" << icon;
        return;
    }
    // SVG 渲染成多尺寸位图 (镜像 _renderSvgIcon)
    if (path.toLower().endsWith(QLatin1String(".svg"))) {
        QSvgRenderer renderer(path);
        if (renderer.isValid()) {
            QIcon qicon;
            for (int sz : {16, 24, 32, 48, 64, 128, 256}) {
                QImage img(sz, sz, QImage::Format_ARGB32_Premultiplied);
                img.fill(Qt::transparent);
                QPainter p(&img);
                p.setRenderHint(QPainter::Antialiasing);
                renderer.render(&p);
                p.end();
                qicon.addPixmap(QPixmap::fromImage(img));
            }
            if (!qicon.isNull()) {
                QGuiApplication::setWindowIcon(qicon);
                return;
            }
        }
    }
    QIcon qicon(path);
    if (!qicon.isNull())
        QGuiApplication::setWindowIcon(qicon);
    else
        qWarning() << "prism::WindowHelper 图标加载失败:" << path;
}

QVariantMap WindowHelper::availableScreenGeometryAt(int x, int y) const {
    QScreen *screen = QGuiApplication::screenAt(QPoint(x, y));
    if (!screen)
        screen = QGuiApplication::primaryScreen();
    if (!screen)
        return {};

    const QRect geometry = screen->availableGeometry();
    return {
        {QStringLiteral("x"), geometry.x()},
        {QStringLiteral("y"), geometry.y()},
        {QStringLiteral("width"), geometry.width()},
        {QStringLiteral("height"), geometry.height()},
    };
}

qulonglong WindowHelper::winIdFromVariant(const QVariant &window) {
    QObject *object = qvariant_cast<QObject *>(window);
    if (!object)
        return 0;
    if (auto *nativeWindow = qobject_cast<QWindow *>(object))
        return static_cast<qulonglong>(nativeWindow->winId());
    const QVariant winId = object->property("winId");
    return winId.isValid() ? winId.toULongLong() : 0;
}

bool WindowHelper::ensureFollowerFilterInstalled() {
#ifdef Q_OS_WIN
    if (m_followerFilterInstalled)
        return true;
    QCoreApplication *app = QCoreApplication::instance();
    if (!app) {
        qWarning() << "prism::WindowHelper: QCoreApplication 未创建, 无法注册窗口跟随";
        return false;
    }
    app->installNativeEventFilter(this);
    m_followerFilterInstalled = true;
    return true;
#else
    return false;
#endif
}

bool WindowHelper::registerWindowFollower(
    const QVariant &hostWindow, const QVariant &followerWindow,
    int edge, qreal logicalExtent) {
#ifdef Q_OS_WIN
    QObject *hostObject = qvariant_cast<QObject *>(hostWindow);
    QObject *followerObject = qvariant_cast<QObject *>(followerWindow);
    auto *nativeHostWindow = qobject_cast<QWindow *>(hostObject);
    auto *nativeFollowerWindow = qobject_cast<QWindow *>(followerObject);
    if (!nativeHostWindow || !nativeFollowerWindow
        || !detail::isWindowFollowerEdge(edge)
        || logicalExtent <= 0
        || !ensureFollowerFilterInstalled())
        return false;

    const qulonglong hostHwnd = static_cast<qulonglong>(nativeHostWindow->winId());
    const qulonglong followerHwnd = static_cast<qulonglong>(nativeFollowerWindow->winId());
    if (!hostHwnd || !followerHwnd
        || GetWindow(reinterpret_cast<HWND>(followerHwnd), GW_OWNER) != nullptr)
        return false;

    RECT hostNativeRect{};
    if (!GetWindowRect(reinterpret_cast<HWND>(hostHwnd), &hostNativeRect))
        return false;
    const qreal scale = nativeHostWindow->devicePixelRatio();
    const int physicalExtent = qMax(1, qRound(logicalExtent * scale));
    const detail::WindowFollowerRect hostRect{
        hostNativeRect.left, hostNativeRect.top,
        hostNativeRect.right, hostNativeRect.bottom};
    const detail::WindowFollowerRect followerRect =
        detail::followerRectForExtent(hostRect, physicalExtent, edge);
    if (!SetWindowPos(
            reinterpret_cast<HWND>(followerHwnd), reinterpret_cast<HWND>(hostHwnd),
            followerRect.left, followerRect.top,
            followerRect.right - followerRect.left,
            followerRect.bottom - followerRect.top,
            SWP_NOACTIVATE | SWP_NOOWNERZORDER))
        return false;
    m_followers.insert(
        followerHwnd,
        {hostHwnd, followerHwnd, edge, physicalExtent});
    return true;
#else
    Q_UNUSED(hostWindow); Q_UNUSED(followerWindow); Q_UNUSED(edge);
    Q_UNUSED(logicalExtent);
    return false;
#endif
}

bool WindowHelper::updateWindowFollowerGeometry(
    const QVariant &hostWindow, const QVariant &followerWindow,
    int edge, qreal logicalExtent) {
    if (!detail::isWindowFollowerEdge(edge) || logicalExtent <= 0)
        return false;
    QObject *hostObject = qvariant_cast<QObject *>(hostWindow);
    QObject *followerObject = qvariant_cast<QObject *>(followerWindow);
    auto *nativeHostWindow = qobject_cast<QWindow *>(hostObject);
    auto *nativeFollowerWindow = qobject_cast<QWindow *>(followerObject);
    if (!nativeHostWindow || !nativeFollowerWindow)
        return false;

#ifdef Q_OS_WIN
    const qulonglong hostHwnd = static_cast<qulonglong>(nativeHostWindow->winId());
    const qulonglong followerHwnd = static_cast<qulonglong>(nativeFollowerWindow->winId());
    RECT hostNativeRect{};
    if (hostHwnd && followerHwnd
        && GetWindow(reinterpret_cast<HWND>(followerHwnd), GW_OWNER) == nullptr
        && GetWindowRect(reinterpret_cast<HWND>(hostHwnd), &hostNativeRect)) {
        const qreal scale = nativeHostWindow->devicePixelRatio();
        const int physicalExtent = qMax(1, qRound(logicalExtent * scale));
        const detail::WindowFollowerRect hostRect{
            hostNativeRect.left, hostNativeRect.top,
            hostNativeRect.right, hostNativeRect.bottom};
        const detail::WindowFollowerRect followerRect =
            detail::followerRectForExtent(hostRect, physicalExtent, edge);
        if (SetWindowPos(
                reinterpret_cast<HWND>(followerHwnd), reinterpret_cast<HWND>(hostHwnd),
                followerRect.left, followerRect.top,
                followerRect.right - followerRect.left,
                followerRect.bottom - followerRect.top,
                SWP_NOACTIVATE | SWP_NOOWNERZORDER))
            return true;
    }
#endif

    const QRect hostGeometry = nativeHostWindow->frameGeometry();
    const detail::WindowFollowerRect hostRect{
        hostGeometry.left(), hostGeometry.top(),
        hostGeometry.right() + 1, hostGeometry.bottom() + 1};
    const detail::WindowFollowerRect followerRect =
        detail::followerRectForExtent(
            hostRect, qMax(1, qRound(logicalExtent)), edge);
    nativeFollowerWindow->setGeometry(QRect(
        followerRect.left, followerRect.top,
        followerRect.right - followerRect.left,
        followerRect.bottom - followerRect.top));
    return true;
}

bool WindowHelper::unregisterWindowFollower(const QVariant &followerWindow) {
#ifdef Q_OS_WIN
    const qulonglong followerHwnd = winIdFromVariant(followerWindow);
    if (!followerHwnd)
        return false;
    return m_followers.remove(followerHwnd);
#else
    Q_UNUSED(followerWindow);
    return false;
#endif
}

bool WindowHelper::nativeEventFilter(
    const QByteArray &eventType, void *message, qintptr *result) {
    Q_UNUSED(result);
#ifdef Q_OS_WIN
    if (eventType != "windows_generic_MSG" || !message)
        return false;
    MSG *msg = static_cast<MSG *>(message);
    if (msg->message == WM_WINDOWPOSCHANGING && msg->lParam) {
        const qulonglong followerHwnd = reinterpret_cast<qulonglong>(msg->hwnd);
        const auto follower = m_followers.constFind(followerHwnd);
        if (follower != m_followers.cend()) {
            WINDOWPOS *windowPos = reinterpret_cast<WINDOWPOS *>(msg->lParam);
            const HWND hostHwnd = reinterpret_cast<HWND>(follower->hostHwnd);
            // Mirror external follower Z-order requests without activating the host.
            // 同步外部附属窗口的 Z 序请求,但不激活宿主窗口。
            if (!(windowPos->flags & SWP_NOZORDER)
                && windowPos->hwndInsertAfter != hostHwnd
                && !SetWindowPos(
                    hostHwnd, windowPos->hwndInsertAfter,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER)) {
                qWarning() << "prism::WindowHelper: 宿主窗口原生抬升失败";
            }
            windowPos->hwndInsertAfter = hostHwnd;
            windowPos->flags &= ~SWP_NOZORDER;
            windowPos->flags |= SWP_NOOWNERZORDER;
        }
        return false;
    }
    if ((msg->message != WM_MOVING && msg->message != WM_SIZING) || !msg->lParam)
        return false;

    RECT *rect = reinterpret_cast<RECT *>(msg->lParam);
    const detail::WindowFollowerRect hostRect{
        rect->left, rect->top, rect->right, rect->bottom};
    for (auto it = m_followers.cbegin(); it != m_followers.cend(); ++it) {
        const WindowFollowerBinding &binding = it.value();
        if (binding.hostHwnd != reinterpret_cast<qulonglong>(msg->hwnd))
            continue;
        const detail::WindowFollowerRect follower =
            detail::followerRectForExtent(
                hostRect, binding.outwardExtent, binding.edge);
        SetWindowPos(
            reinterpret_cast<HWND>(binding.followerHwnd),
            reinterpret_cast<HWND>(binding.hostHwnd),
            follower.left, follower.top,
            follower.right - follower.left, follower.bottom - follower.top,
            SWP_NOACTIVATE | SWP_NOOWNERZORDER);
    }
#else
    Q_UNUSED(eventType); Q_UNUSED(message);
#endif
    return false;
}

// ==================== AcrylicImageProvider + AcrylicHelper ====================
QImage AcrylicImageState::image() const {
    QMutexLocker locker(&m_mutex);
    return m_image;
}

void AcrylicImageState::setImage(const QImage &image) {
    QMutexLocker locker(&m_mutex);
    m_image = image;
    ++m_imageId;
}

int AcrylicImageState::imageId() const {
    QMutexLocker locker(&m_mutex);
    return m_imageId;
}

AcrylicImageProvider::AcrylicImageProvider()
    : AcrylicImageProvider(std::make_shared<AcrylicImageState>()) {}

AcrylicImageProvider::AcrylicImageProvider(std::shared_ptr<AcrylicImageState> state)
    : QQuickImageProvider(QQuickImageProvider::Image), m_state(std::move(state)) {}

QImage AcrylicImageProvider::requestImage(const QString & /*id*/, QSize *size,
                                          const QSize & /*requestedSize*/) {
    const QImage image = m_state->image();
    if (size)
        *size = image.size();
    return image;
}

void AcrylicImageProvider::setImage(const QImage &image) {
    m_state->setImage(image);
}

int AcrylicImageProvider::currentImageId() const {
    return m_state->imageId();
}

AcrylicHelper *AcrylicHelper::instance() {
    static AcrylicHelper *s = new AcrylicHelper();
    return s;
}
AcrylicHelper::AcrylicHelper(QObject *parent)
    : QObject(parent), m_state(std::make_shared<AcrylicImageState>()) {}

AcrylicImageProvider *AcrylicHelper::createImageProvider() const {
    return new AcrylicImageProvider(m_state);
}

void AcrylicHelper::setBlurRadius(int value) {
    m_blurRadius = qMax(1, qMin(100, value));
}

// 简易高斯模糊: 缩小再放大 (镜像 Python 注释 "Qt 内置缩放实现模糊, 无外部依赖")
static QImage scaleBlur(const QImage &src, int radius) {
    if (src.isNull())
        return src;
    const int factor = qMax(2, radius / 4);
    QSize smallSize = src.size() / factor;
    if (smallSize.width() < 1 || smallSize.height() < 1)
        return src;
    QImage down = src.scaled(smallSize, Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
    return down.scaled(src.size(), Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
}

QString AcrylicHelper::grabAndBlur(const QVariant &window, int x, int y, int width, int height) {
    if (width <= 0 || height <= 0)
        return QString();
    QObject *obj = qvariant_cast<QObject *>(window);
    QWindow *w = qobject_cast<QWindow *>(obj);
    QScreen *screen = w ? w->screen() : QGuiApplication::primaryScreen();
    if (!screen)
        return QString();

    const int winX = w ? w->x() : 0;
    const int winY = w ? w->y() : 0;
    const QRect sg = screen->geometry();
    const int grabX = winX + x - sg.x();
    const int grabY = winY + y - sg.y();

    QPixmap pix = screen->grabWindow(0, grabX, grabY, width, height);
    if (pix.isNull())
        return QString();

    QImage blurred = scaleBlur(pix.toImage(), m_blurRadius);
    m_state->setImage(blurred);
    const QString url = QStringLiteral("image://acrylic/%1").arg(m_state->imageId());
    emit imageReady(url);
    return url;
}

QString AcrylicHelper::getImageUrl() const {
    return QStringLiteral("image://acrylic/%1").arg(m_state->imageId());
}

}  // namespace prism
