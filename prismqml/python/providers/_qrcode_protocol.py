# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Versioned QR image-provider protocol. 版本化二维码图片协议。"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any

from PySide6.QtGui import QColor

from ._qrcode_constants import DEFAULT_QR_CODE_SIZE


PROTOCOL_VERSION = 1
PROTOCOL_PREFIX = "v1."
IMAGE_SOURCE_PREFIX = "image://qrcode/"
DEFAULT_SIZE = DEFAULT_QR_CODE_SIZE
MIN_SIZE = 32
MAX_SIZE = 1024
MAX_CONTENT_UTF8_BYTES = 1024
MAX_JSON_BYTES = 6179
MAX_TOKEN_CHARS = 8239
MAX_PROVIDER_ID_CHARS = len(PROTOCOL_PREFIX) + MAX_TOKEN_CHARS
QUIET_ZONE_MODULES = 4
MAX_CACHE_ENTRIES = 64
MAX_CACHE_BYTES = 32 * 1024 * 1024
ERROR_LEVELS = frozenset({"L", "M", "Q", "H"})
_BASE64URL_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
)


class QRCodeProtocolError(ValueError):
    """Raised when a QR request violates the public protocol contract."""


@dataclass(frozen=True)
class QRCodeRequest:
    """Canonical QR request shared by the generator and provider."""

    content: str
    size: int
    foreground: str
    background: str
    error_level: str


def _validated_content(value: Any) -> str:
    if type(value) is not str or not value or "\x00" in value:
        raise QRCodeProtocolError("QR content must be a non-empty NUL-free string")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise QRCodeProtocolError("QR content contains invalid Unicode") from exc
    if len(encoded) > MAX_CONTENT_UTF8_BYTES:
        raise QRCodeProtocolError("QR content exceeds the UTF-8 byte limit")
    return value


def _validated_size(value: Any) -> int:
    if type(value) is not int or not MIN_SIZE <= value <= MAX_SIZE:
        raise QRCodeProtocolError("QR size is outside the supported range")
    return value


def _normalized_color(value: Any) -> str:
    if type(value) is not str:
        raise QRCodeProtocolError("QR colors must be strings")
    color = QColor(value)
    if not color.isValid() or color.alpha() != 255:
        raise QRCodeProtocolError("QR colors must be valid and opaque")
    return color.name(QColor.NameFormat.HexRgb).lower()


def _normalized_error_level(value: Any) -> str:
    if type(value) is not str:
        raise QRCodeProtocolError("QR error level must be a string")
    normalized = value.upper()
    if normalized not in ERROR_LEVELS:
        raise QRCodeProtocolError("QR error level must be L, M, Q, or H")
    return normalized


def create_request(
    content: Any,
    size: Any = DEFAULT_SIZE,
    foreground: Any = "#000000",
    background: Any = "#ffffff",
    error_level: Any = "M",
) -> QRCodeRequest:
    """Validate and canonicalize a producer request."""
    request = QRCodeRequest(
        content=_validated_content(content),
        size=_validated_size(size),
        foreground=_normalized_color(foreground),
        background=_normalized_color(background),
        error_level=_normalized_error_level(error_level),
    )
    if request.foreground == request.background:
        raise QRCodeProtocolError("QR foreground and background colors must differ")
    return request


def _canonical_json(request: QRCodeRequest) -> bytes:
    payload = [
        PROTOCOL_VERSION,
        request.content,
        request.size,
        request.foreground,
        request.background,
        request.error_level,
    ]
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8", errors="strict")
    if len(encoded) > MAX_JSON_BYTES:
        raise QRCodeProtocolError("QR protocol JSON exceeds its byte limit")
    return encoded


def encode_provider_id(request: QRCodeRequest) -> str:
    """Encode one canonical provider path segment."""
    token = (
        base64.urlsafe_b64encode(_canonical_json(request))
        .rstrip(b"=")
        .decode("ascii")
    )
    if len(token) > MAX_TOKEN_CHARS:
        raise QRCodeProtocolError("QR protocol token exceeds its character limit")
    return f"{PROTOCOL_PREFIX}{token}"


def build_image_source(
    content: Any,
    size: Any = DEFAULT_SIZE,
    foreground: Any = "#000000",
    background: Any = "#ffffff",
    error_level: Any = "M",
) -> str:
    """Return an image URL, or an empty string for invalid producer input."""
    try:
        request = create_request(content, size, foreground, background, error_level)
        return f"{IMAGE_SOURCE_PREFIX}{encode_provider_id(request)}"
    except QRCodeProtocolError:
        return ""


def _validated_token(provider_id: Any) -> str:
    if type(provider_id) is not str:
        raise QRCodeProtocolError("QR provider id must be a string")
    if (
        len(provider_id) > MAX_PROVIDER_ID_CHARS
        or not provider_id.startswith(PROTOCOL_PREFIX)
    ):
        raise QRCodeProtocolError("Unsupported QR provider protocol")

    token = provider_id[len(PROTOCOL_PREFIX) :]
    if (
        not token
        or len(token) > MAX_TOKEN_CHARS
        or any(character not in _BASE64URL_CHARS for character in token)
    ):
        raise QRCodeProtocolError("Invalid QR Base64URL token")
    return token


def _decoded_json(token: str) -> bytes:
    padding = "=" * ((4 - len(token) % 4) % 4)
    try:
        raw = base64.b64decode(
            f"{token}{padding}",
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise QRCodeProtocolError("Invalid QR Base64URL payload") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise QRCodeProtocolError("QR protocol JSON exceeds its byte limit")
    return raw


def _parsed_payload(raw: bytes):
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise QRCodeProtocolError("Invalid QR JSON payload") from exc

    if type(payload) is not list or len(payload) != 6:
        raise QRCodeProtocolError("QR JSON payload must contain exactly six fields")
    return payload


def _request_from_payload(payload) -> QRCodeRequest:
    version, content, size, foreground, background, error_level = payload
    if type(version) is not int or version != PROTOCOL_VERSION:
        raise QRCodeProtocolError("Unsupported QR JSON protocol version")
    return create_request(content, size, foreground, background, error_level)


def decode_provider_id(provider_id: Any) -> QRCodeRequest:
    """Strictly decode and canonicalize one image-provider identifier."""
    token = _validated_token(provider_id)
    request = _request_from_payload(_parsed_payload(_decoded_json(token)))
    if encode_provider_id(request) != provider_id:
        raise QRCodeProtocolError("QR provider id is not canonical")
    return request


__all__ = [
    "DEFAULT_SIZE",
    "IMAGE_SOURCE_PREFIX",
    "MAX_CACHE_BYTES",
    "MAX_CACHE_ENTRIES",
    "MAX_CONTENT_UTF8_BYTES",
    "MAX_JSON_BYTES",
    "MAX_PROVIDER_ID_CHARS",
    "MAX_SIZE",
    "MAX_TOKEN_CHARS",
    "MIN_SIZE",
    "PROTOCOL_PREFIX",
    "PROTOCOL_VERSION",
    "QUIET_ZONE_MODULES",
    "QRCodeProtocolError",
    "QRCodeRequest",
    "build_image_source",
    "create_request",
    "decode_provider_id",
    "encode_provider_id",
]
