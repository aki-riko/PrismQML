// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ScreenEyedropperManager 实现 (镜像 screen_eyedropper.py)
#include "prism/ScreenEyedropper.h"

#include <QWidget>
#include <QGuiApplication>
#include <QApplication>
#include <QScreen>
#include <QMouseEvent>
#include <QKeyEvent>
#include <QPixmap>
#include <QPainter>
#include <QCursor>

namespace prism {

// 全屏覆盖窗: 抓取整屏作背景, 点击取像素, Esc 取消
class EyedropperOverlay : public QWidget {
public:
    EyedropperOverlay(ScreenEyedropperManager *mgr)
        : QWidget(nullptr, Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint),
          m_mgr(mgr) {
        setCursor(Qt::CrossCursor);
        setMouseTracking(true);
    }

    void beginPick() {
        QScreen *screen = QGuiApplication::primaryScreen();
        if (screen) {
            m_shot = screen->grabWindow(0);  // 抓整屏
            setGeometry(screen->geometry());
        }
        showFullScreen();
        raise();
        activateWindow();
    }

protected:
    void paintEvent(QPaintEvent *) override {
        QPainter p(this);
        if (!m_shot.isNull())
            p.drawPixmap(rect(), m_shot);
    }

    void mousePressEvent(QMouseEvent *e) override {
        if (e->button() == Qt::LeftButton) {
            const QColor c = pickAt(e->globalPosition().toPoint());
            close();
            emit_picked(c);
        }
    }

    void keyPressEvent(QKeyEvent *e) override {
        if (e->key() == Qt::Key_Escape) {
            close();
            emit_cancelled();
        }
    }

private:
    QColor pickAt(const QPoint &globalPos) {
        if (m_shot.isNull())
            return QColor();
        // grabWindow(0) 以主屏左上为原点, globalPos 减屏偏移
        QScreen *screen = QGuiApplication::primaryScreen();
        const QPoint o = screen ? screen->geometry().topLeft() : QPoint();
        const QImage img = m_shot.toImage();
        const QPoint p = globalPos - o;
        if (p.x() >= 0 && p.y() >= 0 && p.x() < img.width() && p.y() < img.height())
            return img.pixelColor(p);
        return QColor();
    }
    void emit_picked(const QColor &c);
    void emit_cancelled();

    ScreenEyedropperManager *m_mgr;
    QPixmap m_shot;
};

// EyedropperOverlay 非 QObject, 用辅助函数发管理器信号
void EyedropperOverlay::emit_picked(const QColor &c) {
    if (m_mgr) {
        emit m_mgr->colorPicked(c);
        emit m_mgr->pickingFinished();
    }
}
void EyedropperOverlay::emit_cancelled() {
    if (m_mgr) {
        emit m_mgr->pickingCancelled();
        emit m_mgr->pickingFinished();
    }
}

// ==================== Manager ====================
ScreenEyedropperManager *ScreenEyedropperManager::instance() {
    static ScreenEyedropperManager *s = new ScreenEyedropperManager();
    return s;
}

ScreenEyedropperManager::ScreenEyedropperManager(QObject *parent) : QObject(parent) {}

void ScreenEyedropperManager::startPicking(bool /*isDark*/) {
    if (!m_overlay)
        m_overlay = new EyedropperOverlay(this);
    m_overlay->beginPick();
    emit pickingStarted();
}

void ScreenEyedropperManager::stopPicking() {
    if (m_overlay)
        m_overlay->close();
    emit pickingFinished();
}

}  // namespace prism
