"""Blind feasibility check of Amendment 4 section 7 (parent-configuration replication). Run once, at freezing time.

Prints only what section 7 allows: whether the preserved transcripts decompress to the recorded hashes,
and counts of parsed files, python snippets and `Current state` lines. It never counts or prints kept,
carried or retained-line quantities or levels reached.

Usage: python3 -I check_s7_format.py <third_party/franzen_m2_v3 dir>
"""
import gzip
import hashlib
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("analyze_reuse", os.path.join(HERE, "analyze_reuse.py"))
AR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AR)

root = sys.argv[1]
recorded = {}
for line in open(os.path.join(root, "MANIFEST_transcripts_events.sha256")):
    h, rel = line.split(None, 1)
    rel = rel.strip()
    if rel.startswith("transcripts/"):
        recorded[rel.split("/", 1)[1]] = h
files = sorted(f[:-3] for f in os.listdir(os.path.join(root, "transcripts")) if f.endswith(".txt.gz"))
hash_ok = parsed = with_both = 0
snippets_total = levels_total = 0
min_snip = min_lvl = None
for name in files:
    data = gzip.open(os.path.join(root, "transcripts", name + ".gz"), "rb").read()
    hash_ok += hashlib.sha256(data).hexdigest() == recorded.get(name)
    if not AR.FILE_NAME.search(name):
        continue
    parsed += 1
    text = data.decode("utf-8", errors="replace")
    n_snip = n_lvl = 0
    for m in AR.EVENTS.finditer(text):
        if m.group("level") is not None:
            n_lvl += 1
        elif m.group("code") is not None:
            n_snip += 1
    snippets_total += n_snip
    levels_total += n_lvl
    with_both += n_snip > 0 and n_lvl > 0
    min_snip = n_snip if min_snip is None else min(min_snip, n_snip)
    min_lvl = n_lvl if min_lvl is None else min(min_lvl, n_lvl)
print(f"transcript files {len(files)}; recorded hashes {len(recorded)}; decompressed to recorded hash {hash_ok}")
print(f"files matching the parser's file-name rule {parsed}; files with >=1 snippet and >=1 Current state line {with_both}")
print(f"python snippets {snippets_total} (fewest in a file {min_snip}); Current state lines {levels_total} (fewest in a file {min_lvl})")
print("format parses" if parsed == len(files) == with_both == hash_ok == len(recorded) else "FORMAT CHECK FAILED")
