// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#pragma once

#include <QString>

namespace prism::test {

int runConfigStartupContractTests(const QString &rootPath);
int runConfigParserContractTests(const QString &rootPath);
int runConfigQmlContractTests(const QString &rootPath);

}  // namespace prism::test
