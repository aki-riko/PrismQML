// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#pragma once

#include <QDebug>
#include <QString>

namespace prism::test {

struct QRChecks {
    int failures = 0;

    void require(bool condition, const QString &message) {
        if (condition) return;
        ++failures;
        qCritical().noquote() << "FAIL:" << message;
    }
};

void runQrProtocolTests(QRChecks &checks);

}  // namespace prism::test
