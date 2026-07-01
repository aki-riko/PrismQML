#!/usr/bin/env python3
# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QR 端到端验证: 用 opencv 解码 C++ (prism_test_qrcode_gen) 生成的 QR PNG,
断言解出内容 == 原文。用法: python verify_qr.py <生成目录>"""
import sys
from pathlib import Path

import cv2  # opencv-python(-headless): 自带 QRCodeDetector

# 性能/诊断测试, 允许 print (脚本非 prismqml 运行时代码)


def decode(png_path: Path) -> str:
    """opencv 解码单张二维码, 返回解出的文本(失败返回空串)"""
    img = cv2.imread(str(png_path))
    if img is None:
        return ""
    detector = cv2.QRCodeDetector()
    # detectAndDecode 对中文 UTF-8 字节流解出 latin-1 编码, 需重解
    data, points, _ = detector.detectAndDecode(img)
    return data


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: verify_qr.py <生成目录>")
        return 2
    out_dir = Path(sys.argv[1])
    manifest = out_dir / "manifest.tsv"
    if not manifest.exists():
        print(f"FAIL: 找不到 manifest {manifest}")
        return 3

    total = 0
    failed = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fname, expected = line.split("\t", 1)
        total += 1
        png = out_dir / fname
        decoded = decode(png)
        # opencv 对非 ASCII 常解成 UTF-8 字节被当 latin-1, 尝试还原
        ok = decoded == expected
        if not ok and decoded:
            try:
                fixed = decoded.encode("latin-1").decode("utf-8")
                ok = fixed == expected
                if ok:
                    decoded = fixed
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        if ok:
            print(f"  PASS: {fname}  <- {expected[:40]!r}")
        else:
            failed += 1
            print(f"  FAIL: {fname}\n     期望: {expected!r}\n     解出: {decoded!r}")

    print(f"QR_VERIFY: total={total} passed={total - failed} failed={failed}")
    return 0 if failed == 0 and total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
