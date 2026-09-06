"""
precompute_llm.py
=================
Pre-computes the anonymised LLM block (conviction + adversarial identity probe) for every
(ticker, cutoff) in the point-in-time universes, using a thread pool.

Why separate: GLM-5.3 emits several thousand tokens of reasoning per call, so a serial pass
over ~100 (ticker, cutoff) pairs takes over an hour while the GPU sits idle. The LLM block
does not depend on the forecast horizon, so it is computed once, cached in the ledger, and
reused by every horizon. Network calls are parallel; all yfinance/statement work stays
serial because it is already cached and cheap.

Env: TIME_BUDGET_S, EVIDENCE_MODE, LEDGER, MAX_WORKERS
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import SECTOR_BUCKET, price_features  # noqa: E402
from llm_agents import (build_anonymised_packet, retrieve_pit_evidence,  # noqa: E402
                        run_identity_probe, score_conviction)
from pit_data import build_pit_bundle, industry_of, pit_fundamentals  # noqa: E402
from run_validation import COMPANY_NAMES, CUTOFFS, load_ledger, save_ledger  # noqa: E402
from universe import screen_universe  # noqa: E402


def build_packet_for(ticker, cutoff, industry, evidence_mode):
    bundle = build_pit_bundle(ticker, cutoff, 60, max_context=4096, industry=industry)
    names = list(COMPANY_NAMES.get(ticker, [ticker.split(".")[0]])) + [ticker, ticker.split(".")[0]]
    evidence = (retrieve_pit_evidence(COMPANY_NAMES.get(ticker, [ticker.split(".")[0]]), cutoff)
                if evidence_mode == "with_evidence"
                else {"snippets": [], "status": "skipped_numbers_only_mode", "provider": "none",
                      "n_raw": 0, "n_kept": 0, "dropped_future": 0, "dropped_boilerplate": 0})
    packet, anon = build_anonymised_packet(
        fundamentals=pit_fundamentals(ticker, cutoff),
        price_features=price_features(bundle),
        evidence=evidence,
        company_names=names,
        cutoff=cutoff,
        sector_bucket=SECTOR_BUCKET.get(bundle.sector_ticker, "diversified"),
        evidence_mode=evidence_mode,
    )
    return packet, anon, evidence, names


def llm_work(job):
    ticker, cutoff, packet, anon, evidence, names = job
    probe = run_identity_probe(packet, names)
    conv = score_conviction(packet, n_samples=1)
    return ticker, cutoff, {
        "status": conv.status,
        "evidence": {k: v for k, v in evidence.items() if k != "snippets"},
        "anonymisation": anon,
        "identity_probe": probe,
        "conviction_score": conv.conviction_score,
        "axis_scores": conv.axis_scores,
        "expected_rerating_pct": conv.expected_rerating_pct,
        "thesis": conv.thesis,
        "risks": conv.risks,
        "n_samples": conv.n_samples,
        "disagreement": round(conv.disagreement, 2),
        "provider": conv.provider,
    }


def main():
    budget = float(os.environ.get("TIME_BUDGET_S", "1500"))
    evidence_mode = os.environ.get("EVIDENCE_MODE", "numbers_only")
    ledger_path = os.environ.get("LEDGER", "/content/OUT/ledger.json")
    workers = int(os.environ.get("MAX_WORKERS", "6"))
    recompute_probe = os.environ.get("RECOMPUTE_PROBE", "0") == "1"
    t0 = time.time()

    ledger = load_ledger(ledger_path)
    for cut in CUTOFFS:
        if cut not in ledger["universes"]:
            ledger["universes"][cut] = screen_universe(cut)
    save_ledger(ledger, ledger_path)

    if recompute_probe:
        # Refresh ONLY the adversarial identity probe for already-cached blocks, using the
        # corrected distinctive-token matcher. Conviction scores are left untouched.
        jobs = []
        for cut in CUTOFFS:
            for m in ledger["universes"][cut]["members"]:
                tk = m["ticker"]
                key = f"{tk}|{cut}|{evidence_mode}"
                if key not in ledger["llm_cache"]:
                    continue
                ind = ledger["industries"].get(tk) or industry_of(tk, True)
                ledger["industries"][tk] = ind
                try:
                    packet, _anon, _ev, names = build_packet_for(tk, cut, ind, evidence_mode)
                except Exception as exc:
                    print(f"  packet ERROR {tk} {cut}: {type(exc).__name__}")
                    continue
                jobs.append((key, packet, names))
        print(f"[precompute] re-running {len(jobs)} identity probes with corrected matcher")
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(run_identity_probe, p, n): k for k, p, n in jobs}
            for fut in as_completed(futs):
                key = futs[fut]
                try:
                    probe = fut.result()
                    ledger["llm_cache"][key]["identity_probe"] = probe
                    done += 1
                    print(f"  [{done}/{len(jobs)}] {key.split('|')[0]:15s} {key.split('|')[1]} "
                          f"leak={probe.get('leak')} guess={str(probe.get('guess'))[:28]!r} "
                          f"token={probe.get('matched_token')}")
                    if done % 8 == 0:
                        save_ledger(ledger, ledger_path)
                except Exception as exc:
                    print(f"  probe ERROR {key}: {type(exc).__name__}: {str(exc)[:100]}")
        save_ledger(ledger, ledger_path)
        leaks = sum(1 for v in ledger["llm_cache"].values()
                    if v.get("identity_probe", {}).get("leak"))
        print(f"[precompute] probes refreshed={done} leaking={leaks}/{len(ledger['llm_cache'])} "
              f"elapsed={round(time.time()-t0,1)}s")
        print("REMAINING:0")
        return

    pairs = []
    for cut in CUTOFFS:
        for m in ledger["universes"][cut]["members"]:
            key = f"{m['ticker']}|{cut}|{evidence_mode}"
            if key not in ledger["llm_cache"]:
                pairs.append((m["ticker"], cut))
    print(f"[precompute] {len(pairs)} (ticker,cutoff) LLM blocks to compute, workers={workers}")

    jobs = []
    for ticker, cut in pairs:
        if time.time() - t0 > budget * 0.35:
            break
        try:
            if ticker not in ledger["industries"]:
                ledger["industries"][ticker] = industry_of(ticker, allow_live_metadata=True)
            ind = ledger["industries"][ticker]
            packet, anon, evidence, names = build_packet_for(ticker, cut, ind, evidence_mode)
            jobs.append((ticker, cut, packet, anon, evidence, names))
        except Exception as exc:
            print(f"  packet ERROR {ticker} {cut}: {type(exc).__name__}: {str(exc)[:120]}")
    save_ledger(ledger, ledger_path)
    print(f"[precompute] {len(jobs)} packets built in {round(time.time()-t0,1)}s; calling LLM...")

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(llm_work, j): j for j in jobs}
        for fut in as_completed(futs):
            job = futs[fut]
            try:
                ticker, cut, block = fut.result()
                ledger["llm_cache"][f"{ticker}|{cut}|{evidence_mode}"] = block
                done += 1
                pr = block["identity_probe"]
                print(f"  [{done}/{len(jobs)}] {ticker} {cut}: conv={block['conviction_score']} "
                      f"status={block['status'][:28]} probe_leak={pr.get('leak')} "
                      f"guess={str(pr.get('guess'))[:24]!r}")
                if done % 5 == 0:
                    save_ledger(ledger, ledger_path)
            except Exception as exc:
                print(f"  llm ERROR {job[0]} {job[1]}: {type(exc).__name__}: {str(exc)[:120]}")
    save_ledger(ledger, ledger_path)
    remaining = sum(
        1 for cut in CUTOFFS for m in ledger["universes"][cut]["members"]
        if f"{m['ticker']}|{cut}|{evidence_mode}" not in ledger["llm_cache"]
    )
    print(f"[precompute] cached={len(ledger['llm_cache'])} remaining={remaining} "
          f"elapsed={round(time.time()-t0,1)}s")
    print("REMAINING:" + str(remaining))


if __name__ == "__main__":
    main()
