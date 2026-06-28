// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Store 响应式状态存储 (镜像 Python state/store.py)
#pragma once

#include <QObject>
#include <QString>
#include <QVariant>
#include <QHash>
#include <QList>
#include <functional>

namespace prism {

// StoreSignals - Qt 信号桥接 (镜像 Python StoreSignals), 供 QML 绑定
class StoreSignals : public QObject {
    Q_OBJECT
public:
    using QObject::QObject;
signals:
    void changed(const QString &key, const QVariant &newValue, const QVariant &oldValue);
};

class Store;

// BatchGuard - RAII 批量更新 (镜像 Python BatchContext, 用法: { auto b = store.batch(); ... })
class BatchGuard {
public:
    explicit BatchGuard(Store *store);
    ~BatchGuard();
    BatchGuard(BatchGuard &&other) noexcept;
    BatchGuard(const BatchGuard &) = delete;
    BatchGuard &operator=(const BatchGuard &) = delete;
private:
    Store *m_store;
};

// Store - 响应式状态存储 (镜像 Python Store)
class Store {
public:
    using KeyWatcher = std::function<void(const QVariant &newV, const QVariant &oldV)>;
    using GlobalWatcher = std::function<void(const QString &key, const QVariant &newV, const QVariant &oldV)>;
    using Unwatch = std::function<void()>;

    explicit Store(const QString &name = QString());
    virtual ~Store() = default;

    QString name() const { return m_name; }
    StoreSignals *qtSignals() { return &m_signals; }

    void define(const QString &key, const QVariant &defaultValue = QVariant());
    QVariant get(const QString &key, const QVariant &defaultValue = QVariant()) const;
    void set(const QString &key, const QVariant &value, bool force = false);

    Unwatch watch(const QString &key, KeyWatcher callback);
    Unwatch watchAll(GlobalWatcher callback);

    BatchGuard batch() { return BatchGuard(this); }

    void reset(const QString &key = QString());
    QList<QString> keys() const { return m_state.keys(); }
    QHash<QString, QVariant> values() const { return m_state; }

    QVariant operator[](const QString &key) const { return get(key); }

private:
    friend class BatchGuard;
    void notify(const QString &key, const QVariant &newV, const QVariant &oldV);
    void beginBatch();
    void endBatch();

    QString m_name;
    QHash<QString, QVariant> m_state;
    QHash<QString, QVariant> m_defaults;
    QHash<QString, QList<KeyWatcher>> m_watchers;
    QList<GlobalWatcher> m_globalWatchers;
    bool m_batchMode = false;
    QHash<QString, QPair<QVariant, QVariant>> m_batchChanges;  // key -> (new, old)
    StoreSignals m_signals;
};

}  // namespace prism
