# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Apply a manually authored Gallery translation draft. 应用人工编写的 Gallery 翻译稿。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N_ROOT = ROOT / "prismqml" / "PrismQML" / "i18n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("language")
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()

    source = json.loads((I18N_ROOT / "zh_CN.json").read_text(encoding="utf-8"))
    keys = [key for key in source if key.startswith("gallery_")]
    values: list[str] = []
    for expected, line in enumerate(args.draft.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        number, value = line.split("\t", 1)
        if int(number) != len(values) + 1:
            raise ValueError(
                f"draft sequence mismatch: expected {len(values) + 1}, got {number}"
            )
        values.append(value.replace("<NL>", "\n").replace("<SP>", " "))
    if len(values) != len(keys):
        raise ValueError(f"draft has {len(values)} values; expected {len(keys)}")

    path = I18N_ROOT / f"{args.language}.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog.update(dict(zip(keys, values, strict=True)))
    path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
