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

template <std::size_t Size>
bool containsString(const std::array<const char *, Size> &values,
                    const QString &value) {
    return std::any_of(values.begin(), values.end(), [&](const char *candidate) {
        return value == QLatin1String(candidate);
    });
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
            if (key == QStringLiteral("LazyAnimationType") ||
                key == QStringLiteral("DpiScale") ||
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

detail::ConfigLoadStatus parseConfigObjects(
    const QByteArray &data, QJsonObject &window, QJsonObject &appearance,
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
    const QJsonObject root = document.object();
    const QJsonValue windowValue = root.value(QStringLiteral("Window"));
    if (!windowValue.isUndefined() && !windowValue.isObject()) {
        error = QStringLiteral("Window must be an object");
        return detail::ConfigLoadStatus::Invalid;
    }
    const QJsonValue appearanceValue = root.value(QStringLiteral("Appearance"));
    if (!appearanceValue.isUndefined() && !appearanceValue.isObject()) {
        error = QStringLiteral("Appearance must be an object");
        return detail::ConfigLoadStatus::Invalid;
    }
    window = windowValue.toObject();
    appearance = appearanceValue.toObject();
    integerTokens = JsonIntegerFieldScanner(data).scan();
    return detail::ConfigLoadStatus::Valid;
}

bool readOptionalString(const QJsonObject &object, const QString &key,
                        QString &target, QString &invalidField) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined()) return true;
    if (!value.isString()) {
        invalidField = key;
        return false;
    }
    target = value.toString();
    return true;
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
bool isValidLazyAnimationType(int value) {
    return contains(kValidLazyAnimationTypes, value);
}
bool isValidTheme(const QString &value) { return containsString(kValidThemes, value); }
bool isValidSkin(const QString &value) { return containsString(kValidSkins, value); }
bool isValidLanguage(const QString &value) {
    return containsString(kValidLanguages, value);
}
bool isValidAccentColor(const QString &value) {
    const int length = value.length();
    if (!value.startsWith(QLatin1Char('#')) ||
        (length != 4 && length != 7 && length != 9))
        return false;
    for (int index = 1; index < length; ++index) {
        const QChar character = value.at(index);
        if (!character.isDigit() &&
            !(character >= QLatin1Char('a') && character <= QLatin1Char('f')) &&
            !(character >= QLatin1Char('A') && character <= QLatin1Char('F')))
            return false;
    }
    return true;
}

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

QVariantList lazyAnimationTypeOptions() {
    QVariantList result;
    for (int value : kValidLazyAnimationTypes) result.append(value);
    return result;
}

template <std::size_t Size>
QVariantList stringOptions(const std::array<const char *, Size> &values) {
    QVariantList result;
    for (const char *value : values)
        result.append(QString::fromLatin1(value));
    return result;
}

QVariantList themeOptions() { return stringOptions(kValidThemes); }
QVariantList skinOptions() { return stringOptions(kValidSkins); }
QVariantList languageOptions() { return stringOptions(kValidLanguages); }

namespace detail {
ConfigLoadStatus readAppConfigState(const QString &path,
                                    AppConfigState &state,
                                    QString &error,
                                    QString &invalidField) {
    QByteArray data;
    const ConfigLoadStatus readStatus = readConfigBytes(path, data, error);
    if (readStatus != ConfigLoadStatus::Valid) return readStatus;
    QJsonObject window;
    QJsonObject appearance;
    QHash<QString, bool> integerTokens;
    const ConfigLoadStatus parseStatus =
        parseConfigObjects(data, window, appearance, integerTokens, error);
    if (parseStatus != ConfigLoadStatus::Valid) return parseStatus;
    AppConfigState candidate = state;
    const bool windowValid =
        readOptionalBool(window, QStringLiteral("LazyLoading"),
                         candidate.window.lazyLoading, invalidField) &&
        readOptionalInteger(window, QStringLiteral("LazyAnimationType"),
                            candidate.window.lazyAnimationType,
                            kValidLazyAnimationTypes, integerTokens,
                            invalidField) &&
        readOptionalBool(window, QStringLiteral("DwmShadow"),
                         candidate.window.dwmShadow, invalidField) &&
        readOptionalBool(window, QStringLiteral("MicaEnabled"),
                         candidate.window.micaEnabled, invalidField) &&
        readOptionalInteger(window, QStringLiteral("DpiScale"),
                            candidate.window.dpiScale, kValidDpiScales,
                            integerTokens, invalidField) &&
        readOptionalInteger(window, QStringLiteral("WindowType"),
                            candidate.window.windowType, kValidWindowTypes,
                            integerTokens, invalidField);
    const bool appearanceTyped =
        readOptionalString(appearance, QStringLiteral("Theme"),
                           candidate.appearance.theme, invalidField) &&
        readOptionalString(appearance, QStringLiteral("Skin"),
                           candidate.appearance.skin, invalidField) &&
        readOptionalString(appearance, QStringLiteral("Language"),
                           candidate.appearance.language, invalidField) &&
        readOptionalString(appearance, QStringLiteral("AccentColor"),
                           candidate.appearance.accentColor, invalidField);
    const bool appearanceValid = appearanceTyped &&
        isValidTheme(candidate.appearance.theme) &&
        isValidSkin(candidate.appearance.skin) &&
        isValidLanguage(candidate.appearance.language) &&
        isValidAccentColor(candidate.appearance.accentColor);
    if (!windowValid || !appearanceValid) {
        if (invalidField.isEmpty()) invalidField = QStringLiteral("Appearance");
        return ConfigLoadStatus::Invalid;
    }
    state = candidate;
    return ConfigLoadStatus::Valid;
}

ConfigLoadStatus readWindowConfigState(const QString &path,
                                       WindowConfigState &state,
                                       QString &error,
                                       QString &invalidField) {
    AppConfigState appState;
    appState.window = state;
    const ConfigLoadStatus status =
        readAppConfigState(path, appState, error, invalidField);
    if (status == ConfigLoadStatus::Valid) state = appState.window;
    return status;
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
