// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 平台检测宏 (统一移动/桌面/WASM 分支判据)
#pragma once

#include <QtGlobal>

// 移动平台 (iOS / Android): 无窗口装饰/托盘/单实例/自更新概念, 全屏单窗口
#if defined(Q_OS_ANDROID) || defined(Q_OS_IOS)
#  define PRISM_MOBILE 1
#else
#  define PRISM_MOBILE 0
#endif

// WebAssembly: 浏览器沙箱, 文件系统/网络受限
#if defined(Q_OS_WASM)
#  define PRISM_WASM 1
#else
#  define PRISM_WASM 0
#endif

// 桌面平台 (Windows / macOS / Linux): 全部能力可用
#if !PRISM_MOBILE && !PRISM_WASM
#  define PRISM_DESKTOP 1
#else
#  define PRISM_DESKTOP 0
#endif

// 窗口装饰(无边框/阴影/云母/托盘)是否可用 — 仅桌面
#define PRISM_HAS_WINDOW_CHROME PRISM_DESKTOP
