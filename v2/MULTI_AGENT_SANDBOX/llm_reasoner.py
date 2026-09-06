"""
llm_reasoner.py -- AkashML Semantic Reasoner for TimesFM 3.0 Hybrid Pipeline
Powered by zai-org/GLM-5.3 via AkashML (https://api.akashml.com/v1/chat/completions)

No rate-limits. Deep institutional reasoning. Automatic mathematical guardrails
(Target Price = EPS * Target P/E) and graceful fallback to audited statement formulas.
"""

import os
import json
import re
import requests
from typing import Dict, Any, Optional

def get_akashml_api_key() -> str:
    key = os.environ.get("AKASHML_API_KEY")
    if key:
        return key.strip()
    for loc in [
        os.path.join(os.path.dirname(__file__), ".akashml_key"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".akashml_key"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
        ".env"
    ]:
        if os.path.exists(loc):
            try:
                with open(loc) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("AKASHML_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif not line.startswith("#") and loc.endswith(".akashml_key") and line:
                            return line
            except Exception:
                pass
    return ""

AKASHML_API_KEY = get_akashml_api_key()
INVOKE_URL = "https://api.akashml.com/v1/chat/completions"
DEFAULT_MODEL = "zai-org/GLM-5.3"

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM text output."""
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    
    # Try finding markdown code block ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Try finding any outer braces { ... }
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None

def invoke_akashml_reasoner(
    prompt: str,
    system_prompt: str = "You are an institutional quantitative equity research analyst.",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    temperature: float = 0.0,
    top_p: float = 0.9,
    timeout: int = 90
) -> Dict[str, Any]:
    """
    Invokes AkashML API with zai-org/GLM-5.3.
    """
    api_key = get_akashml_api_key()
    if not api_key:
        return {
            "success": False,
            "error": "AKASHML_API_KEY not configured in environment or .env file",
            "source": "heuristic_fallback"
        }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": f"{system_prompt}\n\n{prompt}"
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p
    }

    try:
        print(f"[LLM_Reasoner] Querying AkashML model: {model}...")
        response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content", "")
            reasoning = msg.get("reasoning_content", "")
            print(f"[LLM_Reasoner] Response received from {model} ({len(content)} chars, {len(reasoning)} reasoning chars).")
            return {
                "success": True,
                "model": model,
                "content": content,
                "reasoning": reasoning
            }
        else:
            print(f"[LLM_Reasoner] AkashML returned HTTP {response.status_code}: {response.text[:200]}")
            return {
                "success": False,
                "model": model,
                "content": "",
                "reasoning": "",
                "error": response.text
            }

    except requests.exceptions.Timeout:
        print(f"[LLM_Reasoner] Timeout ({timeout}s) waiting for AkashML {model}.")
        return {"success": False, "model": model, "content": "", "reasoning": "", "error": "timeout"}
    except Exception as e:
        print(f"[LLM_Reasoner] Error connecting to AkashML {model}: {e}")
        return {"success": False, "model": model, "content": "", "reasoning": "", "error": str(e)}

def reason_market_scenarios(
    ticker: str,
    current_price: float,
    eps: float,
    sector_pe: float,
    eps_cagr: Optional[float] = None,
    industry: str = "",
    recent_news: str = "",
    revenue_growth: Optional[float] = None,
    earnings_growth: Optional[float] = None,
    institutional_benchmark_pe: Optional[float] = None,
    institutional_target: Optional[float] = None
) -> Dict[str, Any]:
    """
    Synthesizes fundamental data and qualitative thesis through AkashML zai-org/GLM-5.3.
    Returns calibrated scenario targets (bear, base, bull) and probabilities.
    Ensures mathematical consistency: Target Price = EPS * Target P/E.
    """
    cagr_str = f"{eps_cagr*100:.1f}%" if eps_cagr is not None else "N/A"
    rev_str = f"{revenue_growth*100:+.1f}% YoY" if revenue_growth is not None else "N/A"
    earn_str = f"{earnings_growth*100:+.1f}% YoY" if earnings_growth is not None else "N/A"
    bench_pe = institutional_benchmark_pe or sector_pe
    bench_tgt = institutional_target or (eps * bench_pe)
    
    prompt = f"""
Analyze equity target for {ticker} ({industry}).
Comprehensive Financial & Market Context:
- Current Market Price: Rs. {current_price:.2f}
- Effective Normalized EPS: Rs. {eps:.2f}
- Current Trailing P/E: {current_price/eps:.1f}x
- Industry Sector P/E: {sector_pe:.1f}x
- Growth Calibration: Revenue {rev_str} | Earnings {earn_str}
- Institutional Growth-Calibrated Forward Multiple: {bench_pe:.1f}x
- Quantitative Baseline Fair Target: Rs. {bench_tgt:.2f}
- Qualitative News / Catalyst Context: {recent_news or 'Standard quarterly operations'}

Tasks:
1. Provide a concise institutional reasoning (under 80 words) evaluating multiple premium/discount.
2. Determine appropriate 12-month Forward P/E multiples for Bear, Base, and Bull scenarios centered around the {bench_pe:.1f}x institutional benchmark.
   CRITICAL INSTITUTIONAL GUIDANCE:
   - Carefully evaluate the Qualitative News / Catalyst Context alongside YoY earnings growth ({earn_str}).
   - If material positive catalysts exist (e.g. AI servers, defense orders, capacity expansion, promoter buying, export growth), align the Base forward P/E close to {bench_pe:.1f}x.
   - If negative events exist, reflect margin compression and multiple de-rating.
   - Ground multiples rationally based on real forward earning power.
3. Assign probability weights for Bear, Base, Bull (e.g. 0.25, 0.50, 0.25) summing to 1.0.

CRITICAL: Keep your internal thinking strictly under 100 words. You MUST output the final JSON block below:
```json
{{
  "thesis": "<1-2 sentence institutional thesis>",
  "bear": {{"target_pe": <float>, "probability": <float>}},
  "base": {{"target_pe": <float>, "probability": <float>}},
  "bull": {{"target_pe": <float>, "probability": <float>}}
}}
```
"""
    result = invoke_akashml_reasoner(prompt)
    
    if result["success"]:
        # Check both content and reasoning_content for JSON
        parsed = _extract_json(result["content"])
        if not parsed and result["reasoning"]:
            parsed = _extract_json(result["reasoning"])

        if parsed and "bear" in parsed and "base" in parsed and "bull" in parsed:
            try:
                bear_pe = float(parsed["bear"].get("target_pe", sector_pe * 0.8))
                base_pe = float(parsed["base"].get("target_pe", sector_pe * 1.0))
                bull_pe = float(parsed["bull"].get("target_pe", sector_pe * 1.3))
                
                # Sanity bounds on target multiples (between 5x and 150x)
                bear_pe = max(5.0, min(150.0, bear_pe))
                base_pe = max(bear_pe, min(150.0, base_pe))
                bull_pe = max(base_pe, min(180.0, bull_pe))

                bear_p = float(parsed["bear"].get("probability", 0.25))
                base_p = float(parsed["base"].get("probability", 0.50))
                bull_p = float(parsed["bull"].get("probability", 0.25))
                
                total_p = bear_p + base_p + bull_p
                if abs(total_p - 1.0) > 0.05 and total_p > 0:
                    bear_p /= total_p
                    base_p /= total_p
                    bull_p /= total_p

                # Strict mathematical integrity: Target Price = EPS * Target P/E
                bear_tp = round(eps * bear_pe, 2)
                base_tp = round(eps * base_pe, 2)
                bull_tp = round(eps * bull_pe, 2)
                wt = round(bear_p * bear_tp + base_p * base_tp + bull_p * bull_tp, 2)
                
                return {
                    "source": f"llm_akashml_{result['model']}",
                    "thesis": parsed.get("thesis", "Institutional valuation scenario analysis."),
                    "scenarios": {
                        "bear": {"probability": round(bear_p, 2), "target_pe": round(bear_pe, 1), "target_price": bear_tp},
                        "base": {"probability": round(base_p, 2), "target_pe": round(base_pe, 1), "target_price": base_tp},
                        "bull": {"probability": round(bull_p, 2), "target_pe": round(bull_pe, 1), "target_price": bull_tp},
                    },
                    "weighted_target": wt,
                    "reasoning": result.get("reasoning", "")
                }
            except Exception as e:
                print(f"[LLM_Reasoner] Error parsing AkashML numeric fields: {e}")

    # Fallback to audited statement formula
    print("[LLM_Reasoner] Fallback to audited fundamental formula.")
    band = (0.75, 1.00, 1.30) if (eps_cagr or 0) > 0.15 else (0.65, 0.90, 1.15) if (eps_cagr or 0) > 0.07 else (0.55, 0.78, 1.00)
    sc = {
        "bear": {"probability": 0.25, "target_pe": round(sector_pe * band[0], 1), "target_price": round(eps * sector_pe * band[0], 2)},
        "base": {"probability": 0.50, "target_pe": round(sector_pe * band[1], 1), "target_price": round(eps * sector_pe * band[1], 2)},
        "bull": {"probability": 0.25, "target_pe": round(sector_pe * band[2], 1), "target_price": round(eps * sector_pe * band[2], 2)},
    }
    wt = round(sum(s["probability"] * s["target_price"] for s in sc.values()), 2)
    return {
        "source": "audited_formula_fallback",
        "thesis": f"Fundamental valuation using audited EPS of Rs. {eps:.2f} and sector P/E of {sector_pe:.1f}x.",
        "scenarios": sc,
        "weighted_target": wt,
        "reasoning": ""
    }

if __name__ == "__main__":
    import sys
    tk = sys.argv[1] if len(sys.argv) > 1 else "MODISONLTD.NS"
    res = reason_market_scenarios(
        ticker=tk,
        current_price=469.95,
        eps=22.35,
        sector_pe=22.0,
        eps_cagr=0.12,
        industry="Metals & Mining",
        recent_news="Debt-free balance sheet, high electrical contact silver demand."
    )
    print("\n--- AKASHML REASONING RESULT ---")
    print(json.dumps(res, indent=2))
