// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// ConstantsStaticData - Static palette data 静态调色板数据
// Plain objects keep static data out of the QML object tree without adding types.
// 使用普通对象承载静态数据，避免为数据命名空间新增 QML 类型。

function semanticColors() {
    return {
        infoLight: "#676767", successLight: "#0f7b0f", warningLight: "#9d5d00",
        errorLight: "#c42b1c", processingLight: "#7b2cbf", attentionLight: "#0a93a8",
        cautionLight: "#b88600", infoDark: "#a3a3a3", successDark: "#6ccb5f",
        warningDark: "#c09000", errorDark: "#ff99a4", processingDark: "#d8b4fe",
        attentionDark: "#33b5bf", cautionDark: "#e8c547", infoBgLight: "#cce4f7",
        successBgLight: "#dff6dd", warningBgLight: "#fff4ce", errorBgLight: "#fde7e9",
        attentionBgLight: "#f0e6fa", processingBgLight: "#f3e8ff", cautionBgLight: "#fff8d6"
    }
}

function demoPalette() {
    return {
        blue: "#3b82f6", green: "#10b981", orange: "#f59e0b", red: "#ef4444",
        purple: "#8b5cf6", cyan: "#06b6d4", teal: "#14b8a6", pink: "#ec4899",
        sky: "#0ea5e9", lime: "#84cc16"
    }
}

function colorPalette() {
    return {
        automaticColor: "#000000",
        themeColors: [
            "#ffffff", "#000000", "#e7e6e6", "#44546a", "#4472c4", "#ed7d31", "#a5a5a5", "#ffc000", "#5b9bd5", "#70ad47",
            "#f2f2f2", "#7f7f7f", "#d0cece", "#d6dce4", "#d9e2f3", "#fbe5d5", "#ededed", "#fff2cc", "#deebf6", "#e2efd9",
            "#d8d8d8", "#595959", "#aeabab", "#adb9ca", "#b4c6e7", "#f7cbac", "#dbdbdb", "#ffe599", "#bdd7ee", "#c5e0b3",
            "#bfbfbf", "#3f3f3f", "#757070", "#8496b0", "#8eaadb", "#f4b183", "#c9c9c9", "#ffd966", "#9cc3e5", "#a8d08d",
            "#a5a5a5", "#262626", "#3a3838", "#323f4f", "#2f5496", "#c55a11", "#7b7b7b", "#bf9000", "#2e75b5", "#538135",
            "#7f7f7f", "#0c0c0c", "#171616", "#222a35", "#1f3864", "#833c0b", "#525252", "#7f6000", "#1e4e79", "#375623"
        ],
        standardColors: ["#c00000", "#ff0000", "#ffc000", "#ffff00", "#92d050", "#00b050", "#00b0f0", "#0070c0", "#002060", "#7030a0"]
    }
}

function colorPickerGradient() {
    return {
        huePos0: 0.0, huePos1: 0.166, huePos2: 0.333, huePos3: 0.5,
        huePos4: 0.666, huePos5: 0.833, huePos6: 1.0,
        hueColor0: "#ff0000", hueColor1: "#ffff00", hueColor2: "#00ff00",
        hueColor3: "#00ffff", hueColor4: "#0000ff", hueColor5: "#ff00ff", hueColor6: "#ff0000",
        lightnessDark: "#000000", lightnessMid: "#808080", lightnessLight: "#ffffff"
    }
}
