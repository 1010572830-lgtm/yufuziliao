#!/usr/bin/env python3
"""Run from any directory: python3 tools/verify_public_bundle.py."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bundle = json.loads((root / "data/public-materials.json").read_text(encoding="utf-8"))
index = json.loads((root / "data/source-index.json").read_text(encoding="utf-8"))
errors = []
paths = set()
for doc in bundle["documents"]:
    rel = doc["path"]
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        errors.append(f"Invalid path: {rel}")
        continue
    if rel in paths:
        errors.append(f"Duplicate document: {rel}")
    paths.add(rel)
    if not path.is_file():
        errors.append(f"Missing document: {rel}")
        continue
    raw = path.read_bytes()
    if raw.decode("utf-8") != doc["content_markdown"]:
        errors.append(f"Content mismatch: {rel}")
    sha = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if sha != doc["github_blob_sha"]:
        errors.append(f"Blob SHA mismatch: {rel}")
if paths != {p.relative_to(root).as_posix() for p in (root / "docs").glob("*.md")}:
    errors.append("Bundle/document file set mismatch")
for source in index["sources"]:
    if not source["url"].startswith(("http://", "https://")):
        errors.append("Invalid source URL")
    for rel in source["referenced_by"]:
        if rel not in paths:
            errors.append(f"Unknown source reference: {rel}")
        elif source["url"] not in (root / rel).read_text(encoding="utf-8"):
            errors.append(f"Source URL absent in document: {rel}")
if errors:
    raise SystemExit("\n".join(errors))
print(f"OK: {len(paths)} documents; {len(index['sources'])} indexed source URLs.")
print("Local consistency only; this does not verify external facts or live URLs.")
