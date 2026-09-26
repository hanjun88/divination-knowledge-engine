# -*- coding: utf-8 -*-
"""
scripts/export_schema.py — 静态导出 FastAPI OpenAPI Schema
================================================================
将 engine.main.app 的运行时 /openapi.json 固化为仓库根目录的
openapi_schema.json 静态构建产物（供下游 Consumer 校验与客户端生成）。

用法:
    python scripts/export_schema.py            # 写出 openapi_schema.json 并打印 SHA256
    python scripts/export_schema.py --stdout  # 仅打印 schema JSON 到 stdout

产物: <repo_root>/openapi_schema.json
注入: info.version 强制为 "1.0.0"
序列化: sort_keys + indent=2 + ensure_ascii=False，保证 SHA256 可复现。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
# engine.main 需要 repo_root 在 sys.path（包导入），engine/ 目录在 sys.path
# （main.py 内部 `from rule_engine import ...` 为扁平导入）。
for _p in (str(REPO_ROOT), str(REPO_ROOT / "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine.main import app  # noqa: E402  (path 已在上方注入)

SCHEMA_FILENAME = "openapi_schema.json"
SCHEMA_VERSION = "1.0.0"
CANONICAL_INDENT = 2


def build_openapi_spec() -> dict:
    """构造 OpenAPI 文档 dict，强制 info.version = SCHEMA_VERSION。"""
    spec = app.openapi()
    spec.setdefault("info", {})
    spec["info"]["version"] = SCHEMA_VERSION
    return spec


def dump_canonical_bytes(spec: dict) -> bytes:
    """稳定序列化：sort_keys 保证哈希可复现。"""
    return (
        json.dumps(spec, ensure_ascii=False, indent=CANONICAL_INDENT, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export_schema(out_path: Path | None = None) -> tuple[Path, str]:
    """写出 openapi_schema.json，返回 (路径, sha256)。"""
    spec = build_openapi_spec()
    payload = dump_canonical_bytes(spec)
    digest = sha256_hex(payload)
    target = out_path or (REPO_ROOT / SCHEMA_FILENAME)
    target.write_bytes(payload)
    return target, digest


def main() -> int:
    if "--stdout" in sys.argv:
        json.dump(build_openapi_spec(), sys.stdout,
                  ensure_ascii=False, indent=CANONICAL_INDENT, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    path, digest = export_schema()
    spec = build_openapi_spec()
    print(f"[export_schema] wrote {path.relative_to(REPO_ROOT)} "
          f"({path.stat().st_size} bytes)")
    print(f"[export_schema] info.version = {spec['info']['version']}")
    print(f"[export_schema] openapi = {spec.get('openapi')}")
    print(f"[export_schema] paths = {sorted(spec.get('paths', {}).keys())}")
    print(f"[export_schema] sha256 = {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
