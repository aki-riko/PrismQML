// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Shared configuration contracts for startup, QML setters, and persistence.
#pragma once

#include <array>

#include <QString>
#include <QVariant>
#include <QVariantList>

namespace prism {

inline constexpr char kConfigFilePathEnvironment[] = "PRISMQML_CONFIG_FILE";
inline constexpr char kQtAutoScreenScaleFactorEnvironment[] =
    "QT_AUTO_SCREEN_SCALE_FACTOR";
inline constexpr char kQtScreenScaleFactorsEnvironment[] =
    "QT_SCREEN_SCALE_FACTORS";
inline constexpr char kQtEnableHighDpiScalingEnvironment[] =
    "QT_ENABLE_HIGHDPI_SCALING";
inline constexpr char kQtScaleFactorEnvironment[] = "QT_SCALE_FACTOR";
inline constexpr std::array<int, 6> kValidDpiScales = {
    0, 100, 125, 150, 175, 200,
};
inline constexpr std::array<int, 3> kValidWindowTypes = {0, 1, 2};

QString resolveConfigFilePath(const QString &configured = QString());
bool isValidDpiScale(int value);
bool isValidWindowType(int value);
bool strictIntegerVariant(const QVariant &value, int &result);
QVariantList dpiScaleOptions();
QVariantList windowTypeOptions();

// Apply validated startup DPI environment before QApplication construction.
// 在 QApplication 构造前应用经过整份配置校验的 DPI 环境。
int applyDpiScaleBeforeApplication(const QString &configured = QString());

}  // namespace prism
