// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 主题/皮肤枚举 + 全局自由函数 (镜像 Python theme.py)
#pragma once

#include <QString>
#include <QColor>

namespace prism {

// Theme - 明暗主题枚举 (镜像 Python Theme(Enum)) 值对齐 light/dark/auto
enum class Theme { Light, Dark, Auto };

// Skin - 皮肤(设计语言)枚举 与 Theme 正交 (镜像 Python Skin(Enum))
enum class Skin { Fluent, Neobrutalism };

// 字符串 <-> 枚举互转 (QML 侧用字符串, 与 Python 的 .value 对齐)
QString themeToString(Theme t);
Theme   themeFromString(const QString &s);
QString skinToString(Skin s);
Skin    skinFromString(const QString &s);

// ==================== 全局自由函数 (镜像 Python __all__ 导出) ====================
void   setTheme(Theme theme);
Theme  getTheme();
void   setSkin(Skin skin);
Skin   getSkin();
bool   isDark();
void   setAccentColor(const QString &color);
QString getAccentColor();
QColor  accentQColor();

}  // namespace prism
