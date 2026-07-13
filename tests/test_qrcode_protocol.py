# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Strict QR image-provider protocol regressions. 二维码图片协议严格回归。"""

import base64
import json

import pytest

from prismqml.python.providers._qrcode_protocol import (
    IMAGE_SOURCE_PREFIX,
    MAX_PROVIDER_ID_CHARS,
    MAX_TOKEN_CHARS,
    QRCodeProtocolError,
    QRCodeRequest,
    build_image_source,
    create_request,
    decode_provider_id,
    encode_provider_id,
)


GOLDEN_URL = (
    "image://qrcode/"
    "v1.WzEsIkhFTExPIiwxMjAsIiMxMTIyMzMiLCIjNDQ1NTY2IiwiSCJd"
)


def _encode_raw(raw: bytes) -> str:
    token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return f"v1.{token}"


def _encode_payload(payload, *, compact: bool = True) -> str:
    separators = (",", ":") if compact else None
    raw = json.dumps(payload, ensure_ascii=False, separators=separators).encode("utf-8")
    return _encode_raw(raw)


def test_qrcode_protocol_golden_vector_and_color_normalization():
    assert build_image_source("HELLO", 120, "#112233", "#445566", "H") == GOLDEN_URL
    request = create_request("X", 32, "#AABBCC", "white", "l")
    assert request == QRCodeRequest("X", 32, "#aabbcc", "#ffffff", "L")
    assert encode_provider_id(request) == (
        "v1.WzEsIlgiLDMyLCIjYWFiYmNjIiwiI2ZmZmZmZiIsIkwiXQ"
    )


@pytest.mark.parametrize(
    "content",
    [
        "你好，PrismQML 🌈 / QR",
        'A|#%?/&=+"\\\nB',
        "\tline one\r\nline two",
        "😀" * 256,
        "\x01" * 1024,
    ],
)
def test_qrcode_protocol_round_trips_reserved_and_unicode_content(content):
    request = create_request(content, 120, "#112233", "#445566", "H")
    provider_id = encode_provider_id(request)
    assert len(provider_id) <= MAX_PROVIDER_ID_CHARS
    assert decode_provider_id(provider_id) == request


def test_qrcode_protocol_worst_case_token_is_within_the_contract():
    provider_id = encode_provider_id(
        create_request("\x01" * 1024, 1024, "#112233", "#445566", "H")
    )
    assert len(provider_id.removeprefix("v1.")) == MAX_TOKEN_CHARS


@pytest.mark.parametrize(
    "args",
    [
        ("", 120, "#000000", "#ffffff", "M"),
        ("A\x00B", 120, "#000000", "#ffffff", "M"),
        ("\ud800", 120, "#000000", "#ffffff", "M"),
        ("a" * 1025, 120, "#000000", "#ffffff", "M"),
        ("😀" * 257, 120, "#000000", "#ffffff", "M"),
        ("A", True, "#000000", "#ffffff", "M"),
        ("A", 31, "#000000", "#ffffff", "M"),
        ("A", 1025, "#000000", "#ffffff", "M"),
        ("A", 120, "invalid", "#ffffff", "M"),
        ("A", 120, "#80000000", "#ffffff", "M"),
        ("A", 120, "#ffffff", "white", "M"),
        ("A", 120, "#000000", "#ffffff", "X"),
    ],
)
def test_qrcode_protocol_rejects_invalid_producer_input(args):
    with pytest.raises(QRCodeProtocolError):
        create_request(*args)
    assert build_image_source(*args) == ""


@pytest.mark.parametrize(
    "provider_id",
    [
        "",
        "HELLO|120|#112233|#445566|H",
        "v1.",
        "v2.AA",
        "v1.A",
        "v1.AA==",
        "v1.A+B",
        "v1.A/B",
        "v1.A%2FB",
        "v1.A?B",
        "v1.A#B",
        "v1.A/B/C",
        "v1." + "A" * (MAX_TOKEN_CHARS + 1),
        _encode_raw(b"\xff"),
        _encode_raw(b"\xef\xbb\xbf[1,\"A\",120,\"#000000\",\"#ffffff\",\"M\"]"),
        _encode_raw(b"not-json"),
    ],
)
def test_qrcode_protocol_rejects_invalid_envelopes(provider_id):
    with pytest.raises(QRCodeProtocolError):
        decode_provider_id(provider_id)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        [],
        [1, "A", 120, "#000000", "#ffffff"],
        [1, "A", 120, "#000000", "#ffffff", "M", "extra"],
        [True, "A", 120, "#000000", "#ffffff", "M"],
        [2, "A", 120, "#000000", "#ffffff", "M"],
        [1, True, 120, "#000000", "#ffffff", "M"],
        [1, "A", True, "#000000", "#ffffff", "M"],
        [1, "A", 120.0, "#000000", "#ffffff", "M"],
        [1, "A", 31, "#000000", "#ffffff", "M"],
        [1, "A", 1025, "#000000", "#ffffff", "M"],
        [1, "A", 120, "#ABC", "#ffffff", "M"],
        [1, "A", 120, "#000000", "#FFFFFF", "M"],
        [1, "A", 120, "#000000", "#ffffff", "m"],
        [1, "A", 120, "#000000", "#ffffff", "MM"],
    ],
)
def test_qrcode_protocol_rejects_noncanonical_or_invalid_payloads(payload):
    with pytest.raises(QRCodeProtocolError):
        decode_provider_id(_encode_payload(payload))


def test_qrcode_protocol_rejects_noncanonical_json_spelling():
    payload = [1, "A", 120, "#000000", "#ffffff", "M"]
    with pytest.raises(QRCodeProtocolError):
        decode_provider_id(_encode_payload(payload, compact=False))
    escaped = b'[1,"\\u0041",120,"#000000","#ffffff","M"]'
    with pytest.raises(QRCodeProtocolError):
        decode_provider_id(_encode_raw(escaped))


def test_qrcode_protocol_rejects_deep_json_without_recursion_escape():
    deeply_nested = b"[" * 3000 + b"0" + b"]" * 3000
    provider_id = _encode_raw(deeply_nested)
    assert len(provider_id) <= MAX_PROVIDER_ID_CHARS
    with pytest.raises(QRCodeProtocolError):
        decode_provider_id(provider_id)


def test_qrcode_image_source_prefix_is_not_part_of_the_provider_id():
    source = build_image_source("A", 128, "#000000", "#ffffff", "M")
    assert source.startswith(IMAGE_SOURCE_PREFIX)
    assert decode_provider_id(source.removeprefix(IMAGE_SOURCE_PREFIX)).content == "A"
