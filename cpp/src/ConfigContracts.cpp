// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Shared strict config parsing and startup DPI environment implementation.
#include "prism/ConfigContracts.h"
#include "ConfigContracts_p.h"

#include <QByteArray>
#include <QDebug>
#include <QDir>
#include <QFile>
#include <QHash>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QMetaType>
#include <algorithm>
#include <cmath>
#include <limits>

namespace prism {

namespace {
constexpr char kDefaultConfigRelativePath[] = ".prismqml/app.json";
constexpr char kUtf8Bom[] = "\xEF\xBB\xBF";

template <std::size_t Size>
bool contains(const std::array<int, Size> &values, int value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

class JsonIntegerFieldScanner {
public:
    explicit JsonIntegerFieldScanner(const QByteArray &data) : m_data(data) {}

    QHash<QString, bool> scan() {
        QHash<QString, bool> fields;
        skipWhitespace();
        if (peek() == '{') scanRootObject(fields);
        return fields;
    }

private:
    char peek() const {
        return m_position < m_data.size() ? m_data.at(m_position) : '\0';
    }

    void skipWhitespace() {
        while (m_position < m_data.size()) {
            const char value = m_data.at(m_position);
            if (value != ' ' && value != '\t' && value != '\r' && value != '\n')
                break;
            ++m_position;
        }
    }

    bool consume(char expected) {
        skipWhitespace();
        if (peek() != expected) return false;
        ++m_position;
        return true;
    }

    QString readString() {
        skipWhitespace();
        const qsizetype start = m_position;
        if (peek() != '"') return {};
        ++m_position;
        while (m_position < m_data.size()) {
            const char value = m_data.at(m_position++);
            if (value == '"') break;
            if (value != '\\' || m_position >= m_data.size()) continue;
            const char escaped = m_data.at(m_position++);
            if (escaped == 'u') m_position += 4;
        }
        const QByteArray token = m_data.mid(start, m_position - start);
        const QJsonDocument decoded = QJsonDocument::fromJson("[" + token + "]");
        const QJsonArray values = decoded.array();
        return values.isEmpty() ? QString() : values.at(0).toString();
    }

    bool skipNumber() {
        bool integerToken = true;
        while (m_position < m_data.size()) {
            const char value = m_data.at(m_position);
            if (value == ',' || value == ']' || value == '}' || value == ' ' ||
                value == '\t' || value == '\r' || value == '\n')
                break;
            if (value == '.' || value == 'e' || value == 'E') integerToken = false;
            ++m_position;
        }
        return integerToken;
    }

    void skipLiteral() {
        if (m_data.mid(m_position, 4) == "true") m_position += 4;
        else if (m_data.mid(m_position, 5) == "false") m_position += 5;
        else if (m_data.mid(m_position, 4) == "null") m_position += 4;
    }

    void skipArray() {
        consume('[');
        skipWhitespace();
        if (consume(']')) return;
        while (m_position < m_data.size()) {
            skipValue();
            if (consume(']')) return;
            consume(',');
        }
    }

    void skipObject() {
        consume('{');
        skipWhitespace();
        if (consume('}')) return;
        while (m_position < m_data.size()) {
            readString();
            consume(':');
            skipValue();
            if (consume('}')) return;
            consume(',');
        }
    }

    void skipValue() {
        skipWhitespace();
        const char value = peek();
        if (value == '{') skipObject();
        else if (value == '[') skipArray();
        else if (value == '"') readString();
        else if (value == 't' || value == 'f' || value == 'n') skipLiteral();
        else skipNumber();
    }

    void scanWindowObject(QHash<QString, bool> &fields) {
        consume('{');
        skipWhitespace();
        if (consume('}')) return;
        while (m_position < m_data.size()) {
            const QString key = readString();
            consume(':');
            if (key == QStringLiteral("DpiScale") ||
                key == QStringLiteral("WindowType")) {
                skipWhitespace();
                const char value = peek();
                const bool number = value == '-' || (value >= '0' && value <= '9');
                fields.insert(key, number ? skipNumber() : (skipValue(), false));
            } else {
                skipValue();
            }
            if (consume('}')) return;
            consume(',');
        }
    }

    void scanRootObject(QHash<QString, bool> &fields) {
        consume('{');
        skipWhitespace();
        if (consume('}')) return;
        while (m_position < m_data.size()) {
            const QString key = readString();
            consume(':');
            skipWhitespace();
            if (key == QStringLiteral("Window") && peek() == '{') {
                QHash<QString, bool> candidate;
                scanWindowObject(candidate);
                fields = candidate;
            } else {
                skipValue();
                if (key == QStringLiteral("Window")) fields.clear();
            }
            if (consume('}')) return;
            consume(',');
        }
    }

    QByteArray m_data;
    qsizetype m_position = 0;
};

detail::ConfigLoadStatus readConfigBytes(const QString &path, QByteArray &data,
                                         QString &error) {
    if (path.isEmpty()) {
        error = QStringLiteral("empty configuration path");
        return detail::ConfigLoadStatus::Invalid;
    }
    QFile file(path);
    if (!file.exists()) return detail::ConfigLoadStatus::Missing;
    if (!file.open(QIODevice::ReadOnly)) {
        error = file.errorString();
        return detail::ConfigLoadStatus::Invalid;
    }
    data = file.readAll();
    if (file.error() == QFileDevice::NoError) return detail::ConfigLoadStatus::Valid;
    error = file.errorString();
    return detail::ConfigLoadStatus::Invalid;
}

detail::ConfigLoadStatus parseWindowObject(
    const QByteArray &data, QJsonObject &window,
    QHash<QString, bool> &integerTokens, QString &error) {
    if (data.startsWith(kUtf8Bom)) {
        error = QStringLiteral("UTF-8 BOM is not supported");
        return detail::ConfigLoadStatus::Invalid;
    }
    QJsonParseError parseError{};
    const QJsonDocument document = QJsonDocument::fromJson(data, &parseError);
    if (parseError.error != QJsonParseError::NoError) {
        error = parseError.errorString();
        return detail::ConfigLoadStatus::Invalid;
    }
    if (!document.isObject()) {
        error = QStringLiteral("root must be an object");
        return detail::ConfigLoadStatus::Invalid;
    }
    const QJsonValue value = document.object().value(QStringLiteral("Window"));
    if (!value.isUndefined() && !value.isObject()) {
        error = QStringLiteral("Window must be an object");
        return detail::ConfigLoadStatus::Invalid;
    }
    window = value.toObject();
    integerTokens = JsonIntegerFieldScanner(data).scan();
    return detail::ConfigLoadStatus::Valid;
}

bool readOptionalBool(const QJsonObject &object, const QString &key, bool &target,
                      QString &invalidField) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined()) return true;
    if (!value.isBool()) {
        invalidField = key;
        return false;
    }
    target = value.toBool();
    return true;
}

template <std::size_t Size>
bool readOptionalInteger(const QJsonObject &object, const QString &key, int &target,
                         const std::array<int, Size> &validValues,
                         const QHash<QString, bool> &integerTokens,
                         QString &invalidField) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined()) return true;
    const double number = value.toDouble(std::numeric_limits<double>::quiet_NaN());
    if (!integerTokens.value(key, false) || !value.isDouble() ||
        !std::isfinite(number) || std::floor(number) != number ||
        number < std::numeric_limits<int>::min() ||
        number > std::numeric_limits<int>::max()) {
        invalidField = key;
        return false;
    }
    const int integer = static_cast<int>(number);
    if (!contains(validValues, integer)) {
        invalidField = key;
        return false;
    }
    target = integer;
    return true;
}

QByteArray scaleFactorText(int dpiScale) {
    QString factor = QString::number(dpiScale / 100.0, 'f', 2);
    while (factor.endsWith(QLatin1Char('0')) &&
           !factor.endsWith(QStringLiteral(".0")))
        factor.chop(1);
    return factor.toLatin1();
}

void clearDpiEnvironment() {
    qunsetenv(kQtAutoScreenScaleFactorEnvironment);
    qunsetenv(kQtScreenScaleFactorsEnvironment);
}
}  // namespace

QString resolveConfigFilePath(const QString &configured) {
    if (!configured.isEmpty()) return configured;
    const QString environmentPath = qEnvironmentVariable(kConfigFilePathEnvironment);
    if (!environmentPath.isEmpty()) return environmentPath;
    return QDir(QDir::homePath()).filePath(
        QString::fromLatin1(kDefaultConfigRelativePath));
}

bool isValidDpiScale(int value) { return contains(kValidDpiScales, value); }
bool isValidWindowType(int value) { return contains(kValidWindowTypes, value); }

bool strictIntegerVariant(const QVariant &value, int &result) {
    if (value.metaType().id() != QMetaType::Int) return false;
    result = value.toInt();
    return true;
}

QVariantList dpiScaleOptions() {
    QVariantList result;
    for (int value : kValidDpiScales) result.append(value);
    return result;
}

QVariantList windowTypeOptions() {
    QVariantList result;
    for (int value : kValidWindowTypes) result.append(value);
    return result;
}

namespace detail {
ConfigLoadStatus readWindowConfigState(const QString &path,
                                       WindowConfigState &state,
                                       QString &error,
                                       QString &invalidField) {
    QByteArray data;
    const ConfigLoadStatus readStatus = readConfigBytes(path, data, error);
    if (readStatus != ConfigLoadStatus::Valid) return readStatus;
    QJsonObject window;
    QHash<QString, bool> integerTokens;
    const ConfigLoadStatus parseStatus =
        parseWindowObject(data, window, integerTokens, error);
    if (parseStatus != ConfigLoadStatus::Valid) return parseStatus;
    WindowConfigState candidate = state;
    const bool valid =
        readOptionalBool(window, QStringLiteral("LazyLoading"),
                         candidate.lazyLoading, invalidField) &&
        readOptionalBool(window, QStringLiteral("DwmShadow"),
                         candidate.dwmShadow, invalidField) &&
        readOptionalBool(window, QStringLiteral("MicaEnabled"),
                         candidate.micaEnabled, invalidField) &&
        readOptionalInteger(window, QStringLiteral("DpiScale"),
                            candidate.dpiScale, kValidDpiScales,
                            integerTokens, invalidField) &&
        readOptionalInteger(window, QStringLiteral("WindowType"),
                            candidate.windowType, kValidWindowTypes,
                            integerTokens, invalidField);
    if (!valid) return ConfigLoadStatus::Invalid;
    state = candidate;
    return ConfigLoadStatus::Valid;
}
}  // namespace detail

int applyDpiScaleBeforeApplication(const QString &configured) {
    detail::WindowConfigState state;
    QString error;
    QString invalidField;
    const QString path = resolveConfigFilePath(configured);
    const detail::ConfigLoadStatus status =
        detail::readWindowConfigState(path, state, error, invalidField);
    if (status == detail::ConfigLoadStatus::Invalid) {
        qWarning() << "prism::App DPI 配置无效:"
                   << (invalidField.isEmpty() ? error : invalidField);
        state.dpiScale = 0;
    }
    if (state.dpiScale > 0) {
        qputenv(kQtEnableHighDpiScalingEnvironment, "0");
        qputenv(kQtScaleFactorEnvironment, scaleFactorText(state.dpiScale));
        clearDpiEnvironment();
        qInfo() << "prism::App 应用固定 DPI 缩放:" << state.dpiScale << "%";
    } else {
        qputenv(kQtEnableHighDpiScalingEnvironment, "1");
        clearDpiEnvironment();
        qunsetenv(kQtScaleFactorEnvironment);
    }
    return state.dpiScale;
}

}  // namespace prism
