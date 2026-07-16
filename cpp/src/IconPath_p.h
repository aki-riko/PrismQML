// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Shared private icon source resolution. 图标来源共享私有解析。
#pragma once

#include <QString>
#include <QUrl>

namespace prism::detail {

inline QString resolveIconPath(const QString &icon) {
    if (icon.isEmpty() || icon.startsWith(QLatin1String(":/")))
        return icon;

    const QUrl url(icon);
    if (url.isLocalFile())
        return url.toLocalFile();
    if (url.scheme().compare(QLatin1String("qrc"), Qt::CaseInsensitive) == 0) {
        QString path = url.path(QUrl::FullyDecoded);
        while (path.startsWith(QLatin1Char('/')))
            path.remove(0, 1);
        return QStringLiteral(":/") + path;
    }
    return icon;
}

}  // namespace prism::detail
