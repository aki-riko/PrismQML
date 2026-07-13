// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#include "QRCodeProtocol_p.h"

#include "prism/QRCodeGenerator.h"

#include <QByteArray>
#include <QColor>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonParseError>

#include <cmath>

namespace prism::qrcode_protocol {
namespace {

const QString &protocolPrefix() {
    static const QString prefix = QStringLiteral("v1.");
    return prefix;
}

bool isBase64UrlToken(const QString &token) {
    if (token.isEmpty() || token.size() > kMaxTokenChars) return false;
    for (const QChar character : token) {
        const ushort value = character.unicode();
        const bool alphaNumeric =
            (value >= 'A' && value <= 'Z') || (value >= 'a' && value <= 'z') ||
            (value >= '0' && value <= '9');
        if (!alphaNumeric && value != '-' && value != '_') return false;
    }
    return true;
}

std::optional<QString> validatedContent(const QString &content) {
    if (content.isEmpty() || content.contains(QChar::Null) ||
        !content.isValidUtf16()) {
        return std::nullopt;
    }
    if (content.toUtf8().size() > kMaxContentUtf8Bytes) return std::nullopt;
    return content;
}

std::optional<QString> normalizedColor(const QString &value) {
    const QColor color(value);
    if (!color.isValid() || color.alpha() != 255) return std::nullopt;
    return color.name(QColor::HexRgb).toLower();
}

std::optional<QString> normalizedErrorLevel(const QString &value) {
    const QString normalized = value.toUpper();
    if (normalized == QStringLiteral("L") || normalized == QStringLiteral("M") ||
        normalized == QStringLiteral("Q") || normalized == QStringLiteral("H")) {
        return normalized;
    }
    return std::nullopt;
}

QByteArray canonicalJson(const Request &request) {
    QJsonArray payload;
    payload.append(kProtocolVersion);
    payload.append(request.content);
    payload.append(request.size);
    payload.append(request.foreground);
    payload.append(request.background);
    payload.append(request.errorLevel);
    return QJsonDocument(payload).toJson(QJsonDocument::Compact);
}

std::optional<QByteArray> decodeToken(const QString &token) {
    const auto result = QByteArray::fromBase64Encoding(
        token.toLatin1(),
        QByteArray::Base64UrlEncoding | QByteArray::AbortOnBase64DecodingErrors);
    if (!result || result.decoded.size() > kMaxJsonBytes) return std::nullopt;
    const QString decoded = QString::fromUtf8(result.decoded);
    if (decoded.toUtf8() != result.decoded) return std::nullopt;
    return result.decoded;
}

std::optional<int> jsonInteger(const QJsonValue &value) {
    if (!value.isDouble()) return std::nullopt;
    const double number = value.toDouble();
    if (!std::isfinite(number) || std::floor(number) != number ||
        number < kQrCodeMinimumSize || number > kQrCodeMaximumSize) {
        return std::nullopt;
    }
    return static_cast<int>(number);
}

std::optional<Request> requestFromJson(const QByteArray &raw) {
    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(raw, &error);
    if (error.error != QJsonParseError::NoError || !document.isArray())
        return std::nullopt;
    const QJsonArray payload = document.array();
    if (payload.size() != 6 || !payload.at(0).isDouble() ||
        payload.at(0).toDouble() != kProtocolVersion ||
        !payload.at(1).isString() || !payload.at(3).isString() ||
        !payload.at(4).isString() || !payload.at(5).isString()) {
        return std::nullopt;
    }
    const auto size = jsonInteger(payload.at(2));
    if (!size) return std::nullopt;
    return createRequest(payload.at(1).toString(), *size, payload.at(3).toString(),
                         payload.at(4).toString(), payload.at(5).toString());
}

}  // namespace

std::optional<Request> createRequest(const QString &content, int size,
                                     const QString &foreground,
                                     const QString &background,
                                     const QString &errorLevel) {
    const auto validContent = validatedContent(content);
    const auto validForeground = normalizedColor(foreground);
    const auto validBackground = normalizedColor(background);
    const auto validLevel = normalizedErrorLevel(errorLevel);
    if (!validContent || size < kQrCodeMinimumSize || size > kQrCodeMaximumSize ||
        !validForeground || !validBackground || !validLevel ||
        *validForeground == *validBackground) {
        return std::nullopt;
    }
    return Request{*validContent, size, *validForeground, *validBackground, *validLevel};
}

QString encodeProviderId(const Request &request) {
    const QByteArray json = canonicalJson(request);
    if (json.size() > kMaxJsonBytes) return QString();
    const QByteArray token =
        json.toBase64(QByteArray::Base64UrlEncoding | QByteArray::OmitTrailingEquals);
    if (token.size() > kMaxTokenChars) return QString();
    return protocolPrefix() + QString::fromLatin1(token);
}

QString buildImageSource(const QString &content, int size,
                         const QString &foreground, const QString &background,
                         const QString &errorLevel) {
    const auto request = createRequest(content, size, foreground, background, errorLevel);
    if (!request) return QString();
    const QString providerId = encodeProviderId(*request);
    if (providerId.isEmpty()) return QString();
    return QStringLiteral("image://qrcode/") + providerId;
}

std::optional<Request> decodeProviderId(const QString &providerId) {
    if (providerId.size() > kMaxProviderIdChars ||
        !providerId.startsWith(protocolPrefix())) {
        return std::nullopt;
    }
    const QString token = providerId.mid(protocolPrefix().size());
    if (!isBase64UrlToken(token)) return std::nullopt;
    const auto raw = decodeToken(token);
    if (!raw) return std::nullopt;
    const auto request = requestFromJson(*raw);
    if (!request || encodeProviderId(*request) != providerId) return std::nullopt;
    return request;
}

}  // namespace prism::qrcode_protocol
