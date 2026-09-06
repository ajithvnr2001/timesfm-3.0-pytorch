"""
timesfm3_adapter.py
===================
Hard-fail adapter around the real Google TimesFM 3.0 PyTorch checkpoint.

Design rules (learned from auditing the previous engine):
  * There is NO silent heuristic fallback. If the foundation model cannot be loaded,
    `TimesFMUnavailable` is raised. A run either used the neural model or it did not exist.
  * Every forecast carries provenance: model id, device, context length actually used,
    covariate counts, target count, and the number of neural points returned.
  * The model's own 9 quantiles are the source of uncertainty. Nothing is substituted
    from historical volatility.
  * Shapes are validated against the contract verified on a T4 (see TIMESFM3_API.md):
    context (T,) or (V,T); past_only_covariates (k,T); past_future_covariates (k,T+H);
    quantiles [H,9] or [V,H,9] with index 0 = q10 ... 4 = median ... 8 = q90.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

Q10_IDX, MEDIAN_IDX, Q90_IDX = 0, 4, 8
N_QUANTILES = 9
MODEL_ID = "google/timesfm-3.0-pytorch"


class TimesFMUnavailable(RuntimeError):
    """Raised when the real TimesFM 3.0 checkpoint cannot be loaded or used."""


class ForecastContractError(RuntimeError):
    """Raised when the model returns tensors that violate the verified contract."""


@dataclass
class ForecastResult:
    """Neural forecast for the primary target plus provenance."""

    point: np.ndarray  # (H,) median/point path for target 0
    quantiles: np.ndarray  # (H, 9) q10..q90 for target 0
    aux_points: dict = field(default_factory=dict)  # other target name -> (H,)
    provenance: dict = field(default_factory=dict)

    @property
    def q10(self) -> np.ndarray:
        return self.quantiles[:, Q10_IDX]

    @property
    def q90(self) -> np.ndarray:
        return self.quantiles[:, Q90_IDX]

    @property
    def median(self) -> np.ndarray:
        return self.quantiles[:, MEDIAN_IDX]


class TimesFM3Adapter:
    """Thin, strict wrapper over timesfm.TimesFM3Forecaster."""

    def __init__(self, device: str = "cuda", model_id: str = MODEL_ID):
        self.device = device
        self.model_id = model_id
        self._fc = None
        self.load_seconds: Optional[float] = None

    # ---------------------------------------------------------------- loading
    def load(self) -> "TimesFM3Adapter":
        if self._fc is not None:
            return self
        try:
            import timesfm  # noqa: WPS433 (runtime import is intentional)
        except Exception as exc:  # pragma: no cover - environment dependent
            raise TimesFMUnavailable(
                f"timesfm package not importable ({type(exc).__name__}: {exc}). "
                "Install with: pip install git+https://github.com/google-research/timesfm.git"
            ) from exc

        if not hasattr(timesfm, "TimesFM3Forecaster"):
            raise TimesFMUnavailable(
                "installed timesfm exposes no TimesFM3Forecaster; "
                f"available symbols: {[s for s in dir(timesfm) if not s.startswith('_')]}"
            )

        t0 = time.time()
        try:
            self._fc = timesfm.TimesFM3Forecaster.from_pretrained(self.model_id, device=self.device)
        except Exception as exc:
            raise TimesFMUnavailable(
                f"failed to load {self.model_id} on {self.device}: {type(exc).__name__}: {exc}"
            ) from exc
        self.load_seconds = round(time.time() - t0, 2)
        return self

    @property
    def is_loaded(self) -> bool:
        return self._fc is not None

    # -------------------------------------------------------------- inference
    def predict(
        self,
        context: np.ndarray,
        horizon: int,
        past_covariates: Optional[np.ndarray] = None,
        past_future_covariates: Optional[np.ndarray] = None,
        target_names: Optional[list] = None,
        scale_targets: bool = True,
        ts_id: Optional[str] = None,
    ) -> ForecastResult:
        """Run one forward pass.

        Args:
            context: (T,) univariate or (V, T) multivariate. Target 0 is the asset of interest.
            horizon: number of steps to forecast in a single pass.
            past_covariates: (k, T) matrix of covariates observed only up to the cutoff.
            past_future_covariates: (k, T + horizon) matrix known for the future too
                (calendar features only - anything else would leak).
            target_names: labels for the V variates, used for aux output keys.
            scale_targets: divide each variate by its own last observed value so the model
                sees comparable magnitudes across targets; inverted after inference.
                This is a per-variate affine transform and cannot leak information.
            ts_id: opaque id passed through to the model (never the real ticker).
        """
        if self._fc is None:
            raise TimesFMUnavailable("adapter.load() must be called before predict()")
        if horizon < 1:
            raise ValueError("horizon must be >= 1")

        ctx = np.asarray(context, dtype=np.float32)
        if ctx.ndim == 1:
            ctx = ctx[None, :]
        if ctx.ndim != 2:
            raise ValueError(f"context must be (T,) or (V, T); got {ctx.shape}")
        n_targets, ctx_len = ctx.shape
        if ctx_len < 32:
            raise ValueError(f"context too short for TimesFM ({ctx_len} points)")
        if not np.all(np.isfinite(ctx)):
            raise ValueError("context contains non-finite values")

        # Per-variate scaling (affine, invertible, no cross-variate information flow).
        if scale_targets:
            anchors = ctx[:, -1].copy()
            if np.any(anchors == 0):
                raise ValueError("cannot scale targets: a variate ends at zero")
            ctx_in = ctx / anchors[:, None]
        else:
            anchors = np.ones(n_targets, dtype=np.float32)
            ctx_in = ctx

        poc = self._check_cov(past_covariates, ctx_len, "past_covariates")
        pfc = self._check_cov(past_future_covariates, ctx_len + horizon, "past_future_covariates")

        t0 = time.time()
        out = self._fc.predict(
            context=ctx_in[0] if n_targets == 1 else ctx_in,
            horizon=horizon,
            past_only_covariates=poc,
            past_future_covariates=pfc,
            ts_id=ts_id,
            return_quantiles=True,
            sort_quantiles=True,
        )
        predict_seconds = round(time.time() - t0, 3)

        forecast = np.asarray(out.forecast, dtype=np.float64)
        quantiles = np.asarray(out.quantiles, dtype=np.float64)

        # Normalise shapes to (V, H) and (V, H, 9)
        if n_targets == 1:
            forecast = forecast.reshape(1, -1)
            quantiles = quantiles.reshape(1, forecast.shape[1], -1)
        if forecast.shape != (n_targets, horizon):
            raise ForecastContractError(
                f"expected forecast {(n_targets, horizon)}, got {forecast.shape}"
            )
        if quantiles.shape != (n_targets, horizon, N_QUANTILES):
            raise ForecastContractError(
                f"expected quantiles {(n_targets, horizon, N_QUANTILES)}, got {quantiles.shape}"
            )
        if not np.all(np.isfinite(forecast)) or not np.all(np.isfinite(quantiles)):
            raise ForecastContractError("model returned non-finite values")
        if np.any(np.diff(quantiles, axis=-1) < -1e-4):
            raise ForecastContractError("quantiles are not monotone despite sort_quantiles=True")

        # Invert scaling
        forecast = forecast * anchors[:, None]
        quantiles = quantiles * anchors[:, None, None]

        names = list(target_names) if target_names else [f"target_{i}" for i in range(n_targets)]
        aux = {names[i]: forecast[i] for i in range(1, n_targets)}

        return ForecastResult(
            point=forecast[0],
            quantiles=quantiles[0],
            aux_points=aux,
            provenance={
                "model_id": self.model_id,
                "device": self.device,
                "load_seconds": self.load_seconds,
                "predict_seconds": predict_seconds,
                "context_length": int(ctx_len),
                "n_targets": int(n_targets),
                "target_names": names,
                "n_past_covariates": 0 if poc is None else int(poc.shape[0]),
                "n_past_future_covariates": 0 if pfc is None else int(pfc.shape[0]),
                "neural_points": int(horizon),
                "extrapolated_points": 0,
                "scaled_targets": bool(scale_targets),
                "quantile_layout": "index0=q10 ... index4=median ... index8=q90",
            },
        )

    @staticmethod
    def _check_cov(cov: Optional[np.ndarray], expected_len: int, label: str):
        if cov is None:
            return None
        arr = np.asarray(cov, dtype=np.float32)
        if arr.ndim != 2:
            raise ValueError(f"{label} must be 2-D (k, {expected_len}); got {arr.shape}")
        if arr.shape[1] != expected_len:
            raise ValueError(
                f"{label} must be (k, {expected_len}) per the verified TimesFM 3.0 contract; "
                f"got {arr.shape}. Note: (T, k) is silently wrong - transpose it."
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{label} contains non-finite values")
        return arr
