// RepeaterModel - Model adapter for the virtualized repeaters 虚拟化重复器的模型适配
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

// Supported models 支持的模型:
//   * number                       — count only, modelData is the index 仅计数, modelData 为索引
//   * JS array                     — modelData is the entry 数组项本身
//   * ListModel / QAbstractItemModel with count()+get()  — modelData is the role object 角色对象
function dataAt(model, index) {
    if (model === null || model === undefined) return undefined
    if (index < 0) return undefined
    if (typeof model === "number") {
        return index < model ? index : undefined
    }
    if (typeof model.get === "function") {
        return model.get(index)
    }
    if (typeof model.length === "number") {
        return index < model.length ? model[index] : undefined
    }
    return undefined
}
