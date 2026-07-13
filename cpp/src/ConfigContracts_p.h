// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#pragma once

#include <QString>

namespace prism {
namespace detail {

enum class ConfigLoadStatus { Missing, Invalid, Valid };

struct WindowConfigState {
    bool lazyLoading = true;
    bool dwmShadow = true;
    bool micaEnabled = false;
    int dpiScale = 0;
    int windowType = 1;
};

ConfigLoadStatus readWindowConfigState(const QString &path,
                                       WindowConfigState &state,
                                       QString &error,
                                       QString &invalidField);

}  // namespace detail
}  // namespace prism
