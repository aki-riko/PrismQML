# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Validate Gallery catalog completeness. 校验 Gallery 翻译目录完整性。"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Sequence

try:
    from .gallery_i18n import I18N_ROOT, SOURCE_LANGUAGE, referenced_keys
except ImportError:
    from gallery_i18n import I18N_ROOT, SOURCE_LANGUAGE, referenced_keys

logger = logging.getLogger("prismqml.generate_gallery_catalogs")


def source_catalog() -> dict[str, str]:
    source = json.loads(
        (I18N_ROOT / f"{SOURCE_LANGUAGE}.json").read_text(encoding="utf-8")
    )
    keys = referenced_keys()
    missing = sorted(key for key in keys if not source.get(key, "").strip())
    if missing:
        raise ValueError(f"source catalog missing Gallery keys: {missing}")
    return {key: source[key] for key in sorted(keys)}


def generate(check: bool = False) -> None:
    source = source_catalog()
    for path in sorted(I18N_ROOT.glob("*.json")):
        catalog = json.loads(path.read_text(encoding="utf-8"))
        missing = sorted(key for key in source if not catalog.get(key, "").strip())
        if missing:
            raise ValueError(f"incomplete Gallery catalog {path.stem}: {missing}")
        if check:
            rendered = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
            if path.read_text(encoding="utf-8") != rendered:
                raise ValueError(f"stale Gallery catalog: {path}")
        logger.info("%s: %s entries", path.stem, len(catalog))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        generate(parse_args(argv).check)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Gallery catalog validation failed: %s", exc)
        return 1
    except Exception:
        logger.exception("unexpected Gallery catalog validation failure")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
