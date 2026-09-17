# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Touch adaptation source gate. 触摸适配源码门禁。

规则: `prismqml/PrismQML` 下每个在**代码**中使用 hover 原语的 QML 文件（含
`_internal` 委托, 因为真实交互面常常就在委托里）必须
  1) 引用 `Touch.` (已做触摸适配), 或
  2) 出现在带原因的显式豁免表中。
注释里的 hover 字样不计入; 任何新增的 hover 控件都会让本门禁失败, 从而阻止触摸适配回流。
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
QMLDIR = QML_ROOT / "qmldir"
TOUCH_SINGLETON = QML_ROOT / "Touch.qml"
METRICS_SOURCE = QML_ROOT / "PrismEnums" / "Metrics.qml"

HOVER_PATTERN = re.compile(
    r"hoverEnabled|containsMouse|HoverHandler|HoverBehavior|onEntered|onExited"
)
# A real touch decision: the mapping helpers, or a Touch.isTouch test applied on
# the same line as the hover state. 真正的触摸决策: 映射助手, 或同一行里把
# Touch.isTouch 作用在 hover 状态上; 只出现 "Touch." 字样的死引用不算。
TOUCH_DECISION = re.compile(r"Touch\.feedback\(|Touch\.reveal\(|Touch\.target\(")
HOVER_STATE = re.compile(r"hovered|containsMouse|hoverEnabled|HoverHandler")
LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def code_only(source: str) -> str:
    """Drop comments so the gate measures code, not prose. 去注释, 只量代码。"""
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", source))


def has_touch_decision(code: str) -> bool:
    """True when the file actually branches on touch for its hover state.

    Bindings are often wrapped over several lines, so the Touch.isTouch test is
    matched against a small window instead of a single line.
    绑定常折行, 因此 Touch.isTouch 与 hover 状态的配对按小窗口判定而非单行。
    """
    if TOUCH_DECISION.search(code):
        return True
    lines = code.splitlines()
    for index, line in enumerate(lines):
        if "Touch.isTouch" not in line:
            continue
        window = lines[max(0, index - 3) : index + 4]
        if any(HOVER_STATE.search(candidate) for candidate in window):
            return True
    return False

# Controls whose hover usage carries no visual feedback of its own, so there is no
# touch branch to add. 仅用于逻辑(预热/光标/tooltip/命中管线)的 hover: 无视觉分支可加。
TOUCH_EXEMPT = {
    "effects/HoverBehavior.qml": "hover 动画助手本体, 只对鼠标 hover 有意义",
    "controls/utils/WindowDragHandle.qml": "鼠标拖动窗口句柄, 触摸端不存在该交互",
    "controls/auth/_internal/LoginWindowContent.qml":
        "无 hover 视觉; MouseArea 只做光标/预热/登录模式切换",
    "controls/buttons/Button/_internal/ButtonInteraction.qml":
        "纯 MouseArea, hover 只触发菜单预热, 自身无视觉",
    "controls/containers/_internal/WidgetToolTipSupport.qml":
        "hover 只驱动 tooltip 计时与预热, 属逻辑非视觉",
    "controls/data/Carousel/_internal/CarouselFactories.qml":
        "揭示决策已在 Carousel.qml 经 Touch.reveal 完成, 此处只是创建顺序闩",
    "controls/data/Chart/_internal/BoxplotChartArea.qml":
        "hover 视觉由共享 hoveredIndex 命令式写入, 本组件无按压源; 配套 tooltip 属保留逻辑",
    "controls/data/Chart/_internal/BoxplotChartContent.qml":
        "hover 是指针到索引的命中管线, 其点击路径依赖它, 属逻辑非视觉",
    "controls/feedback/Tooltip/TipPopup.qml":
        "不可见 Item, hover 只触发 prewarm",
    "controls/inputs/ImageCropper.qml":
        "无 hover 视觉, hover 只触发 prewarm",
    "controls/inputs/InputCore.qml":
        "hovered 是公开转发状态, 本文件无 hover 视觉 (hoverEnabled 只服务 cursorShape)",
    "controls/inputs/LineEdit/LineEditLabel.qml":
        "HoverHandler 仅向上转发 hovered, 全仓无视觉消费者",
    "controls/inputs/LineEdit/LineEditNormal.qml":
        "HoverHandler 仅向上转发 hovered, 全仓无视觉消费者",
    "controls/inputs/LineEdit/TagLineEdit.qml":
        "HoverHandler 仅向上转发 hovered, 全仓无视觉消费者",
    "controls/menus/_internal/ActionTooltipShowTimer.qml":
        "hover 只驱动动作 tooltip 的延时计时",
    "controls/inputs/CycleWheelPicker.qml":
        "hover 揭示的滚动按钮已在 _internal/CycleWheelPickerButtons.qml 经 Touch.reveal 常显",
}

# Hover input ports: helpers that receive a hover state and turn it into visuals.
# 接收 hover 状态并产出视觉的助手: 必须由已做触摸适配的源头喂入, 否则门禁扫不到。
HOVER_INPUT_HELPERS = {
    "controls/buttons/Button/ButtonStyleHelper.qml": {
        "owner": "controls/buttons/Button/ButtonCore.qml",
        "marker": "_styleEffectiveEnabled, _touchActive, pressed",
        "note": "ButtonCore 以 _touchActive 作为 helper 的 hovered 入参",
    },
    "controls/inputs/ComboBox/_internal/ComboBoxStyleHelper.qml": {
        "owner": "controls/inputs/ComboBox/ComboBoxCore.qml",
        "marker": "readonly property bool hovered: Touch.feedback(",
        "note": "ComboBoxCore.hovered 在源头经 Touch.feedback 映射",
    },
}

# Interactive controlSize tokens raised to the touch floor 抬到触摸下限的交互 token
FLOORED_TOKENS = (
    "inputHeight",
    "inputHeightLarge",
    "inputHeightCompact",
    "pickerRow",
    "tabBarHeight",
    "segmentedHeight",
    "segmentedToolSize",
    "commandBarButtonSize",
    "calendarCell",
    "calendarCellHeight",
    "closeButton",
    "buttonHeight",
    "dialogButtonHeight",
    "emptyStateButtonHeight",
    "topNavItemHeight",
    "navItemHeight",
    "closeButtonSize",
    "flipViewNavButton",
    "tableHeaderHeight",
    "listItemHeight",
    "toolButtonWidth",
    "wheelPickerItemHeight",
    "wheelPickerRowHeight",
    "toolBoxItemHeight",
    "treeItemHeight",
    "itemHeight",
)


def _hover_sources() -> dict[str, str]:
    """Map repo-relative QML path -> raw source for every hover-using file. 全部 hover 文件。"""
    controls: dict[str, str] = {}
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(QML_ROOT)
        if relative.parts[0] == "PrismEnums":
            continue
        source = path.read_text(encoding="utf-8")
        if HOVER_PATTERN.search(code_only(source)):
            controls[relative.as_posix()] = source
    return controls

def test_touch_singleton_is_registered():
    assert TOUCH_SINGLETON.exists()
    source = TOUCH_SINGLETON.read_text(encoding="utf-8")
    qmldir = QMLDIR.read_text(encoding="utf-8")

    assert "pragma Singleton" in source
    assert "singleton Touch Touch.qml" in qmldir
    for api in (
        "readonly property bool isTouch",
        "readonly property int minTargetSize",
        "function feedback(hovered, pressed)",
        "function reveal(hovered)",
        "function target(desktopSize)",
    ):
        assert api in source, api


def test_interactive_metrics_keep_the_touch_floor():
    source = METRICS_SOURCE.read_text(encoding="utf-8")
    for token in FLOORED_TOKENS:
        assert re.search(
            rf"readonly property int {token}: Math\.max\(\d+, root\.touchTargetFloor\)",
            source,
        ), token


def test_every_hover_control_is_touch_adapted_or_exempt():
    controls = _hover_sources()
    assert controls, "hover scan found no controls"

    missing = [
        relative
        for relative, source in controls.items()
        if relative not in TOUCH_EXEMPT and not has_touch_decision(code_only(source))
    ]
    assert missing == [], (
        "这些文件在代码里使用 hover 但没有真正的触摸决策 (Touch.feedback/reveal/target, "
        "或把 Touch.isTouch 作用在 hover 状态上; 仅出现 Touch. 字样的死引用不算); "
        "请按规范适配, 或加入 TOUCH_EXEMPT 并写明理由: " + ", ".join(missing)
    )


def test_touch_exemptions_are_live_and_justified():
    controls = _hover_sources()
    for relative, reason in TOUCH_EXEMPT.items():
        assert relative in controls, f"豁免项已不适用(文件不存在或不含 hover): {relative}"
        assert len(reason.strip()) >= 8, f"豁免理由过短: {relative}"


def test_hover_input_helpers_are_fed_by_touch_aware_owners():
    for helper, spec in HOVER_INPUT_HELPERS.items():
        helper_source = (QML_ROOT / helper).read_text(encoding="utf-8")
        assert "hovered" in code_only(helper_source), helper
        owner_source = (QML_ROOT / spec["owner"]).read_text(encoding="utf-8")
        assert spec["marker"] in code_only(owner_source), (
            f"{helper} 的 hover 入参必须由 {spec['owner']} 经触摸适配喂入 "
            f"({spec['note']}); 缺少标记: {spec['marker']}"
        )
