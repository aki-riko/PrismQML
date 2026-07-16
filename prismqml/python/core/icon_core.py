# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

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

_SVG_NAMESPACE_URI = "http://www.w3.org/2000/svg"


def _qfile_svg_path(svg_path: str) -> str:
    return ":" + svg_path[4:] if svg_path.startswith("qrc:/") else svg_path


def _read_svg_text(svg_path: str) -> Optional[str]:
    handle = QFile(_qfile_svg_path(svg_path))
    if not handle.open(QFile.ReadOnly):
        return None
    try:
        return bytes(handle.readAll()).decode("utf-8")
    finally:
        handle.close()


def _prepare_svg_rewrite(overrides, only_paths):
    selected = set(only_paths) if only_paths is not None else None
    normalized = {str(k): str(v) for k, v in (overrides or {}).items()}
    return selected, normalized


def _create_svg_stream(raw_text: str):
    reader = QXmlStreamReader(raw_text)
    sink = QBuffer()
    sink.open(QIODevice.WriteOnly)
    writer = QXmlStreamWriter(sink)
    writer.setAutoFormatting(False)
    return reader, sink, writer


def _write_namespace_declarations(writer, declarations) -> None:
    for declaration in declarations:
        prefix = declaration.prefix()
        name = ("xmlns:" + prefix) if prefix else "xmlns"
        writer.writeAttribute(name, declaration.namespaceUri())


def _write_start_element(writer, qualified_name, declarations, attributes) -> None:
    writer.writeStartElement(qualified_name)
    _write_namespace_declarations(writer, declarations)
    for name, value in attributes:
        writer.writeAttribute(name, value)


def _is_svg_path(name, namespace_uri, root_is_legacy_svg) -> bool:
    if name != "path":
        return False
    return namespace_uri == _SVG_NAMESPACE_URI or (
        namespace_uri == "" and root_is_legacy_svg
    )


def _merged_path_attributes(attributes, overrides, hit):
    merged = {attribute.qualifiedName(): attribute.value() for attribute in attributes}
    if hit:
        merged.update(overrides)
    return merged.items()


def _write_svg_start_element(
    reader, writer, selected, overrides, path_seq, root_is_legacy_svg
):
    name = reader.name()
    qualified_name = reader.qualifiedName()
    namespace_uri = reader.namespaceUri()
    attributes = reader.attributes()
    if root_is_legacy_svg is None:
        root_is_legacy_svg = name == "svg" and namespace_uri == ""
    declarations = reader.namespaceDeclarations()
    if _is_svg_path(name, namespace_uri, root_is_legacy_svg):
        path_seq += 1
        hit = selected is None or path_seq in selected
        output_attributes = _merged_path_attributes(attributes, overrides, hit)
    else:
        output_attributes = (
            (attribute.qualifiedName(), attribute.value())
            for attribute in attributes
        )
    _write_start_element(
        writer, qualified_name, declarations, output_attributes
    )
    return path_seq, root_is_legacy_svg


def _write_start_document(reader, writer) -> None:
    version = reader.documentVersion()
    if version:
        writer.writeStartDocument(version, reader.isStandaloneDocument())
    else:
        writer.writeStartDocument()


def _write_characters(reader, writer) -> None:
    if reader.isCDATA():
        writer.writeCDATA(reader.text())
    else:
        writer.writeCharacters(reader.text())


def _copy_svg_token(reader, writer, token) -> None:
    if token == QXmlStreamReader.StartDocument:
        _write_start_document(reader, writer)
    elif token == QXmlStreamReader.EndDocument:
        writer.writeEndDocument()
    elif token == QXmlStreamReader.EndElement:
        writer.writeEndElement()
    elif token == QXmlStreamReader.Characters:
        _write_characters(reader, writer)
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


def _finish_svg_rewrite(reader, sink, svg_path: str) -> str:
    if reader.hasError():
        error_message = reader.errorString()
        line_number = reader.lineNumber()
        column_number = reader.columnNumber()
        sink.close()
        raise ValueError(
            f"SVG XML 解析失败: {svg_path} "
            f"(line={line_number}, column={column_number}): {error_message}"
        )
    sink.close()
    return bytes(sink.data()).decode("utf-8")


def _rewrite_svg_stream(raw_text, selected, overrides, svg_path: str) -> str:
    reader, sink, writer = _create_svg_stream(raw_text)
    path_seq = -1
    root_is_legacy_svg = None
    while not reader.atEnd():
        token = reader.readNext()
        if reader.hasError():
            break
        if token == QXmlStreamReader.StartElement:
            path_seq, root_is_legacy_svg = _write_svg_start_element(
                reader, writer, selected, overrides,
                path_seq, root_is_legacy_svg,
            )
        else:
            _copy_svg_token(reader, writer, token)
    return _finish_svg_rewrite(reader, sink, svg_path)


def _rewrite_svg_attrs(
    svg_path: str,
    overrides: dict,
    *,
    only_paths: Optional[Iterable[int]] = None,
) -> str:
    """流式覆盖 SVG ``<path>`` 属性并返回新的 XML 字符串。

    Args:
        svg_path: SVG 本地文件或 ``qrc:/`` 资源路径; 非 ``.svg`` 直接返回空串。
        overrides: 要写到命中 ``<path>`` 上的属性映射, 例如 ``{"fill": "#ff0000"}``。
            空映射只做流式复制。
        only_paths: 仅作用于这些零基 ``<path>`` 序号; ``None`` 表示全部,
            空集合表示一个都不改。

    Raises:
        ValueError: SVG 内容不是合法 XML, 不返回不可渲染的部分输出。
    """
    if not svg_path.lower().endswith(".svg"):
        return ""
    raw_text = _read_svg_text(svg_path)
    if raw_text is None:
        return ""
    selected, normalized = _prepare_svg_rewrite(overrides, only_paths)
    return _rewrite_svg_stream(raw_text, selected, normalized, svg_path)


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
