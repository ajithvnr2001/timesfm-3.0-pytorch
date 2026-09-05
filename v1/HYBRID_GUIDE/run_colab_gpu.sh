#!/usr/bin/env bash
# ==============================================================================
# run_colab_gpu.sh
# ==============================================================================
# One-Click Colab Cloud GPU Provisioning, Execution, Artifact Download & Teardown
# for Google TimesFM 3.0 Hybrid Financial Forecasting.
#
# Usage:
#   ./run_colab_gpu.sh --tickers MODISONLTD.NS,CUPID.NS --mode live --gpu T4
# ==============================================================================

set -e

# Default Arguments
AUTH_MODE="adc"
GPU_TYPE="T4"
SESSION_NAME="timesfm-gpu-$RANDOM"
TICKERS="MODISONLTD.NS,CUPID.NS"
MODE="live"
HORIZON="14"
SCENARIO="HYBRID_GUIDE/sample_scenario.json"
OUTPUT_DIR="./colab_results"

# Parse CLI Flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --auth) AUTH_MODE="$2"; shift ;;
        --gpu) GPU_TYPE="$2"; shift ;;
        --tickers) TICKERS="$2"; shift ;;
        --mode) MODE="$2"; shift ;;
        --horizon) HORIZON="$2"; shift ;;
        --scenario) SCENARIO="$2"; shift ;;
        --output_dir) OUTPUT_DIR="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "================================================================="
echo " GOOGLE COLAB CLOUD GPU RUNNER FOR TIMESFM 3.0"
echo " Session:  $SESSION_NAME"
echo " GPU Type: $GPU_TYPE"
echo " Auth:     --auth=$AUTH_MODE"
echo " Tickers:  $TICKERS"
echo " Mode:     $MODE"
echo " Horizon:  $HORIZON days"
echo "================================================================="

# Trap to guarantee session cleanup on exit or error
cleanup() {
    echo ""
    echo "[Teardown] Stopping Colab GPU session $SESSION_NAME..."
    colab --auth="$AUTH_MODE" stop -s "$SESSION_NAME" || true
    echo "[Teardown] Done! Compute units conserved."
}
trap cleanup EXIT

# 1. Provision Cloud GPU VM
echo ""
echo "[1/5] Launching Cloud GPU Session ($GPU_TYPE)..."
colab --auth="$AUTH_MODE" new -s "$SESSION_NAME" --gpu "$GPU_TYPE"

# 2. Install Dependencies
echo ""
echo "[2/5] Installing TimesFM 3.0 and quantitative libraries on GPU VM..."
colab --auth="$AUTH_MODE" install -s "$SESSION_NAME" \
  git+https://github.com/google-research/timesfm.git yfinance exa-py pypdf matplotlib pandas numpy

# 3. Upload Local Code and Scenarios
echo ""
echo "[3/5] Uploading HYBRID_GUIDE assets to remote VM..."
colab --auth="$AUTH_MODE" upload -s "$SESSION_NAME" HYBRID_GUIDE/ /content/HYBRID_GUIDE/

# 4. Execute Hybrid Inference on GPU
echo ""
echo "[4/5] Executing TimesFM 3.0 with CUDA GPU Acceleration..."
REMOTE_CMD="python3 /content/HYBRID_GUIDE/hybrid_agentic_pipeline.py \
  --mode $MODE \
  --tickers $TICKERS \
  --scenario /content/$SCENARIO \
  --horizon $HORIZON \
  --output_dir /content/colab_output"

colab --auth="$AUTH_MODE" exec -s "$SESSION_NAME" "$REMOTE_CMD"

# 5. Download Artifacts Back to Local Workspace
echo ""
echo "[5/5] Downloading forecast charts and JSON records to $OUTPUT_DIR..."
mkdir -p "$OUTPUT_DIR"
colab --auth="$AUTH_MODE" download -s "$SESSION_NAME" /content/colab_output/ "$OUTPUT_DIR/"

echo ""
echo "================================================================="
echo " EXECUTION COMPLETE! Artifacts saved to: $OUTPUT_DIR"
echo "================================================================="
