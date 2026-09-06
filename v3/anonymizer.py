"""
anonymizer.py
=============
Entity/date anonymisation for the LLM layer, plus an adversarial identity probe.

The problem this solves: an LLM asked about "INFY.NS as of 2024-06-28" answers using its
pretraining memory of what actually happened after that date. Locking the *retrieved*
evidence to the cutoff is not enough - the model itself is a leak. So for every backtest
run the LLM receives:

  * no ticker, no company name, no exchange, no index names
  * no absolute dates - only relative period tokens (T, T-1, ...)
  * numeric fundamentals expressed as unit-free ratios
  * evidence snippets scrubbed of proper nouns and future-year tokens

and then a second, independent LLM call is asked to identify the company. If it succeeds,
the run is marked `INVALID_FOR_BACKTEST`. That probe is the only credible evidence that a
backtest is not contaminated, so its result is stored alongside every prediction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

PSEUDONYM = "ASSET_ALPHA"

# Words that would identify the market/sector too precisely.
GENERIC_INDEX_TERMS = [
    "NIFTY", "SENSEX", "NSE", "BSE", "National Stock Exchange", "Bombay Stock Exchange",
    "India VIX", "INDIAVIX", "CNXIT", "CNXAUTO", "NSEBANK", "CNXFMCG", "CNXMETAL",
    "CNXENERGY", "CNXPHARMA", "CNXREALTY",
]

CORPORATE_SUFFIXES = [
    "Limited", "Ltd", "Ltd.", "Private", "Pvt", "Inc", "Incorporated", "Corporation",
    "Corp", "Company", "Co.", "PLC", "LLP", "Industries", "Enterprises",
]


@dataclass
class AnonymisationReport:
    replacements: int = 0
    future_tokens_found: list = field(default_factory=list)
    scrubbed_terms: list = field(default_factory=list)
    clean: bool = True


def _year_tokens(cutoff_year: int, lookahead: int = 12):
    """Years and FY labels strictly after the cutoff year - these must never appear."""
    toks = []
    for y in range(cutoff_year + 1, cutoff_year + 1 + lookahead):
        toks.append(str(y))
        toks.append(f"FY{str(y)[2:]}")
        toks.append(f"FY {str(y)[2:]}")
        toks.append(f"FY{y}")
    return toks


def build_name_variants(names: Iterable[str]) -> list:
    """Expand company names into the variants that actually appear in text."""
    out = set()
    for raw in names:
        if not raw:
            continue
        name = str(raw).strip()
        if not name:
            continue
        out.add(name)
        cleaned = name
        for suf in CORPORATE_SUFFIXES:
            cleaned = re.sub(rf"\b{re.escape(suf)}\b\.?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
        if cleaned:
            out.add(cleaned)
            parts = [p for p in cleaned.split() if len(p) > 3]
            out.update(parts)
    # longest first so "Modison Metals" is replaced before "Modison"
    return sorted({o for o in out if len(o) >= 3}, key=len, reverse=True)


def anonymise_text(
    text: str,
    name_variants: Iterable[str],
    cutoff_year: Optional[int] = None,
    report: Optional[AnonymisationReport] = None,
) -> str:
    """Replace entity names, index names and absolute years with neutral tokens."""
    if not text:
        return ""
    rep = report or AnonymisationReport()
    out = str(text)

    for variant in name_variants:
        pat = rf"\b{re.escape(variant)}\b"
        out, n = re.subn(pat, PSEUDONYM, out, flags=re.IGNORECASE)
        if n:
            rep.replacements += n
            rep.scrubbed_terms.append(variant)

    for term in GENERIC_INDEX_TERMS:
        out, n = re.subn(rf"\b{re.escape(term)}\b", "[BENCHMARK_INDEX]", out, flags=re.IGNORECASE)
        rep.replacements += n

    if cutoff_year is not None:
        # Relative period labels: cutoff year -> [T], earlier -> [T-k]
        for offset in range(0, 16):
            y = cutoff_year - offset
            token = "[T]" if offset == 0 else f"[T-{offset}]"
            out, n = re.subn(rf"\b{y}\b", token, out)
            rep.replacements += n
            out, n = re.subn(rf"\bFY\s?{str(y)[2:]}\b", f"FY{token}", out, flags=re.IGNORECASE)
            rep.replacements += n
        # Anything still referencing a future year is a leak, not something to mask.
        for tok in _year_tokens(cutoff_year):
            if re.search(rf"\b{re.escape(tok)}\b", out, flags=re.IGNORECASE):
                rep.future_tokens_found.append(tok)
                rep.clean = False

    # Strip explicit ISO dates that survived
    out = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[DATE]", out)
    return out


def audit_packet(packet: dict, name_variants: Iterable[str], cutoff_year: Optional[int]) -> AnonymisationReport:
    """Fail-closed audit of the fully assembled LLM packet."""
    rep = AnonymisationReport()
    blob = _flatten(packet)
    for variant in name_variants:
        if len(variant) < 4:
            continue
        if re.search(rf"\b{re.escape(variant)}\b", blob, flags=re.IGNORECASE):
            rep.clean = False
            rep.scrubbed_terms.append(f"LEAK:{variant}")
    if cutoff_year is not None:
        for tok in _year_tokens(cutoff_year):
            if re.search(rf"\b{re.escape(tok)}\b", blob, flags=re.IGNORECASE):
                rep.clean = False
                rep.future_tokens_found.append(tok)
    return rep


def _flatten(obj) -> str:
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return " ".join(f"{k} {_flatten(v)}" for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten(v) for v in obj)
    return str(obj)


IDENTITY_PROBE_PROMPT = """You are a forensic equity analyst. Below is an anonymised profile of
a listed company (all names, tickers, exchanges and calendar dates have been removed).

Your task: identify the company if you can.

{packet}

Keep reasoning under 40 words, then emit ONLY this JSON last, inside a ```json fence:
```json
{{"can_identify": true, "company_guess": "<name or empty>", "confidence": 0.0, "clues": "<max 25 words>"}}
```
"""


GENERIC_NAME_TOKENS = {
    "limited", "ltd", "private", "pvt", "company", "corporation", "corp", "industries",
    "enterprises", "technologies", "technology", "systems", "services", "solutions",
    "international", "national", "india", "indian", "bharat", "power", "energy", "bank",
    "motors", "motor", "steel", "metals", "cement", "chemicals", "pharma", "finance",
    "financial", "holdings", "group", "global", "products", "engineering", "electric",
    "electricals", "electronics", "infra", "infrastructure", "projects", "ventures",
    "consultancy", "consulting", "state", "life", "auto", "tech", "labs", "mills",
    "heavy", "industrial", "industrials", "greentech", "green", "realty", "remedies",
}


def distinctive_tokens(names: Iterable[str]) -> list:
    """Name tokens that actually identify a company.

    Matching on generic words like "power", "bank" or "limited" produces false leak reports,
    because those words appear in ordinary analytical prose. Only distinctive tokens count.
    """
    out = set()
    for raw in names or []:
        if not raw:
            continue
        core = re.sub(r"[^a-z0-9 ]", " ", str(raw).lower())
        for tok in core.split():
            if len(tok) >= 4 and tok not in GENERIC_NAME_TOKENS:
                out.add(tok)
    return sorted(out)


def identity_probe_verdict(response_json: Optional[dict], true_names: Iterable[str]) -> dict:
    """Decide whether the probe actually recovered the identity.

    A guess only counts as a leak if it overlaps a *distinctive* part of the real name;
    high self-reported confidence with a wrong guess is not a leak.
    """
    verdict = {
        "probe_ran": response_json is not None,
        "identified": False,
        "guess": "",
        "self_confidence": None,
        "leak": False,
        "matched_token": None,
    }
    if not response_json:
        return verdict
    guess = str(response_json.get("company_guess", "") or "")
    verdict["guess"] = guess[:120]
    verdict["self_confidence"] = response_json.get("confidence")
    if not guess.strip():
        return verdict
    guess_l = guess.lower()
    for token in distinctive_tokens(true_names):
        if token in guess_l:
            verdict["identified"] = True
            verdict["leak"] = True
            verdict["matched_token"] = token
            return verdict
    return verdict
