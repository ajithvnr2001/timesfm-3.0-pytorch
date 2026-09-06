"""Merge ##BLOCK##/##RUN## lines captured from a Colab exec into the local ledger.

Usage:  python3 merge_stream.py pass.log      (override target with LEDGER=...)

Why this exists: free-tier Colab recycles the VM while the session name persists, so a ledger
written only to the VM disk can vanish. Both stages stream finished records to stdout; this
folds a captured log back into the authoritative local ledger. Idempotent - safe to re-run."""
import json, sys, os
import os
LED = os.environ.get("LEDGER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts/ledger.json"))
log = sys.argv[1]
led = json.load(open(LED))
nb = nr = 0
for line in open(log, errors="ignore"):
    line = line.strip()
    for tag, bucket, field in (("##BLOCK##", "llm_cache", "block"), ("##RUN##", "runs", "row")):
        if line.startswith(tag):
            try:
                obj = json.loads(line[len(tag):])
            except Exception:
                continue
            if obj["key"] not in led[bucket]:
                nb += (tag == "##BLOCK##"); nr += (tag == "##RUN##")
            led[bucket][obj["key"]] = obj[field]
tmp = LED + ".tmp"
json.dump(led, open(tmp, "w")); os.replace(tmp, LED)
import collections
c = collections.Counter(k.rsplit("|", 1)[1] for k in led["llm_cache"])
print(f"merged +{nb} blocks +{nr} runs | llm_cache={dict(c)} runs={len(led['runs'])}")
