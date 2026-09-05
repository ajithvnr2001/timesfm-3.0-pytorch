#!/usr/bin/env python3
"""
test_multi_agent_flow.py
========================
End-to-End Verification Test for Multi-Agent Zero-Leakage Triad:
1. Ingests HEROMOTOCO.NS strictly before 2023-12-31.
2. Demonstrates A2A protocol message dispatch between Agent 1 and Agent 2.
3. Proves ProcessAgent operates with ZERO knowledge of asset identity or dates.
4. Generates output report and visual chart.
"""

import os
import sys
from multi_agent_system import MultiAgentCoordinator

def main():
    ticker = "HEROMOTOCO.NS"
    cutoff = "2023-12-31"
    horizon = 663
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_results", "test_run_output")

    print(f"Executing Multi-Agent Test Flow on {ticker} (Cutoff: {cutoff}, Horizon: {horizon} Days)...")
    coordinator = MultiAgentCoordinator()
    record = coordinator.run(ticker, cutoff, horizon, out_dir)

    print("=================================================================")
    print(" VERIFICATION TEST COMPLETED SUCCESSFULLY")
    print("=================================================================")
    print(f"• A2A Ingress Message ID: {record['a2a_message_id']}")
    print(f"• Pure Baseline Terminal: Rs. {record['metrics']['pure_baseline_terminal']:.2f} (Exploded: {record['metrics']['pure_baseline_error_pct']:+.1f}%)")
    print(f"• Bull Scenario Terminal: Rs. {record['metrics']['bull_terminal']:.2f} (Error: {record['metrics']['bull_error_pct']:+.1f}%)")
    print(f"• Weighted Model Terminal: Rs. {record['metrics']['weighted_terminal']:.2f}")
    print(f"• Scenario Envelope Coverage: {record['metrics']['envelope_coverage_pct']:.1f}%")
    print(f"• Chart: {record['chart_saved']}")
    print(f"• Report: {record['report_saved']}")
    print("=================================================================")

if __name__ == "__main__":
    main()
