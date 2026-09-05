"""
llm_reasoner.py -- NVIDIA NIM Semantic Reasoner for TimesFM 3.0 Hybrid Pipeline
Integrates moonshotai/kimi-k3 (with streaming & reasoning extraction)
and provides resilient fallback to meta/llama-3.2-11b-vision-instruct.

Bridging qualitative disclosures, guidance, and sector dynamics into
rigorous quantitative target prices and scenario probabilities for TimesFM 3.0.
"""

import os
import json
import re
import requests
from typing import Dict, Any, Optional

def get_nvidia_api_key() -> str:
    key = os.environ.get("NVIDIA_API_KEY")
    if key:
        return key.strip()
    for loc in [
        os.path.join(os.path.dirname(__file__), ".nvidia_key"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".nvidia_key"),
        "/content/timesfm_repo/.nvidia_key"
    ]:
        if os.path.exists(loc):
            try:
                with open(loc) as f:
                    k = f.read().strip()
                    if k: return k
            except Exception:
                pass
    return ""

NVIDIA_API_KEY = get_nvidia_api_key()
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse JSON from LLM text output."""
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return None

def invoke_nvidia_reasoner(
    prompt: str,
    system_prompt: str = "You are an institutional quantitative equity research analyst.",
    primary_model: str = "moonshotai/kimi-k3",
    fallback_model: str = "meta/llama-3.2-11b-vision-instruct",
    stream: bool = True,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    timeout: int = 90
) -> Dict[str, Any]:
    """
    Invokes NVIDIA NIM API with streaming support.
    Attempts primary_model (kimi-k3), falling back to fallback_model on 429/timeout.
    """
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json"
    }

    models_to_try = [primary_model, fallback_model] if fallback_model else [primary_model]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{system_prompt}\n\n{prompt}"
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "seed": 0,
            "stream": stream,
            "temperature": temperature
        }
        
        if "kimi" in model_name:
            payload["reasoning_effort"] = "max"

        try:
            print(f"[LLM_Reasoner] Querying NVIDIA NIM model: {model_name} (stream={stream})...")
            response = requests.post(INVOKE_URL, headers=headers, json=payload, stream=stream, timeout=timeout)
            
            if response.status_code == 200:
                full_content = ""
                full_reasoning = ""
                
                if stream:
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode("utf-8")
                            if decoded.startswith("data: "):
                                data_str = decoded[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "reasoning_content" in delta and delta["reasoning_content"]:
                                        full_reasoning += delta["reasoning_content"]
                                    if "content" in delta and delta["content"]:
                                        full_content += delta["content"]
                                except Exception:
                                    pass
                else:
                    data = response.json()
                    msg = data["choices"][0].get("message", {})
                    full_content = msg.get("content", "")
                    full_reasoning = msg.get("reasoning_content", "")

                print(f"[LLM_Reasoner] Response received from {model_name} ({len(full_content)} chars).")
                return {
                    "success": True,
                    "model": model_name,
                    "content": full_content,
                    "reasoning": full_reasoning
                }
            elif response.status_code == 429:
                print(f"[LLM_Reasoner] {model_name} rate limited (HTTP 429). Attempting fallback...")
                continue
            else:
                print(f"[LLM_Reasoner] {model_name} returned HTTP {response.status_code}: {response.text[:200]}")
                continue

        except requests.exceptions.Timeout:
            print(f"[LLM_Reasoner] Timeout ({timeout}s) waiting for {model_name}.")
            continue
        except Exception as e:
            print(f"[LLM_Reasoner] Error connecting to {model_name}: {e}")
            continue

    return {
        "success": False,
        "model": None,
        "content": "",
        "reasoning": ""
    }

def reason_market_scenarios(
    ticker: str,
    current_price: float,
    eps: float,
    sector_pe: float,
    eps_cagr: Optional[float] = None,
    industry: str = "",
    recent_news: str = ""
) -> Dict[str, Any]:
    """
    Synthesizes fundamental data and qualitative thesis through LLM reasoning.
    Returns calibrated scenario targets (bear, base, bull) and probabilities.
    Ensures mathematical consistency: Target Price = EPS * Target P/E.
    """
    cagr_str = f"{eps_cagr*100:.1f}%" if eps_cagr is not None else "N/A"
    
    prompt = f"""
Analyze the equity target for {ticker} ({industry}).
Market Context:
- Current Market Price: Rs. {current_price:.2f}
- Audited Diluted EPS: Rs. {eps:.2f}
- Current Implied P/E: {current_price/eps:.1f}x
- Industry Benchmark P/E: {sector_pe:.1f}x
- Historical EPS CAGR: {cagr_str}
- Qualitative News / Catalyst Context: {recent_news or 'Standard quarterly operations'}

Tasks:
1. Provide an institutional qualitative thesis (1-2 sentences) evaluating valuation premium/discount.
2. Determine appropriate 12-month Forward P/E multiples for Bear, Base, and Bull scenarios.
   (Note: Current P/E is {current_price/eps:.1f}x vs Sector P/E {sector_pe:.1f}x).
3. Assign probability weights for Bear, Base, Bull (e.g. 0.25, 0.50, 0.25) summing to 1.0.

You MUST reply with ONLY a valid JSON object matching this exact schema:
{{
  "thesis": "<1-2 sentence institutional thesis>",
  "bear": {{"target_pe": <float>, "probability": <float>}},
  "base": {{"target_pe": <float>, "probability": <float>}},
  "bull": {{"target_pe": <float>, "probability": <float>}}
}}
"""
    result = invoke_nvidia_reasoner(prompt)
    
    if result["success"]:
        parsed = _extract_json(result["content"])
        if parsed and "bear" in parsed and "base" in parsed and "bull" in parsed:
            try:
                bear_pe = float(parsed["bear"].get("target_pe", sector_pe * 0.8))
                base_pe = float(parsed["base"].get("target_pe", sector_pe * 1.0))
                bull_pe = float(parsed["bull"].get("target_pe", sector_pe * 1.3))
                
                # Sanity bound on target multiples (between 5x and 150x)
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

                # Quantitative institutional integrity: Target Price = EPS * Target P/E
                bear_tp = round(eps * bear_pe, 2)
                base_tp = round(eps * base_pe, 2)
                bull_tp = round(eps * bull_pe, 2)
                wt = round(bear_p * bear_tp + base_p * base_tp + bull_p * bull_tp, 2)
                
                return {
                    "source": f"llm_nvidia_{result['model']}",
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
                print(f"[LLM_Reasoner] Error parsing LLM numeric fields: {e}")

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
        current_price=469.0,
        eps=8.64,
        sector_pe=22.0,
        eps_cagr=0.12,
        industry="Metals & Mining",
        recent_news="Q1 profit up 24% YoY; high electrical contact silver demand; debt-free operations."
    )
    print("\n--- REASONING RESULT ---")
    print(json.dumps(res, indent=2))
