#!/usr/bin/env python3
"""Rubric library tree — FULL library-half data, organized, zero compression.

Structure: no per-domain cap, no dedup/selection; the
directory tree is the scale answer. The agent navigates it like a filesystem
(cat README -> grep -> read the hit), so the library holds EVERY library-half
criterion, grouped by the bench's official criteria categories:

    rubric/<domain>/README.md        category index (counts + file names)
    rubric/<domain>/INDEX.tsv        one line per entry (id, severity, category,
                                     task, topic, sentence) — the grep surface
    rubric/<domain>/<cat-slug>.md    every entry of one category, full text

Entries carry raw provenance (source task + topic); severity uses the frozen
three-level mapping from ingest. Judge-time evidence surface is the FAMILY
vocabulary, stated once in the README — no invented per-entry binding.
IDs are deterministic: sorted by (category, task_id, seed_id) -> FIN-0001…
"""
from __future__ import annotations

import os
import re
import csv
import hashlib
import json
import tempfile
from collections import Counter
from dataclasses import dataclass

SEVERITIES = ("必须", "建议", "负面")
PREFIX = {"finance": "FIN", "legal": "LEG", "medicine": "MED",
          "finance_hard": "FINH", "legal_hard": "LEGH",
          "banking_ops": "BNK", "airline_ops": "AIR"}


def slug(category: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
    return s or "misc"


@dataclass
class Entry:
    id: str                      # FIN-0001
    domain: str
    category: str                # official criteria_category, verbatim
    severity: str                # 必须 | 建议 | 负面
    sentence: str                # the criterion, verbatim from the bench
    hint: str                    # criteria_description, verbatim
    task_id: str                 # source library-half task
    topic: str
    library_version: str | None = None   # populated when loading a versioned tree

    @property
    def reference(self) -> str:
        """A positional id is meaningful only within this exact library version."""
        if self.library_version is None:
            raise ValueError("entry is not bound to a loaded library version")
        return f"{self.domain}@{self.library_version}:{self.id}"

    def render(self) -> str:
        h = " ".join(self.hint.split())
        s = " ".join(self.sentence.split())
        return (f"## {self.id} [{self.severity}]\n"
                f"判据: {s}\n"
                + (f"提示: {h}\n" if h else "")
                + f"出处: {self.task_id} | 话题: {' '.join(self.topic.split())}\n")

    def validate(self) -> list[str]:
        errs = []
        if not re.fullmatch(r"[A-Z]{2,4}-\d{4,}", self.id):
            errs.append(f"{self.id}: id 不合规")
        if self.severity not in SEVERITIES:
            errs.append(f"{self.id}: 严重度 {self.severity!r} 不在三档内")
        if not self.sentence.strip():
            errs.append(f"{self.id}: 判据为空")
        if not self.task_id:
            errs.append(f"{self.id}: 缺出处")
        for name in ("category", "task_id"):
            value = getattr(self, name)
            if not value or any(c in value for c in "\t\r\n"):
                errs.append(f"{self.id}: {name} must be a non-empty single-line field")
        return errs


def entries_from_tasks(domain: str, tasks: list[dict]) -> list[Entry]:
    """flatten ingest.load_prbench task dicts -> deterministic id-stamped entries."""
    rows = []
    for t in tasks:
        for c in t["criteria"]:
            rows.append((c["category"], t["task_id"], c["seed_id"], c, t))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    out = []
    for i, (cat, tid, _sid, c, t) in enumerate(rows, 1):
        out.append(Entry(id=f"{PREFIX[domain]}-{i:04d}", domain=domain, category=cat,
                         severity=c["severity"], sentence=c["sentence"], hint=c["hint"],
                         task_id=tid, topic=t["topic"]))
    return out


def write_domain(root: str, domain: str, entries: list[Entry],
                 evidence_vocab: dict[str, str]) -> list[str]:
    """Validate a complete replacement tree before publishing it.

    Colliding category slugs are rejected before touching the destination. A
    successful rebuild replaces the generated domain directory, so old category
    files cannot survive. Existing committed libraries are never rewritten by load.
    """
    errs = [e for en in entries for e in en.validate()]
    ids = [e.id for e in entries]
    errs += [f"{domain}: 条目号重复 {i}" for i, count in Counter(ids).items() if count > 1]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", domain):
        errs.append("invalid domain directory name")
    errs += [f"{e.id}: entry domain differs from {domain}" for e in entries if e.domain != domain]
    by_slug = {}
    for category in sorted({e.category for e in entries}):
        filename = slug(category) + ".md"
        if filename in by_slug:
            errs.append(f"category slug collision: {by_slug[filename]!r} and {category!r} -> {filename}")
        by_slug[filename] = category
    if errs:
        return errs
    os.makedirs(root, exist_ok=True)
    destination = os.path.join(root, domain)
    if os.path.islink(destination):
        return ["refusing to replace a symlinked domain directory"]
    with tempfile.TemporaryDirectory(prefix=f".{domain}-build-", dir=root) as staging:
        d = os.path.join(staging, domain)
        os.mkdir(d)
        _write_tree(d, domain, entries, evidence_vocab)
        load_domain(staging, domain)       # verify INDEX, full text, and file hashes
        backup = os.path.join(staging, "previous")
        had_previous = os.path.exists(destination)
        if had_previous:
            os.replace(destination, backup)
        try:
            os.replace(d, destination)
        except BaseException:
            if had_previous:
                os.replace(backup, destination)
            raise
    return []


def _write_tree(d: str, domain: str, entries: list[Entry], evidence_vocab: dict) -> None:
    by_cat: dict[str, list[Entry]] = {}
    for e in entries:
        by_cat.setdefault(e.category, []).append(e)

    with open(os.path.join(d, "INDEX.tsv"), "w") as fh:
        fh.write("id\tseverity\tcategory\ttask\ttopic\tsentence\n")
        for e in entries:
            fh.write(f"{e.id}\t{e.severity}\t{e.category}\t{e.task_id}\t"
                     f"{' '.join(e.topic.split())}\t{' '.join(e.sentence.split())}\n")

    for cat, es in sorted(by_cat.items()):
        with open(os.path.join(d, f"{slug(cat)}.md"), "w") as fh:
            fh.write(f"# {domain} / {cat}({len(es)} 条)\n\n")
            for e in es:
                fh.write(e.render() + "\n")

    with open(os.path.join(d, "README.md"), "w") as fh:
        fh.write(f"# {domain} 判据库({len(entries)} 条,全量,零压缩)\n\n"
                 f"用法:先看本索引挑类目 -> grep INDEX.tsv 找关键词 -> 打开类目文件精读。\n"
                 f"判定时证据面(全库统一): "
                 + ", ".join(f"{k}({v})" for k, v in sorted(evidence_vocab.items())) + "\n\n")
        for cat, es in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
            sev = {s: sum(1 for e in es if e.severity == s) for s in SEVERITIES}
            fh.write(f"- {slug(cat)}.md — {cat}: {len(es)} 条 "
                     f"(必须 {sev['必须']} / 建议 {sev['建议']} / 负面 {sev['负面']})\n")
    # Version binds positional ids to all serialized content, including the index,
    # full hints, and evidence vocabulary. It is stable for identical rebuilds.
    files = _tree_hashes(d)
    version = _version(files)
    with open(os.path.join(d, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump({"schema": "veritas/rubric-library/1", "domain": domain,
                   "version": version, "entry_ids": [e.id for e in entries],
                   "files": files}, fh, ensure_ascii=False, sort_keys=True, indent=1)


def _tree_hashes(directory: str) -> dict[str, str]:
    hashes = {}
    for filename in sorted(os.listdir(directory)):
        if filename == "INDEX.tsv" or filename.endswith(".md"):
            path = os.path.join(directory, filename)
            if os.path.islink(path) or not os.path.isfile(path):
                raise ValueError(f"library source is not a regular file: {filename}")
            with open(path, "rb") as fh:
                hashes[filename] = hashlib.sha256(fh.read()).hexdigest()
    return hashes


def _version(files: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(files, sort_keys=True,
                                                 separators=(",", ":")).encode()).hexdigest()


def load_domain(root: str, domain: str) -> list[Entry]:
    """Validate and parse a tree; old trees get a read-only content version.

    INDEX is authoritative. Missing/extra/duplicate entries, malformed Markdown,
    changed versioned files, or disagreement with indexed metadata fail explicitly.
    """
    d = os.path.join(root, domain)
    with open(os.path.join(d, "INDEX.tsv"), encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        expected_fields = ["id", "severity", "category", "task", "topic", "sentence"]
        if reader.fieldnames != expected_fields:
            raise ValueError(f"{domain}: invalid INDEX.tsv header")
        index = list(reader)
    if any(set(row) != set(expected_fields) or any(value is None for value in row.values())
           for row in index):
        raise ValueError(f"{domain}: malformed INDEX.tsv row")
    indexed_ids = [row["id"] for row in index]
    if len(set(indexed_ids)) != len(indexed_ids):
        raise ValueError(f"{domain}: duplicate ids in INDEX.tsv")
    hashes = _tree_hashes(d)
    version = _version(hashes)
    manifest_path = os.path.join(d, "MANIFEST.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
        if not isinstance(manifest, dict) or manifest.get("schema") != "veritas/rubric-library/1" \
                or manifest.get("domain") != domain or manifest.get("files") != hashes \
                or manifest.get("version") != version or manifest.get("entry_ids") != indexed_ids:
            raise ValueError(f"{domain}: library manifest/content mismatch")
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".md") or f == "README.md":
            continue
        with open(os.path.join(d, f), encoding="utf-8") as fh:
            text = fh.read()
        header = re.search(r"^# " + re.escape(domain) + r" / (.*)\((\d+) 条\)$", text, re.M)
        if not header:
            raise ValueError(f"{domain}/{f}: malformed category header")
        cat = header.group(1)
        matches = list(re.finditer(
                r"^## ([A-Z]{2,4}-\d{4,}) \[(.+?)\]\n判据: (.*)\n(?:提示: (.*)\n)?"
                r"出处: (.*?) \| 话题: (.*)$", text, re.M))
        if len(matches) != int(header.group(2)) or len(matches) != len(re.findall(r"^## ", text, re.M)):
            raise ValueError(f"{domain}/{f}: malformed or missing category entries")
        for m in matches:
            out.append(Entry(id=m.group(1), domain=domain, category=cat,
                             severity=m.group(2), sentence=m.group(3),
                             hint=m.group(4) or "", task_id=m.group(5),
                             topic=m.group(6), library_version=version))
    by_id = {e.id: e for e in out}
    if len(by_id) != len(out) or set(by_id) != set(indexed_ids):
        raise ValueError(f"{domain}: INDEX/full-text id mismatch or duplicates")
    for row in index:
        entry = by_id[row["id"]]
        full = {"id": entry.id, "severity": entry.severity, "category": entry.category,
                "task": entry.task_id, "topic": entry.topic, "sentence": entry.sentence}
        if full != row or entry.validate():
            raise ValueError(f"{domain}: invalid/inconsistent indexed entry {entry.id}")
    return [by_id[entry_id] for entry_id in indexed_ids]


def _selftest():
    import tempfile
    vocab = {"conversation": "process.language", "final_response": "final.artifact"}
    tasks = [
        {"task_id": "T2", "domain": "finance", "topic": "费用",
         "criteria": [{"seed_id": "s1", "sentence": "说明A基金费率为1.5%",
                       "hint": "看最终回复", "category": "Financial Accuracy",
                       "severity": "必须"}]},
        {"task_id": "T1", "domain": "finance", "topic": "风险",
         "criteria": [{"seed_id": "s2", "sentence": "严禁承诺保本",
                       "hint": "", "category": "Risk & Regulatory Disclosure",
                       "severity": "负面"},
                      {"seed_id": "s3", "sentence": "给出风险等级",
                       "hint": "x", "category": "Financial Accuracy",
                       "severity": "建议"}]},
    ]
    es = entries_from_tasks("finance", tasks)
    # deterministic ids: sorted by (category, task, seed) — T1/s3 before T2/s1
    assert [e.id for e in es] == ["FIN-0001", "FIN-0002", "FIN-0003"]
    assert es[0].task_id == "T1" and es[0].category == "Financial Accuracy"
    assert all(e.validate() == [] for e in es)
    with tempfile.TemporaryDirectory() as d:
        assert write_domain(d, "finance", es, vocab) == []
        got = load_domain(d, "finance")
        assert {e.id for e in got} == {e.id for e in es}
        g0 = {e.id: e for e in got}
        assert g0["FIN-0002"].sentence == "说明A基金费率为1.5%"
        assert g0["FIN-0003"].hint == ""            # hint-less entry round-trips
        idx = open(os.path.join(d, "finance", "INDEX.tsv")).read().splitlines()
        assert len(idx) == 4 and idx[1].startswith("FIN-0001\t")
        rd = open(os.path.join(d, "finance", "README.md")).read()
        assert "3 条" in rd and "financial-accuracy.md" in rd
    bad = entries_from_tasks("finance", tasks[:1])
    bad[0].severity = "重要"
    assert write_domain("/nonexistent-never-written", "finance", bad, vocab)
    print("library selftest OK")


if __name__ == "__main__":
    _selftest()
