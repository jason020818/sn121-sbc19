"""Candidate markdown vs policy manifest alignment and archive safety."""

import hashlib

from eval_lab.candidate_store import read_candidate, sha256_text
from eval_lab.config import repo_root
from eval_lab.policy_lint import lint_candidate_policy
from eval_lab.policy_manifests import load_policy

PRODUCTION_SHA = "e6cd5a14bf8734d36474b02f81d5baf41e4a1a18a348867f19d2916bac786fa3"


def test_production_skill_sha_unchanged() -> None:
    text = (repo_root() / "SKILL.md").read_bytes()
    assert hashlib.sha256(text).hexdigest() == PRODUCTION_SHA


def test_all_candidates_align_with_policies() -> None:
    names = [
        "production-f9e5400",
        "candidate-a-conservative",
        "candidate-b-ledger",
        "candidate-b-minimal",
        "candidate-c-assertive",
        "candidate-c-minimal",
    ]
    for name in names:
        _path, text, _digest = read_candidate(name)
        result = lint_candidate_policy(text, load_policy(name))
        assert result["passed"], (name, result)
        assert result["contradictions"] == []
        assert "S-001" not in text


def test_results_archive_untouched() -> None:
    root = repo_root() / "results"
    assert root.is_dir()
    marker = root / ".oracle-lab-should-not-exist"
    assert not marker.exists()


def test_candidate_bytes_match_registered_sha() -> None:
    _path, text, digest = read_candidate("candidate-a-conservative")
    assert digest == sha256_text(text)
    assert digest == hashlib.sha256(text.encode("utf-8")).hexdigest()
