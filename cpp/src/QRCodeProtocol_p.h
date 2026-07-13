// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#pragma once

#include <QString>

#include <optional>

namespace prism::qrcode_protocol {

inline constexpr int kProtocolVersion = 1;
inline constexpr int kProtocolPrefixChars = 3;
inline constexpr int kMaxContentUtf8Bytes = 1024;
inline constexpr int kMaxJsonBytes = 6179;
inline constexpr int kMaxTokenChars = 8239;
inline constexpr int kMaxProviderIdChars = kMaxTokenChars + kProtocolPrefixChars;

struct Request {
    QString content;
    int size = 0;
    QString foreground;
    QString background;
    QString errorLevel;
};

std::optional<Request> createRequest(const QString &content, int size,
                                     const QString &foreground,
                                     const QString &background,
                                     const QString &errorLevel);
QString encodeProviderId(const Request &request);
QString buildImageSource(const QString &content, int size,
                         const QString &foreground, const QString &background,
                         const QString &errorLevel);
std::optional<Request> decodeProviderId(const QString &providerId);

}  // namespace prism::qrcode_protocol
