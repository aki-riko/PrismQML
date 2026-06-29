// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - PlatformInfo (移动端触摸适配地基, 注入 QML 供响应式布局)
// QML 防御式可选读取: typeof PlatformInfo !== "undefined" && PlatformInfo.isMobile
#pragma once

#include <QObject>
#include <QString>

namespace prism {

class PlatformInfo : public QObject {
    Q_OBJECT
    // 是否移动平台 (Android/iOS) — 控件据此切换触摸态/尺寸
    Q_PROPERTY(bool isMobile READ isMobile CONSTANT)
    // 是否触摸优先 (移动端 true; 桌面可被环境变量 PRISM_FORCE_TOUCH 覆盖用于测试)
    Q_PROPERTY(bool isTouch READ isTouch CONSTANT)
    // 平台名 "windows"/"macos"/"linux"/"android"/"ios"/"wasm"
    Q_PROPERTY(QString platformName READ platformName CONSTANT)
    // 推荐最小触摸目标尺寸(px): 移动端 44(iOS HIG)/48(Material), 桌面 32
    Q_PROPERTY(int touchTargetSize READ touchTargetSize CONSTANT)
    // 主屏逻辑宽度(px) — 响应式断点用; 随旋转/屏幕变化更新
    Q_PROPERTY(int screenWidth READ screenWidth NOTIFY screenChanged)
    // 是否窄屏(<600px, 导航应改底部Tab/抽屉); 随旋转更新
    Q_PROPERTY(bool isCompact READ isCompact NOTIFY screenChanged)
    // 安全区 insets(px): 移动端状态栏/刘海/导航条避让, 桌面为 0。随旋转更新。
    Q_PROPERTY(int safeAreaTop READ safeAreaTop NOTIFY screenChanged)
    Q_PROPERTY(int safeAreaBottom READ safeAreaBottom NOTIFY screenChanged)
    // 软键盘高度(px): 键盘弹出时>0, 输入框据此上移避让, 收起为0
    Q_PROPERTY(int keyboardHeight READ keyboardHeight NOTIFY keyboardChanged)
    // 软键盘是否可见
    Q_PROPERTY(bool keyboardVisible READ keyboardVisible NOTIFY keyboardChanged)

signals:
    // 屏幕几何变化(旋转/分辨率): screenWidth/isCompact/safeArea 据此重算
    void screenChanged();
    // 软键盘弹出/收起: keyboardHeight/keyboardVisible 据此更新
    void keyboardChanged();

public:
    static PlatformInfo *instance();

    bool isMobile() const;
    bool isTouch() const;
    QString platformName() const;
    int touchTargetSize() const;
    int screenWidth() const;
    bool isCompact() const;
    int safeAreaTop() const;
    int safeAreaBottom() const;
    int keyboardHeight() const;
    bool keyboardVisible() const;

private:
    explicit PlatformInfo(QObject *parent = nullptr);
};

}  // namespace prism
