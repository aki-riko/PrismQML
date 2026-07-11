// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Fixed public visual presets 固定公开视觉预设
var themes = {
    "classic":  { main: "#00ff00", head: "#aaffaa", bg: "#000000" },
    "cyan":     { main: "#00ffff", head: "#aaffff", bg: "#000011" },
    "amber":    { main: "#ffaa00", head: "#ffff00", bg: "#0a0500" },
    "red":      { main: "#ff0040", head: "#ff8888", bg: "#0a0000" },
    "purple":   { main: "#aa00ff", head: "#ffaaff", bg: "#050005" },
    "blue":     { main: "#0088ff", head: "#88ccff", bg: "#000510" },
    "white":    { main: "#ffffff", head: "#ffffff", bg: "#111111" },
    "pink":     { main: "#ff69b4", head: "#ffb6c1", bg: "#0a0008" },
    "gold":     { main: "#ffd700", head: "#ffec8b", bg: "#0a0800" },
    "lime":     { main: "#32cd32", head: "#90ee90", bg: "#000a00" },
    "orange":   { main: "#ff6600", head: "#ffaa66", bg: "#0a0300" },
    "teal":     { main: "#008080", head: "#40e0d0", bg: "#000505" },
    "neon":     { main: "#39ff14", head: "#7fff00", bg: "#000000" },
    "sunset":   { main: "#ff4500", head: "#ff8c00", bg: "#1a0a00" },
    "ocean":    { main: "#006994", head: "#00ced1", bg: "#001015" },
    "forest":   { main: "#228b22", head: "#98fb98", bg: "#000800" },
    "midnight": { main: "#191970", head: "#6495ed", bg: "#000008" }
}

var themeNames = [
    "classic", "cyan", "amber", "red", "purple", "blue", "white",
    "pink", "gold", "lime", "orange", "teal", "neon", "sunset",
    "ocean", "forest", "midnight"
]
