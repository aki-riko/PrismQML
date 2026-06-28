// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Store 实现 (镜像 Python state/store.py)
#include "prism/Store.h"
#include <QDebug>

namespace prism {

// ==================== BatchGuard ====================
BatchGuard::BatchGuard(Store *store) : m_store(store) {
    if (m_store)
        m_store->beginBatch();
}
BatchGuard::~BatchGuard() {
    if (m_store)
        m_store->endBatch();
}
BatchGuard::BatchGuard(BatchGuard &&other) noexcept : m_store(other.m_store) {
    other.m_store = nullptr;
}

// ==================== Store ====================
Store::Store(const QString &name) : m_name(name) {}

void Store::define(const QString &key, const QVariant &defaultValue) {
    m_defaults.insert(key, defaultValue);
    if (!m_state.contains(key))
        m_state.insert(key, defaultValue);
}

QVariant Store::get(const QString &key, const QVariant &defaultValue) const {
    if (m_state.contains(key))
        return m_state.value(key);
    if (m_defaults.contains(key))
        return m_defaults.value(key);
    return defaultValue;
}

void Store::set(const QString &key, const QVariant &value, bool force) {
    const QVariant old = m_state.value(key);
    // 值相同跳过 (镜像 Python: not force and old == value)
    if (!force && old == value)
        return;
    m_state.insert(key, value);

    if (m_batchMode) {
        if (!m_batchChanges.contains(key))
            m_batchChanges.insert(key, qMakePair(value, old));
        else {
            // 保留最早的 old (镜像 Python)
            const QVariant originalOld = m_batchChanges.value(key).second;
            m_batchChanges.insert(key, qMakePair(value, originalOld));
        }
    } else {
        notify(key, value, old);
    }
}

void Store::notify(const QString &key, const QVariant &newV, const QVariant &oldV) {
    // 特定 key 订阅者 (复制防迭代时修改)
    if (m_watchers.contains(key)) {
        const auto callbacks = m_watchers.value(key);
        for (const auto &cb : callbacks) {
            if (cb)
                cb(newV, oldV);
        }
    }
    // 全局订阅者
    const auto globals = m_globalWatchers;
    for (const auto &cb : globals) {
        if (cb)
            cb(key, newV, oldV);
    }
    // Qt 信号
    emit m_signals.changed(key, newV, oldV);
}

Store::Unwatch Store::watch(const QString &key, KeyWatcher callback) {
    m_watchers[key].append(callback);
    const int idx = m_watchers[key].size() - 1;
    // 取消函数: 置空该槽 (避免索引失效, 用标记清除)
    return [this, key, idx]() {
        if (m_watchers.contains(key) && idx < m_watchers[key].size())
            m_watchers[key][idx] = nullptr;
    };
}

Store::Unwatch Store::watchAll(GlobalWatcher callback) {
    m_globalWatchers.append(callback);
    const int idx = m_globalWatchers.size() - 1;
    return [this, idx]() {
        if (idx < m_globalWatchers.size())
            m_globalWatchers[idx] = nullptr;
    };
}

void Store::beginBatch() {
    m_batchMode = true;
    m_batchChanges.clear();
}

void Store::endBatch() {
    m_batchMode = false;
    for (auto it = m_batchChanges.constBegin(); it != m_batchChanges.constEnd(); ++it)
        notify(it.key(), it.value().first, it.value().second);
    m_batchChanges.clear();
}

void Store::reset(const QString &key) {
    if (!key.isEmpty()) {
        if (m_defaults.contains(key))
            set(key, m_defaults.value(key));
    } else {
        for (auto it = m_defaults.constBegin(); it != m_defaults.constEnd(); ++it)
            set(it.key(), it.value());
    }
}

}  // namespace prism
