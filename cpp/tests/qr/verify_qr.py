# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Decode PNG files produced by the real C++ QML QR chain."""

import json
import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_PROCESS = runpy.run_path(str(REPO_ROOT / "scripts" / "test_process.py"))
prepare_automated_test_process = TEST_PROCESS["prepare_automated_test_process"]

prepare_automated_test_process()

import cv2


def print_safe(message: str) -> None:
    """Print diagnostic text using the current console encoding."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    safe_message = message.encode(encoding, errors="backslashreplace").decode(encoding)
    print(safe_message)


def decode(png_path: Path) -> str:
    """Decode one QR PNG, returning an empty string on detector failure."""
    image = cv2.imread(str(png_path))
    if image is None:
        return ""
    decoded, _points, _ = cv2.QRCodeDetector().detectAndDecode(image)
    return decoded


def _load_manifest(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("QR manifest must be a list")
    for item in payload:
        if (
            not isinstance(item, dict)
            or set(item) != {"file", "content"}
            or not isinstance(item["file"], str)
            or not isinstance(item["content"], str)
        ):
            raise ValueError("QR manifest contains an invalid case")
    return payload


def main() -> int:
    if len(sys.argv) != 2:
        print_safe("Usage: verify_qr.py <generated-directory>")
        return 2
    output_directory = Path(sys.argv[1])
    manifest_path = output_directory / "manifest.json"
    if not manifest_path.is_file():
        print_safe(f"FAIL: manifest not found: {manifest_path}")
        return 3

    try:
        cases = _load_manifest(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print_safe(f"FAIL: invalid manifest: {type(exc).__name__}: {exc}")
        return 4

    failures = 0
    for case in cases:
        decoded = decode(output_directory / case["file"])
        if decoded == case["content"]:
            print_safe(f"PASS: {case['file']} <- {case['content'][:40]!r}")
        else:
            failures += 1
            print_safe(
                f"FAIL: {case['file']} expected={case['content']!r} decoded={decoded!r}"
            )
    print_safe(
        f"QR_VERIFY: total={len(cases)} passed={len(cases) - failures} "
        f"failed={failures}"
    )
    return 0 if cases and failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
