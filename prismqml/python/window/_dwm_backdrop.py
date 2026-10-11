# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""DWM system backdrop attributes and application. DWM 系统背板属性与应用。

把系统背板的 DWM 属性常量、背板类型映射与应用流程从 ``mica_window`` 中独立出来：
既让 ``mica_window`` 保持 §5.1 的单文件行数上限，也让 QML(PrismEnums/Backdrop.qml)
与 Python 共用同一套背板编号。
"""

from typing import Any, Optional

from ..core.logger import error, warning

# Windows 11 build number threshold Windows 11 版本号阈值
WIN11_BUILD_THRESHOLD = 22000

# DWMWA_SYSTEMBACKDROP_TYPE 最低支持版本（Win11 22H2）
# Build 22000-22621 之间无此接口，调用会静默失败
WIN11_BACKDROP_BUILD_THRESHOLD = 22621

# DWM constants DWM 常量
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWA_SYSTEMBACKDROP_TYPE = 38  # 需要 Build >= 22621

# Window corner preference 窗口圆角偏好
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2

# DWM backdrop type values DWM背景类型值
DWM_BACKDROP_NONE = 1        # DWMSBT_NONE
DWM_BACKDROP_MICA = 2        # DWMSBT_MAINWINDOW (Mica)
DWM_BACKDROP_ACRYLIC = 3     # DWMSBT_TRANSIENTWINDOW (Acrylic)
DWM_BACKDROP_MICA_ALT = 4    # DWMSBT_TABBEDWINDOW (Mica Alt)
DWMWA_COLOR_NONE = 0xFFFFFFFE  # Suppress the DWM frame border 抑制 DWM 窗口边框

# Public backdrop token -> DWM value map; mirrors PrismEnums/Backdrop.qml.
# 公开背板令牌到 DWM 取值的映射；与 PrismEnums/Backdrop.qml 保持一致。
BACKDROP_TYPE_VALUES = {
    "none": DWM_BACKDROP_NONE,
    "mica": DWM_BACKDROP_MICA,
    "acrylic": DWM_BACKDROP_ACRYLIC,
    "mica_alt": DWM_BACKDROP_MICA_ALT,
}


def hresult_succeeded(result: int) -> bool:
    """Apply Windows SUCCEEDED semantics. 使用 Windows SUCCEEDED 语义。"""
    return int(result) >= 0


def resolve_backdrop_value(backdrop: Any) -> Optional[int]:
    """Resolve a backdrop token to its DWM value. 解析背板令牌为 DWM 取值。"""
    if backdrop is None:
        return None
    return BACKDROP_TYPE_VALUES.get(str(backdrop).strip().lower())


def apply_backdrop_attributes(manager, hwnd: int, backdrop: int) -> bool:
    """Apply rounded frame attributes plus one backdrop value. 应用圆角边框与背板类型。

    ``manager`` 是持有 DWM 调用适配器的 MicaManager；本模块只负责属性顺序与结果判定。
    """
    if manager._windows_build < WIN11_BACKDROP_BUILD_THRESHOLD:
        warning(
            "DWMWA_SYSTEMBACKDROP_TYPE requires Build >= "
            f"{WIN11_BACKDROP_BUILD_THRESHOLD}, current: {manager._windows_build}"
        )
        return False
    manager._set_dwm_int_attribute(
        hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND
    )
    border_result = manager._set_dwm_color_attribute(
        hwnd, DWMWA_BORDER_COLOR, DWMWA_COLOR_NONE
    )
    if not hresult_succeeded(border_result):
        warning(f"DwmSetWindowAttribute border suppression failed: {border_result}")
    result = manager._set_dwm_int_attribute(
        hwnd, DWMWA_SYSTEMBACKDROP_TYPE, backdrop
    )
    if hresult_succeeded(result):
        return True
    warning(f"DwmSetWindowAttribute failed: {result}")
    return False


def apply_backdrop_request(manager, window, value: int, dark: bool, token: str) -> bool:
    """Apply one validated backdrop value and commit Mica state. 应用已验证背板并提交状态。

    micaEnabled 仍表示"存在生效的系统背板"：none 之外的类型提交为 True。
    """
    if not window:
        warning("Cannot set system backdrop: window is None")
        return False
    try:
        hwnd = int(window.winId())
        if not hwnd:
            warning("Cannot set system backdrop: window HWND is empty")
            return False
        manager._set_dwm_int_attribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0
        )
        if not apply_backdrop_attributes(manager, hwnd, value):
            return False
        manager._commit_mica_state(
            window, hwnd, value != DWM_BACKDROP_NONE, f"System backdrop '{token}'"
        )
        return True
    except (ValueError, OSError, TypeError) as e:
        error(f"Failed to set system backdrop: {e}")
        return False
