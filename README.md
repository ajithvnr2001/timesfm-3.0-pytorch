# TimesFM 3.0 Research & Benchmarking

Repository for research, benchmarking, and real-world evaluation of Google Research's **TimesFM 3.0** (`google/timesfm-3.0-pytorch`) time-series foundation model.

---

## Featured Study: MODISONLTD (NSE) Zero-Shot Forecasting Evaluation

Located in the [`MODISONANALYSIS/`](MODISONANALYSIS/) directory:

* **Objective**: Evaluate TimesFM 3.0's zero-shot forecasting capabilities on Indian equities (**Modison Limited**, `MODISONLTD.NS` / BSE: `506261`).
* **Cutoff Constraint**: Historical context data strictly up to **August 1, 2026** (Closing price: ₹268.40 on July 31, 2026).
* **Target Horizon**: 23 trading days spanning **August 3, 2026 through September 2, 2026**.
* **Key Findings**:
  * **Pre-Earnings Period (Aug 3 – Aug 13)**: The model demonstrated high baseline zero-shot accuracy with a **7.27% MAPE** (< 5.5% MAPE in the first week) and 100% of actual prices staying within the 80% confidence interval ($P_{10} - P_{90}$).
  * **The Fundamental Catalyst (Aug 13)**: Modison Ltd released blowout Q1 FY27 earnings (Revenue up +101.6% YoY to ₹270.47 Cr, PAT up +604.9% YoY to ₹33.84 Cr), catalyzing a +94% rally to ₹520.65.
  * **ML Boundary Analysis**: Illustrates the empirical boundary between statistical autoregressive foundation modeling and exogenous fundamental corporate announcements.

---

## Repository Contents

```
timesfm-3.0-pytorch/
├── README.md
└── MODISONANALYSIS/
    ├── README.md                           # Comprehensive evaluation report
    ├── timesfm3_modison_analysis.ipynb     # Interactive, fully executed Jupyter Notebook
    ├── timesfm_modison_experiment.py       # Standalone GPU execution script
    ├── timesfm3_forecast_vs_actual.png     # High-resolution benchmark visualization
    ├── timesfm_results.json                # Complete point forecasts, quantiles, and metrics
    └── filings/
        ├── a83fbfdb_q1_results_2026.pdf    # BSE Filing: Q1 FY27 Unaudited Financial Results
        └── fade292d_annual_report_2026.pdf # BSE Filing: Annual Report FY25-26
```

### Getting Started

To run the interactive analysis:
```bash
cd MODISONANALYSIS
jupyter notebook timesfm3_modison_analysis.ipynb
```

Or run the GPU inference script directly:
```bash
python MODISONANALYSIS/timesfm_modison_experiment.py
```

---

## Citations & References
* **TimesFM 3.0**: Google Research ([`google/timesfm-3.0-pytorch`](https://huggingface.co/google/timesfm-3.0-pytorch))
* **TimesFM GitHub**: [google-research/timesfm](https://github.com/google-research/timesfm)
* **Google Research Blog**: [TimesFM 3: A Zero-Shot Foundation Model for Multivariate Forecasting](https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/)
