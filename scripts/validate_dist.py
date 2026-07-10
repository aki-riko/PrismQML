# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Validate PrismQML wheel and sdist release artifacts. 验证发布制品。"""

import argparse
import glob
import logging
import re
import tarfile
import zipfile
from pathlib import Path
from typing import Optional


logger = logging.getLogger("prismqml.dist")
REQUIRED_SDIST_FILES = {
    "pyproject.toml",
    "rust/Cargo.toml",
    "rust/Cargo.lock",
    "rust/src/lib.rs",
    "rust/src/shard.rs",
}


def parse_args():
    """Parse artifact expectations. 解析制品预期。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+", help="Artifact paths or glob patterns")
    parser.add_argument("--expect-sdist", action="store_true")
    parser.add_argument("--expect-wheels", type=int)
    return parser.parse_args()


def expand_paths(patterns: list[str]) -> list[Path]:
    """Expand shell-independent glob patterns. 展开跨 shell 通配符。"""
    paths = []
    for pattern in patterns:
        matches = [Path(match) for match in glob.glob(pattern)]
        if not matches and Path(pattern).is_file():
            matches = [Path(pattern)]
        paths.extend(matches)
    return sorted(set(path.resolve() for path in paths))


def validate_counts(paths: list[Path], expect_sdist: bool, expect_wheels: Optional[int]):
    """Validate artifact counts. 验证制品数量。"""
    sdist_count = sum(path.name.endswith(".tar.gz") for path in paths)
    wheel_count = sum(path.suffix == ".whl" for path in paths)
    if expect_sdist and sdist_count != 1:
        raise ValueError(f"expected exactly 1 sdist, found {sdist_count}")
    if expect_wheels is not None and wheel_count != expect_wheels:
        raise ValueError(f"expected {expect_wheels} wheels, found {wheel_count}")


def validate_sdist(path: Path):
    """Validate source distribution contents. 验证源码包内容。"""
    with tarfile.open(path, "r:gz") as archive:
        names = set(archive.getnames())
    roots = {name.split("/", 1)[0] for name in names if name}
    if len(roots) != 1:
        raise ValueError(f"sdist must have one root directory, found {sorted(roots)}")
    root = next(iter(roots))
    missing = sorted(item for item in REQUIRED_SDIST_FILES if f"{root}/{item}" not in names)
    if missing:
        raise ValueError(f"sdist missing required files: {missing}")


def validate_wheel(path: Path):
    """Validate abi3 wheel tag and extension name. 验证 abi3 wheel。"""
    if "-cp39-abi3-" not in path.name:
        raise ValueError("wheel filename is not tagged cp39-abi3")
    with zipfile.ZipFile(path) as archive:
        basenames = [Path(name).name for name in archive.namelist()]
    extensions = [name for name in basenames if re.match(r"^prismqml_rs.*\.(?:pyd|so)$", name)]
    expected = "prismqml_rs.pyd" if "-win_" in path.name else "prismqml_rs.abi3.so"
    if extensions != [expected]:
        raise ValueError(f"expected extension {expected}, found {extensions}")
    if any(re.search(r"\.cp\d+", name) for name in extensions):
        raise ValueError(f"version-specific extension found: {extensions}")


def validate_path(path: Path):
    """Dispatch validation by artifact type. 按制品类型验证。"""
    if path.name.endswith(".tar.gz"):
        validate_sdist(path)
    elif path.suffix == ".whl":
        validate_wheel(path)
    else:
        raise ValueError(f"unsupported artifact type: {path.name}")
    logger.info("validated %s", path.name)


def main() -> int:
    """Run artifact validation. 执行制品验证。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    paths = expand_paths(args.patterns)
    if not paths:
        logger.error("no artifacts matched: %s", args.patterns)
        return 1
    try:
        validate_counts(paths, args.expect_sdist, args.expect_wheels)
        for path in paths:
            validate_path(path)
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as error:
        logger.error("artifact validation failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
