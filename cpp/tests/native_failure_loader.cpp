// coding: utf-8
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Pre-main loader-failure fixture. main 前加载失败夹具。

extern "C" __declspec(dllimport) int prismNativeFailureCompanion();

int main() {
    return prismNativeFailureCompanion() == 42 ? 0 : 1;
}
