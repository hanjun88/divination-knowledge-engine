# -*- coding: utf-8 -*-
"""
scripts/generate_manifest.py — 生成 engine/rules_manifest.json（注入溯源字段）
=============================================================================
在既有 rules_manifest.json（manifest_version / repository / generated_at /
rules）之上，注入四个全局溯源字段：

  - provider_commit           当前引擎代码 Git SHA（git rev-parse HEAD）
  - schema_version           显式声明 "1.0.0"
  - schema_sha256            仓库根 openapi_schema.json 的 SHA256
  - canonical_manifest_sha   本清单（不含自身字段）规范化内容的 SHA256
                             （自引用约定：先序列化不含该字段的 body ->
                              求哈希 -> 写回该字段）

规则数据（liuyao 82 + ziwei 64 + bazi 60）保持不变。

用法:
    python scripts/generate_manifest.py              # 先导出 schema 再生成 manifest
    python scripts/generate_manifest.py --no-export  # 复用已有 openapi_schema.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.export_schema import (  # noqa: E402
    SCHEMA_FILENAME,
    SCHEMA_VERSION,
    dump_canonical_bytes,
    export_schema,
)

MANIFEST_REL = Path("engine") / "rules_manifest.json"
# 既有字段（原样保留）；新增溯源字段在下方注入。
PRESERVED_FIELDS = ("manifest_version", "repository", "generated_at", "rules")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def load_existing_manifest() -> dict[str, Any]:
    path = REPO_ROOT / MANIFEST_REL
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest_body(schema_path: Path) -> dict[str, Any]:
    existing = load_existing_manifest()
    body: dict[str, Any] = {}
    # 1) 原样保留既有字段（rules 数据不动）
    for k in PRESERVED_FIELDS:
        if k in existing:
            body[k] = existing[k]
    # 2) 注入全局溯源字段
    body["schema_version"] = SCHEMA_VERSION
    body["provider_commit"] = git_commit()
    body["schema_file"] = SCHEMA_FILENAME
    body["schema_sha256"] = sha256_hex(schema_path.read_bytes())
    return body


def generate_manifest(export: bool = True) -> tuple[Path, str]:
    """导出 schema（可选），生成 rules_manifest.json 并回写 canonical_manifest_sha。"""
    if export:
        export_schema()
    schema_path = REPO_ROOT / SCHEMA_FILENAME
    if not schema_path.exists():
        raise FileNotFoundError(
            f"{SCHEMA_FILENAME} 不存在；请先运行 scripts/export_schema.py 或去掉 --no-export"
        )

    body = build_manifest_body(schema_path)
    # 自引用哈希：先对不含 canonical_manifest_sha 的 body 求摘要
    digest = sha256_hex(dump_canonical_bytes(body))
    body["canonical_manifest_sha"] = digest

    target = REPO_ROOT / MANIFEST_REL
    target.write_bytes(dump_canonical_bytes(body))
    return target, digest


def main() -> int:
    do_export = "--no-export" not in sys.argv
    path, digest = generate_manifest(export=do_export)
    m = json.loads(path.read_text(encoding="utf-8"))
    print(f"[generate_manifest] wrote {path.relative_to(REPO_ROOT)} "
          f"({path.stat().st_size} bytes)")
    print(f"[generate_manifest] provider_commit        = {m['provider_commit']}")
    print(f"[generate_manifest] schema_version         = {m['schema_version']}")
    print(f"[generate_manifest] schema_sha256          = {m['schema_sha256']}")
    print(f"[generate_manifest] canonical_manifest_sha = {m['canonical_manifest_sha']}")
    print(f"[generate_manifest] rule domains           = "
          f"{[r.get('domain') for r in m.get('rules', [])]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
