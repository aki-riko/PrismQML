// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - TableListModel 实现 (镜像 Python table_models.py)
#include "prism/DataModels.h"

namespace prism {

void TableListModel::setItems(const QVariantList &items) {
    beginResetModel();
    m_data = items;
    m_roleNames.clear();
    m_keyToRole.clear();
    // 从首行 keys 动态生成 role 名 (镜像 Python)
    if (!items.isEmpty()) {
        const QVariantMap first = items.first().toMap();
        int role = Qt::UserRole + 1;
        for (auto it = first.constBegin(); it != first.constEnd(); ++it) {
            m_roleNames.insert(role, it.key().toUtf8());
            m_keyToRole.insert(it.key(), role);
            ++role;
        }
    }
    endResetModel();
    emit countChanged();
}

QVariantMap TableListModel::getRow(int index) const {
    if (index < 0 || index >= m_data.size())
        return QVariantMap();
    return m_data.at(index).toMap();
}

int TableListModel::rowCount(const QModelIndex &parent) const {
    if (parent.isValid())
        return 0;
    return m_data.size();
}

QVariant TableListModel::data(const QModelIndex &index, int role) const {
    if (!index.isValid() || index.row() < 0 || index.row() >= m_data.size())
        return QVariant();
    const QVariantMap row = m_data.at(index.row()).toMap();
    if (role == Qt::UserRole)  // 整行
        return row;
    const QByteArray col = m_roleNames.value(role);
    if (col.isEmpty())
        return QVariant();
    return row.value(QString::fromUtf8(col));
}

}  // namespace prism
