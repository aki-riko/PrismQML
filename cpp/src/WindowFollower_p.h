// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 原生附属窗口几何私有工具
#pragma once

#include <QList>

namespace prism::detail {

enum WindowFollowerEdge {
    WindowFollowerLeft = 0,
    WindowFollowerRight = 1,
    WindowFollowerTop = 2,
    WindowFollowerBottom = 3,
};

struct WindowFollowerRect {
    int left;
    int top;
    int right;
    int bottom;
};

struct WindowFollowerPromotionResult {
    bool hostPromoted;
    bool followersPlaced;
};

struct WindowFollowerActivationResult {
    bool hostActivated;
    bool hostPromoted;
    bool followersPlaced;
};

inline bool isWindowFollowerEdge(int edge) {
    return edge >= WindowFollowerLeft && edge <= WindowFollowerBottom;
}

inline WindowFollowerRect followerRect(
    const WindowFollowerRect &host, int followerWidth, int followerHeight, int edge) {
    switch (edge) {
        case WindowFollowerLeft:
            return {host.left - followerWidth, host.top, host.left, host.bottom};
        case WindowFollowerRight:
            return {host.right, host.top, host.right + followerWidth, host.bottom};
        case WindowFollowerTop:
            return {host.left, host.top - followerHeight, host.right, host.top};
        case WindowFollowerBottom:
            return {host.left, host.bottom, host.right, host.bottom + followerHeight};
        default:
            return host;
    }
}

inline WindowFollowerRect followerRectForExtent(
    const WindowFollowerRect &host, int extent, int edge) {
    const int hostWidth = host.right - host.left;
    const int hostHeight = host.bottom - host.top;
    const int followerWidth = edge == WindowFollowerLeft || edge == WindowFollowerRight
        ? extent : hostWidth;
    const int followerHeight = edge == WindowFollowerTop || edge == WindowFollowerBottom
        ? extent : hostHeight;
    return followerRect(host, followerWidth, followerHeight, edge);
}

inline bool sameWindowFollowerRect(
    const WindowFollowerRect &left, const WindowFollowerRect &right) {
    return left.left == right.left && left.top == right.top
        && left.right == right.right && left.bottom == right.bottom;
}

template <typename Handle>
inline bool isWindowFollowerGroupValid(
    Handle host, const QList<Handle> &followers) {
    if (!host || followers.isEmpty())
        return false;
    for (const Handle follower : followers) {
        if (!follower)
            return false;
    }
    return true;
}

template <typename Handle, typename SetZOrder>
inline WindowFollowerPromotionResult promoteWindowFollowerGroup(
    Handle host, const QList<Handle> &followers, SetZOrder setZOrder) {
    if (!isWindowFollowerGroupValid(host, followers))
        return {false, false};
    const bool hostPromoted = setZOrder(host, Handle{});
    bool followersPlaced = true;
    Handle insertAfter = host;
    for (const Handle follower : followers) {
        const bool followerPlaced = setZOrder(follower, insertAfter);
        followersPlaced = followerPlaced && followersPlaced;
        insertAfter = follower;
    }
    return {hostPromoted, followersPlaced};
}

template <typename Handle, typename Activate, typename SetZOrder>
inline WindowFollowerActivationResult activateWindowFollowerGroup(
    Handle host, const QList<Handle> &followers,
    Activate activate, SetZOrder setZOrder) {
    if (!isWindowFollowerGroupValid(host, followers) || !activate(host))
        return {false, false, false};
    const WindowFollowerPromotionResult promotion =
        promoteWindowFollowerGroup(host, followers, setZOrder);
    return {true, promotion.hostPromoted, promotion.followersPlaced};
}

}  // namespace prism::detail
