// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 原生附属窗口几何私有工具
#pragma once

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
    bool followerPlaced;
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

template <typename Handle, typename SetZOrder>
inline WindowFollowerPromotionResult promoteWindowFollowerGroup(
    Handle host, Handle follower, SetZOrder setZOrder) {
    if (!host || !follower)
        return {false, false};
    const bool hostPromoted = setZOrder(host, Handle{});
    const bool followerPlaced = setZOrder(follower, host);
    return {hostPromoted, followerPlaced};
}

}  // namespace prism::detail
