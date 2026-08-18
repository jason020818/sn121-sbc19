"""Store candidate skill markdown files outside production SKILL.md."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from eval_lab.config import lab_root, repo_root
from eval_lab.models import CandidateManifestEntry

PRODUCTION_SKILL_NAME = "SKILL.md"


class CandidateStoreError(RuntimeError):
    pass


def candidates_dir() -> Path:
    path = lab_root() / "candidates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path() -> Path:
    return candidates_dir() / "manifest.json"


def sha256_text(text: str | bytes) -> str:
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict[str, CandidateManifestEntry]:
    path = manifest_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("candidates", raw) if isinstance(raw, dict) else raw
    if isinstance(entries, dict):
        iterable = entries.values()
    else:
        iterable = entries
    out: dict[str, CandidateManifestEntry] = {}
    for item in iterable:
        entry = CandidateManifestEntry.model_validate(item)
        out[entry.name] = entry
    return out


def save_manifest(entries: dict[str, CandidateManifestEntry]) -> None:
    payload = {
        "candidates": [entry.model_dump() for entry in sorted(entries.values(), key=lambda e: e.name)]
    }
    manifest_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def candidate_path(name: str) -> Path:
    safe = _validate_name(name)
    return candidates_dir() / f"{safe}.md"


def _validate_name(name: str) -> str:
    cleaned = name.strip().replace(" ", "-")
    if not cleaned or any(ch in cleaned for ch in r"/\\:"):
        raise CandidateStoreError(f"Invalid candidate name: {name!r}")
    if cleaned.lower() in {PRODUCTION_SKILL_NAME.lower(), "skill.md"}:
        raise CandidateStoreError("Refusing to treat production SKILL.md as a candidate filename")
    return cleaned


def add_candidate(name: str, source: Path, force: bool = False) -> CandidateManifestEntry:
    src = Path(source)
    if not src.exists():
        raise CandidateStoreError(f"Source skill file not found: {src}")
    dest = candidate_path(name)
    production = repo_root() / PRODUCTION_SKILL_NAME
    if dest.resolve() == production.resolve():
        raise CandidateStoreError("Refusing to overwrite production SKILL.md")
    if dest.exists() and not force:
        raise CandidateStoreError(f"Candidate {name} already exists at {dest}. Pass --force to overwrite.")
    text = src.read_text(encoding="utf-8")
    dest.write_text(text, encoding="utf-8")
    entry = CandidateManifestEntry(
        name=_validate_name(name),
        path=str(dest.relative_to(lab_root())),
        sha256=sha256_text(text),
        added_at=datetime.now(timezone.utc).isoformat(),
        source_file=str(src),
        bytes=len(text.encode("utf-8")),
    )
    entries = load_manifest()
    entries[entry.name] = entry
    save_manifest(entries)
    return entry


def list_candidates() -> list[CandidateManifestEntry]:
    return sorted(load_manifest().values(), key=lambda e: e.name)


def resolve_candidate(name_or_path: str) -> Path:
    direct = Path(name_or_path)
    if direct.exists() and direct.is_file():
        production = repo_root() / PRODUCTION_SKILL_NAME
        if direct.resolve() == production.resolve():
            raise CandidateStoreError(
                "Pass a candidate copy, not production SKILL.md. "
                "Use `candidate add` first."
            )
        return direct.resolve()
    named = candidate_path(name_or_path)
    if named.exists():
        return named
    if not name_or_path.endswith(".md"):
        alt = candidate_path(name_or_path)
        if alt.exists():
            return alt
    raise CandidateStoreError(f"Unknown candidate: {name_or_path}")


def read_candidate(name_or_path: str) -> tuple[Path, str, str]:
    path = resolve_candidate(name_or_path)
    text = path.read_text(encoding="utf-8")
    return path, text, sha256_text(text)
