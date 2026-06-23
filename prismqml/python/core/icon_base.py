# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是 FluentQML 的一部分, 采用 MIT 许可证授权。
"""图标基础设施

定义 Fluent 风格图标的抽象基类与两类 QIconEngine:
* :class:`IconCore` —— 资源类图标的协议入口
* :class:`SvgRenderEngine`  —— 直接渲染 SVG 字符串的引擎
* :class:`ThemedIconProxy` —— 跟随主题切换颜色的代理引擎

模块同时暴露 :func:`resolveIconColor`, 给具体图标实现按主题拼资源路径用。
"""

from typing import Iterable, Optional

from PySide6.QtCore import (
    QBuffer,
    QFile,
    QIODevice,
    QRect,
    QRectF,
    QXmlStreamReader,
    QXmlStreamWriter,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QIcon,
    QIconEngine,
    QPainter,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer

from .theme import Theme, isDark


# ---------------------------------------------------------------------------
# 主题颜色解析
# ---------------------------------------------------------------------------

# 解析后的 (reverse, theme) 元组到颜色字符串的映射表。
# 比起 if/else 三元链, 查表写法既能省掉中间变量也方便后续扩主题。
_THEME_COLOR_TABLE = {
    (False, Theme.LIGHT): "black",
    (False, Theme.DARK):  "white",
    (True,  Theme.LIGHT): "white",
    (True,  Theme.DARK):  "black",
}


def resolveIconColor(theme: Theme = Theme.AUTO, reverse: bool = False) -> str:
    """返回当前主题对应的图标颜色名称。

    返回值固定为 ``"black"`` 或 ``"white"``, 由资源命名约定 ``XXX_black.svg`` /
    ``XXX_white.svg`` 拼接路径时使用。

    Args:
        theme: 目标主题; ``Theme.AUTO`` 时按 :func:`isDark` 实时解析。
        reverse: 反转色, 用于在浅色背景上显示白色图标这类反差需求。
    """
    resolved = theme
    if resolved == Theme.AUTO:
        resolved = Theme.DARK if isDark() else Theme.LIGHT
    return _THEME_COLOR_TABLE[(reverse, resolved)]


# ---------------------------------------------------------------------------
# SVG 属性流式重写
# ---------------------------------------------------------------------------

def _rewrite_svg_attrs(
    svg_path: str,
    overrides: dict,
    *,
    only_paths: Optional[Iterable[int]] = None,
) -> str:
    """读 SVG 文件并在 ``<path>`` 元素上覆盖属性, 返回新的 SVG 字符串。

    采用 :class:`QXmlStreamReader` / :class:`QXmlStreamWriter` 流式拷贝原始
    token, 只在命中目标 ``<path>`` 时替换属性, 其余节点(注释、命名空间、文本)
    按原样写出, 不做整树重排。

    Args:
        svg_path: SVG 文件路径; 非 ``.svg`` 直接返回空串。
        overrides: 要写到命中 ``<path>`` 上的属性映射, 例如 ``{"fill": "#ff0000"}``。
            空 dict 表示不改任何属性 (只做一遍流式拷贝)。
        only_paths: 仅作用于这些 ``<path>`` 序号 (强制关键字传入); ``None`` 表示
            对所有 ``<path>`` 生效; 空集合 ``[]`` 表示一个都不改 (语义比
            "None=全部、[]=全部"更精确)。
    """
    if not svg_path.lower().endswith(".svg"):
        return ""

    handle = QFile(svg_path)
    if not handle.open(QFile.ReadOnly):
        return ""
    try:
        raw_text = bytes(handle.readAll()).decode("utf-8")
    finally:
        handle.close()

    selected = set(only_paths) if only_paths is not None else None
    overrides = {str(k): str(v) for k, v in (overrides or {}).items()}

    reader = QXmlStreamReader(raw_text)
    sink = QBuffer()
    sink.open(QIODevice.WriteOnly)
    writer = QXmlStreamWriter(sink)
    writer.setAutoFormatting(False)

    path_seq = -1

    while not reader.atEnd():
        token = reader.readNext()
        if reader.hasError():
            break

        if token == QXmlStreamReader.StartDocument:
            # documentVersion() 在没有 XML 声明时返回空, 这时退化到默认版本
            # 避免输出 version="" 这种不合规 XML 头。
            version = reader.documentVersion()
            if version:
                writer.writeStartDocument(version, reader.isStandaloneDocument())
            else:
                writer.writeStartDocument()
        elif token == QXmlStreamReader.EndDocument:
            writer.writeEndDocument()
        elif token == QXmlStreamReader.StartElement:
            name = reader.name()
            attrs_iter = reader.attributes()
            # 命名空间声明 (xmlns / xmlns:xlink 等) 通过 namespaceDeclarations()
            # 单独取, 不出现在 attributes() 里。直接当普通 xmlns* 属性写出去,
            # 避开 writer 自身的命名空间状态机自动加 n1 前缀的副作用。
            ns_decls = reader.namespaceDeclarations()
            if name == "path":
                path_seq += 1
                hit = selected is None or path_seq in selected
                writer.writeStartElement(name)
                for nd in ns_decls:
                    pref = nd.prefix()
                    writer.writeAttribute(
                        ("xmlns:" + pref) if pref else "xmlns", nd.namespaceUri()
                    )
                # 用 qualifiedName 保留 xlink:href 这类带前缀属性。
                merged = {a.qualifiedName(): a.value() for a in attrs_iter}
                if hit:
                    merged.update(overrides)
                for ak, av in merged.items():
                    writer.writeAttribute(ak, av)
            else:
                writer.writeStartElement(name)
                for nd in ns_decls:
                    pref = nd.prefix()
                    writer.writeAttribute(
                        ("xmlns:" + pref) if pref else "xmlns", nd.namespaceUri()
                    )
                for a in attrs_iter:
                    writer.writeAttribute(a.qualifiedName(), a.value())
        elif token == QXmlStreamReader.EndElement:
            writer.writeEndElement()
        elif token == QXmlStreamReader.Characters:
            if reader.isCDATA():
                writer.writeCDATA(reader.text())
            else:
                writer.writeCharacters(reader.text())
        elif token == QXmlStreamReader.Comment:
            writer.writeComment(reader.text())
        elif token == QXmlStreamReader.ProcessingInstruction:
            writer.writeProcessingInstruction(
                reader.processingInstructionTarget(),
                reader.processingInstructionData(),
            )
        elif token == QXmlStreamReader.DTD:
            writer.writeDTD(reader.text())
        elif token == QXmlStreamReader.EntityReference:
            writer.writeEntityReference(reader.name())

    sink.close()
    return bytes(sink.data()).decode("utf-8")


# ---------------------------------------------------------------------------
# QIconEngine 实现
# ---------------------------------------------------------------------------

def _bake_pixmap(engine: QIconEngine, size, mode, state) -> QPixmap:
    """共用 pixmap 构造逻辑 —— 把引擎的 paint 结果烘到 QPixmap。

    遵循 Qt 的 QIconEngine 约定 (engine.paint 到目标 rect)。
    若 size 不合法 (宽或高 ≤ 0) 或 :class:`QPainter` 在目标 pixmap 上无法激活,
    直接返回空 pixmap; 不再尝试在非 active painter 上 paint, 避免静默丢帧。
    """
    if size.width() <= 0 or size.height() <= 0:
        return QPixmap()

    # 直接构造目标尺寸的 pixmap 并清成全透明背景, 再让引擎 paint 上去。
    # 现代 Qt 的 QPixmap 默认即带 alpha 通道, 无需经 QImage 中转。
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    if not painter.isActive():
        # 极端 case: pixmap 内存分配失败 / size 非法。返回空 pixmap 而非空白图,
        # 让上层能识别失败状态。
        return QPixmap()
    try:
        rect = QRect(0, 0, size.width(), size.height())
        engine.paint(painter, rect, mode, state)
    finally:
        painter.end()
    return pixmap


class SvgRenderEngine(QIconEngine):
    """基于 SVG 字符串的图标引擎。

    持有 SVG 文本本身 (而非文件路径), 适合需要在运行时
    改属性 (例如填充色) 的场景。
    """

    def __init__(self, svg_source: str):
        super().__init__()
        self._svgSource = svg_source

    def paint(self, painter: QPainter, rect, mode, state) -> None:  # noqa: ARG002
        QSvgRenderer(self._svgSource.encode()).render(painter, QRectF(rect))

    def clone(self) -> QIconEngine:
        return SvgRenderEngine(self._svgSource)

    def pixmap(self, size, mode, state) -> QPixmap:
        return _bake_pixmap(self, size, mode, state)


class ThemedIconProxy(QIconEngine):
    """随主题切换颜色的图标引擎代理。

    内部包一个 :class:`IconCore` 实例 (或裸 ``str`` 资源路径),
    paint 时按当前主题挑选合适的 :class:`QIcon` 重新绘制。
    """

    def __init__(self, icon, reverse: bool = False):
        super().__init__()
        self._iconSource = icon
        self._invertTheme = reverse

    # 弱化态 -> 不透明度。元组按优先级线性匹配, 未命中走全不透明。
    _DIMMED_STATES = (
        (QIcon.Disabled, 0.5),
        (QIcon.Selected, 0.7),
    )

    @classmethod
    def _state_alpha(cls, mode) -> float:
        """按 QIcon 渲染模式给出绘制不透明度。

        非激活态降低 alpha 以呈现"弱化"观感; 其余模式全不透明。
        """
        for state, alpha in cls._DIMMED_STATES:
            if mode == state:
                return alpha
        return 1.0

    def _resolve_theme(self) -> Theme:
        if not self._invertTheme:
            return Theme.AUTO
        return Theme.LIGHT if isDark() else Theme.DARK

    def _build_qicon(self) -> QIcon:
        """把当前图标源在当前主题下物化成一个可绘制的 QIcon。"""
        source = self._iconSource
        if isinstance(source, IconCore):
            return make_icon(source, self._resolve_theme())
        return QIcon(source)

    def paint(self, painter: QPainter, rect, mode, state) -> None:
        painter.save()
        try:
            painter.setOpacity(self._state_alpha(mode))
            self._build_qicon().paint(
                painter, rect, Qt.AlignCenter, QIcon.Normal, state
            )
        finally:
            painter.restore()

    def clone(self) -> QIconEngine:
        return ThemedIconProxy(self._iconSource, self._invertTheme)

    def pixmap(self, size, mode, state) -> QPixmap:
        return _bake_pixmap(self, size, mode, state)


# ---------------------------------------------------------------------------
# 抽象图标基类
# ---------------------------------------------------------------------------

class IconCore:
    """Fluent 风格图标的抽象契约。

    本类只规定一件事: 子类必须实现 :meth:`path`, 把图标标识映射到一个
    可被加载的资源路径 (本地文件或 ``qrc:`` 资源)。

    与图标相关的行为 (构造 QIcon、跟随主题、按属性填色渲染) 不挂在本契约上,
    而是由模块级函数 :func:`make_icon` / :func:`make_theme_icon` /
    :func:`paint_icon` 接收一个 ``IconCore`` 来完成。这样图标"是什么"(契约)
    与"怎么画"(策略) 彻底分离, 子类只需关心前者。
    """

    def path(self, theme: Theme = Theme.AUTO) -> str:
        """返回图标资源路径。

        子类必须实现。常见做法是用 :func:`resolveIconColor` 拼出 ``foo_black.svg``
        / ``foo_white.svg`` 然后在本地与 ``qrc:`` 之间挑一个返回。
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 图标行为函数 —— 接收 IconCore, 输出 QIcon / 直接绘制
# ---------------------------------------------------------------------------

def _is_svg(asset_path: str) -> bool:
    return asset_path.lower().endswith(".svg")


def make_icon(
    icon: "IconCore",
    theme: Theme = Theme.AUTO,
    color: Optional[QColor] = None,
) -> QIcon:
    """由 :class:`IconCore` 构造一个静态 :class:`QIcon`。

    仅当给定 ``color`` 且资源为 SVG 时才覆盖填色, 否则直接按路径加载。
    """
    asset_path = icon.path(theme)
    if color is None or not _is_svg(asset_path):
        return QIcon(asset_path)
    tinted = _rewrite_svg_attrs(asset_path, {"fill": QColor(color).name()})
    return QIcon(SvgRenderEngine(tinted))


def make_theme_icon(icon: "IconCore", reverse: bool = False) -> QIcon:
    """构造跟随主题切换的 :class:`QIcon`, 适合放进 menu / action / 托盘。"""
    return QIcon(ThemedIconProxy(icon, reverse))


def paint_icon(
    painter: QPainter,
    rect,
    icon: "IconCore",
    theme: Theme = Theme.AUTO,
    path_indexes: Optional[Iterable[int]] = None,
    **attributes: str,
) -> None:
    """把 :class:`IconCore` 直接绘制到 ``rect``。

    非 SVG 资源走位图绘制; SVG 资源在带 ``attributes`` 时先重写属性再渲染。
    """
    asset_path = icon.path(theme)

    if not _is_svg(asset_path):
        bitmap = QIcon(asset_path)
        target = QRectF(rect).toRect()
        painter.drawPixmap(target, bitmap.pixmap(target.size()))
        return

    if attributes:
        payload = _rewrite_svg_attrs(asset_path, attributes, only_paths=path_indexes).encode()
        QSvgRenderer(payload).render(painter, QRectF(rect))
    else:
        QSvgRenderer(asset_path).render(painter, QRectF(rect))


__all__ = [
    "IconCore",
    "ThemedIconProxy",
    "SvgRenderEngine",
    "resolveIconColor",
    "make_icon",
    "make_theme_icon",
    "paint_icon",
]
