"""
llm_agents.py
=============
LLM layer for the institutional engine. Three jobs, all on anonymised point-in-time input:

  1. `retrieve_pit_evidence`  - Exa neural search hard-locked to `end_published_date`,
     with post-filtering of any snippet that mentions a post-cutoff year.
  2. `score_conviction`       - structured multi-bagger forensics with n-sample
     self-consistency; returns per-axis scores, an expected re-rating range expressed in
     PERCENT (never an absolute P/E, because yfinance reports some NSE names in USD), and
     the sample disagreement as an explicit uncertainty measure.
  3. `run_identity_probe`     - adversarial check that the anonymised packet cannot be
     traced back to the company.

Providers: AkashML (zai-org/GLM-5.3) primary, NVIDIA NIM fallback. Keys come from the
environment only - nothing is hardcoded and nothing is written to disk.
"""

from __future__ import annotations

import json
import os
import re
import statistics
from dataclasses import dataclass, field
from typing import Optional

import requests

from anonymizer import (
    IDENTITY_PROBE_PROMPT,
    PSEUDONYM,
    anonymise_text,
    build_name_variants,
    identity_probe_verdict,
)

AKASHML_URL = "https://api.akashml.com/v1/chat/completions"
AKASHML_MODEL = "zai-org/GLM-5.3"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "moonshotai/kimi-k2-instruct"

CONVICTION_AXES = [
    "earnings_acceleration",
    "margin_expansion",
    "capacity_or_orderbook_expansion",
    "balance_sheet_repair",
    "rerating_headroom",
]


@dataclass
class LLMCall:
    ok: bool
    content: str = ""
    provider: str = ""
    model: str = ""
    error: str = ""
    latency_s: float = 0.0


@dataclass
class ConvictionResult:
    conviction_score: float = 0.0  # 0..100
    axis_scores: dict = field(default_factory=dict)
    expected_rerating_pct: dict = field(default_factory=dict)  # bear/base/bull, % vs spot
    thesis: str = ""
    risks: str = ""
    n_samples: int = 0
    disagreement: float = 0.0  # stdev of conviction across samples
    provider: str = ""
    status: str = "unavailable"
    raw_samples: list = field(default_factory=list)


# ------------------------------------------------------------------ transport
def _post(url: str, key: str, model: str, prompt: str, temperature: float, max_tokens: int,
          timeout: int) -> LLMCall:
    import time

    t0 = time.time()
    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95,
            },
            timeout=timeout,
        )
        dt = round(time.time() - t0, 2)
        if r.status_code != 200:
            return LLMCall(False, provider=url, model=model, error=f"HTTP {r.status_code}: {r.text[:200]}", latency_s=dt)
        data = r.json()
        msg = data["choices"][0].get("message", {})
        content = msg.get("content") or ""
        if not content and msg.get("reasoning_content"):
            content = msg["reasoning_content"]
        return LLMCall(True, content=content, provider=url, model=model, latency_s=dt)
    except Exception as exc:
        return LLMCall(False, provider=url, model=model, error=f"{type(exc).__name__}: {exc}",
                       latency_s=round(time.time() - t0, 2))


def call_llm(prompt: str, temperature: float = 0.2, max_tokens: int = 2048, timeout: int = 120) -> LLMCall:
    akash = os.environ.get("AKASHML_API_KEY", "").strip()
    if akash:
        res = _post(AKASHML_URL, akash, AKASHML_MODEL, prompt, temperature, max_tokens, timeout)
        if res.ok:
            res.provider = "akashml"
            return res
        first_error = res.error
    else:
        first_error = "AKASHML_API_KEY not set"

    nvidia = (os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY") or "").strip()
    if nvidia:
        res = _post(NVIDIA_URL, nvidia, NVIDIA_MODEL, prompt, temperature, max_tokens, timeout)
        res.provider = "nvidia_nim"
        if not res.ok:
            res.error = f"akashml[{first_error[:80]}] nvidia[{res.error[:120]}]"
        return res
    return LLMCall(False, error=f"no usable LLM key ({first_error})")


def extract_json(text: str) -> Optional[dict]:
    """Robustly pull the final JSON object out of a reasoning-heavy response.

    Models like GLM-5.3 emit long chain-of-thought before the answer, so we scan for
    balanced-brace candidates and prefer the LAST one that parses and looks like a result.
    """
    if not text:
        return None
    # 1. fenced code block wins if present
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL):
        try:
            return json.loads(m.group(1))
        except Exception:
            continue
    # 2. balanced-brace scan, last complete object first
    candidates = []
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidates.append(text[start : i + 1])
    for cand in reversed(candidates):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict) and obj:
                return obj
        except Exception:
            continue
    try:
        return json.loads(text.strip())
    except Exception:
        return None


# ------------------------------------------------------------------- evidence
def retrieve_pit_evidence(company_names: list, cutoff: Optional[str], max_results: int = 6) -> dict:
    """Exa search with a hard publication ceiling at the cutoff, then future-token filtering."""
    out = {"snippets": [], "provider": "exa", "status": "unavailable", "n_raw": 0, "n_kept": 0,
           "dropped_future": 0, "dropped_boilerplate": 0}
    key = os.environ.get("EXA_API_KEY", "").strip()
    if not key:
        out["status"] = "no_api_key"
        return out
    primary = next((n for n in company_names if n), None)
    if not primary:
        out["status"] = "no_company_name"
        return out
    try:
        from exa_py import Exa

        exa = Exa(api_key=key)
        query = (
            f"{primary} quarterly results order book capacity expansion margin "
            "management commentary debt reduction"
        )
        kwargs = {"num_results": max_results, "type": "neural", "text": True}
        if cutoff:
            kwargs["end_published_date"] = f"{cutoff}T23:59:59Z"
        res = exa.search_and_contents(query, **kwargs)
        results = getattr(res, "results", []) or []
        out["n_raw"] = len(results)
        cutoff_year = int(str(cutoff)[:4]) if cutoff else None
        boiler = ("Registered Office", "CIN:", "Compliance Officer", "Trading Window",
                  "Scrip Code", "Exchange Plaza", "Bandra-Kurla", "Tel. No.", "Fax:")
        for r in results:
            pub = str(getattr(r, "published_date", "") or "")[:10]
            if cutoff and pub and pub > str(cutoff)[:10]:
                out["dropped_future"] += 1
                continue
            text = (getattr(r, "text", "") or "").replace("\n", " ").strip()
            title = (getattr(r, "title", "") or "").strip()
            if not text:
                continue
            sentences = [
                s.strip() for s in text.split(".")
                if len(s.strip()) > 40 and not any(b in s for b in boiler)
            ]
            if not sentences:
                out["dropped_boilerplate"] += 1
                continue
            snippet = ". ".join(sentences[:4])[:700]
            if cutoff_year is not None:
                future = [str(y) for y in range(cutoff_year + 1, cutoff_year + 8)]
                if any(re.search(rf"\b{y}\b", snippet) for y in future):
                    out["dropped_future"] += 1
                    continue
            out["snippets"].append({"title": title, "text": snippet, "published": pub})
        out["n_kept"] = len(out["snippets"])
        out["status"] = "ok" if out["snippets"] else "no_usable_results"
    except Exception as exc:
        out["status"] = f"error: {type(exc).__name__}: {str(exc)[:120]}"
    return out


# -------------------------------------------------------------------- packets
def build_anonymised_packet(
    fundamentals: dict,
    price_features: dict,
    evidence: dict,
    company_names: list,
    cutoff: Optional[str],
    sector_bucket: str = "unspecified",
    evidence_mode: str = "numbers_only",
) -> tuple:
    """Assemble the LLM input with every identifying detail removed. Returns (packet, report).

    `evidence_mode`:
      * "numbers_only"  - unit-free numbers only. Free-text evidence is EXCLUDED because
        business descriptions ("silver electrical contacts", "German collaboration") are
        themselves identifying even after names are scrubbed. This is the leak-proof mode
        used for headline backtests.
      * "with_evidence" - includes anonymised pre-cutoff snippets. Richer, but identity can
        leak through business description, so the identity probe result must be honoured.
    """
    variants = build_name_variants(company_names)
    cutoff_year = int(str(cutoff)[:4]) if cutoff else None

    def pct(x, nd=1):
        return None if x is None else round(100.0 * float(x), nd)

    clean_snippets = []
    from anonymizer import AnonymisationReport

    rep = AnonymisationReport()
    if evidence_mode == "with_evidence":
        for s in evidence.get("snippets", [])[:6]:
            txt = anonymise_text(f"{s.get('title','')}. {s.get('text','')}", variants, cutoff_year, rep)
            if txt.strip():
                clean_snippets.append(txt[:600])

    packet = {
        "asset_pseudonym": PSEUDONYM,
        "sector_bucket": sector_bucket,
        "reporting_period": "[T]",
        "fundamentals_unit_free": {
            "revenue_growth_yoy_pct": pct(fundamentals.get("revenue_growth_yoy")),
            "revenue_cagr_3y_pct": pct(fundamentals.get("revenue_cagr_3y")),
            "eps_growth_yoy_pct": pct(fundamentals.get("eps_growth_yoy")),
            "eps_cagr_3y_pct": pct(fundamentals.get("eps_cagr_3y")),
            "gross_margin_pct": pct(fundamentals.get("gross_margin")),
            "operating_margin_pct": pct(fundamentals.get("operating_margin")),
            "net_margin_pct": pct(fundamentals.get("net_margin")),
            "operating_margin_change_3y_pp": pct(fundamentals.get("operating_margin_delta_3y")),
            "roe_pct": pct(fundamentals.get("roe")),
            "debt_to_equity": None if fundamentals.get("debt_to_equity") is None
            else round(float(fundamentals["debt_to_equity"]), 2),
            "equity_growth_yoy_pct": pct(fundamentals.get("equity_growth_yoy")),
            "annual_periods_available": fundamentals.get("annual_periods_used", 0),
        },
        "price_behaviour_unit_free": price_features,
        "pre_cutoff_evidence": clean_snippets,
        "evidence_mode": evidence_mode,
    }

    from anonymizer import audit_packet

    audit = audit_packet(packet, variants, cutoff_year)
    return packet, {"anonymisation": rep.__dict__, "audit": audit.__dict__,
                    "n_evidence_used": len(clean_snippets), "evidence_mode": evidence_mode}


CONVICTION_PROMPT = """You are a senior analyst at a long-only institutional fund that hunts
multi-year compounders ("multi-baggers"). You must judge ONLY from the anonymised,
point-in-time data below. You do not know the company, the country's index level, or
anything that happened after the reporting period labelled [T]. Do not speculate about
identity. If evidence is missing, say so and score conservatively.

ANONYMISED COMPANY PACKET
{packet}

Score each axis 0-100 (0 = clearly absent, 50 = neutral/unknown, 100 = exceptionally strong):
  earnings_acceleration            - is profit growth accelerating, not just positive?
  margin_expansion                 - operating/net margin trend and durability
  capacity_or_orderbook_expansion  - evidence of capex, new capacity, orders, exports
  balance_sheet_repair             - leverage trend, equity build, funding quality
  rerating_headroom                - scope for a valuation multiple to expand from here

Then give an expected 12-month re-rating range as a PERCENTAGE change from the current price
(negative allowed). Never quote an absolute price or P/E - you do not know the currency.

OUTPUT DISCIPLINE: keep any reasoning under 60 words, then emit the JSON block LAST inside
a ```json fence. The JSON must be the final content in your reply.

```json
{{"axis_scores": {{"earnings_acceleration": <int>, "margin_expansion": <int>,
"capacity_or_orderbook_expansion": <int>, "balance_sheet_repair": <int>,
"rerating_headroom": <int>}},
 "conviction_score": <int 0-100>,
 "expected_rerating_pct": {{"bear": <float>, "base": <float>, "bull": <float>}},
 "thesis": "<max 40 words>",
 "risks": "<max 25 words>",
 "evidence_quality": "strong|moderate|thin"}}
```
"""


def score_conviction(packet: dict, n_samples: int = 3, temperature: float = 0.3) -> ConvictionResult:
    """Multi-sample self-consistency scoring. Median aggregation, stdev as disagreement."""
    prompt = CONVICTION_PROMPT.format(packet=json.dumps(packet, indent=1))
    samples, provider, errors = [], "", []
    for i in range(max(1, n_samples)):
        call = call_llm(prompt, temperature=temperature if n_samples > 1 else 0.0, max_tokens=6000)
        if not call.ok:
            errors.append(call.error[:120])
            continue
        provider = call.provider
        parsed = extract_json(call.content)
        if not parsed or "conviction_score" not in parsed:
            errors.append(f"unparseable(len={len(call.content)})")
            continue
        try:
            axes = {a: float(parsed.get("axis_scores", {}).get(a, 50.0)) for a in CONVICTION_AXES}
            rr = parsed.get("expected_rerating_pct", {}) or {}
            samples.append({
                "conviction": float(parsed["conviction_score"]),
                "axes": axes,
                "rerating": {k: float(rr.get(k, 0.0)) for k in ("bear", "base", "bull")},
                "thesis": str(parsed.get("thesis", ""))[:400],
                "risks": str(parsed.get("risks", ""))[:300],
                "evidence_quality": str(parsed.get("evidence_quality", "unknown")),
            })
        except Exception:
            continue

    if not samples:
        return ConvictionResult(status=f"llm_unavailable({'; '.join(errors[:2])})")

    convs = [s["conviction"] for s in samples]
    res = ConvictionResult(
        conviction_score=float(statistics.median(convs)),
        axis_scores={a: float(statistics.median([s["axes"][a] for s in samples])) for a in CONVICTION_AXES},
        expected_rerating_pct={
            k: float(statistics.median([s["rerating"][k] for s in samples]))
            for k in ("bear", "base", "bull")
        },
        thesis=samples[0]["thesis"],
        risks=samples[0]["risks"],
        n_samples=len(samples),
        disagreement=float(statistics.pstdev(convs)) if len(convs) > 1 else 0.0,
        provider=provider,
        status="ok",
        raw_samples=samples,
    )
    # Enforce monotone re-rating scenarios
    rr = res.expected_rerating_pct
    lo, mid, hi = sorted([rr["bear"], rr["base"], rr["bull"]])
    res.expected_rerating_pct = {"bear": lo, "base": mid, "bull": hi}
    return res


def run_identity_probe(packet: dict, true_names: list) -> dict:
    """Ask a fresh LLM call to name the company from the anonymised packet.

    GLM-style models emit long reasoning, so we allow a large token budget and fall back to
    scanning the prose for a *distinctive* name token if the JSON block is missing.
    """
    from anonymizer import distinctive_tokens

    prompt = IDENTITY_PROBE_PROMPT.format(packet=json.dumps(packet, indent=1))
    call = call_llm(prompt, temperature=0.0, max_tokens=9000)
    parsed = extract_json(call.content) if call.ok else None
    verdict = identity_probe_verdict(parsed, true_names)
    verdict["provider"] = call.provider
    verdict["error"] = call.error[:200] if not call.ok else ""
    verdict["raw_excerpt"] = (call.content or "")[-500:]

    if call.ok and parsed is None:
        verdict["probe_ran"] = True
        verdict["parse_fallback"] = True
        blob = call.content.lower()
        for token in distinctive_tokens(true_names):
            if token in blob:
                verdict["identified"] = True
                verdict["leak"] = True
                verdict["guess"] = f"prose_match:{token}"
                verdict["matched_token"] = token
                return verdict
        verdict["error"] = f"probe_json_missing(len={len(call.content)}); prose scan found no distinctive name"
    return verdict
