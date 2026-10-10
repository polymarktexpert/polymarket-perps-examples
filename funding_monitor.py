"""
Polymarket Perps — funding rate reference monitor.
Based on the official Perps documentation (docs.polymarket.com/perps), October 2026.

The funding pipeline in three stages:
  1. Premium index sampled every 5 seconds from impact bid/ask vs index.
  2. Samples averaged over a 1-hour charge window into an 8-hour rate:
       F_8h = scale * (mean_P + clamp(0.0001 - mean_P, -0.0005, +0.0005))
     scale = 1.0 for crypto markets, 0.5 for stocks/indices/commodities.
  3. Hourly payment = clamp(F_8h / 8, -0.04, +0.04), capped at 4% per hour.

This module implements the pure math so you can feed it your own samples
from the Data API and model the next payment before it lands.
"""

from dataclasses import dataclass
from typing import Iterable


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class FundingParams:
    baseline: float = 0.0001        # 0.01%
    clamp_band: float = 0.0005      # ±0.05% adjustment band
    scale: float = 1.0              # 1.0 crypto, 0.5 otherwise
    hours_window: float = 8.0
    hourly_cap: float = 0.04        # ±4% per hour


def premium_index(index_price: float, bid_impact: float, ask_impact: float) -> float:
    """Stage 1. Positive when the perp trades rich vs the index."""
    ipd = max(bid_impact - index_price, 0.0) - max(index_price - ask_impact, 0.0)
    if index_price <= 0:
        raise ValueError("index_price must be positive")
    return ipd / index_price


def eight_hour_rate(mean_premium: float, params: FundingParams = FundingParams()) -> float:
    """Stage 2. mean_premium is the average of stage-1 samples over the charge window."""
    adjustment = clamp(params.baseline - mean_premium, -params.clamp_band, params.clamp_band)
    return params.scale * (mean_premium + adjustment)


def hourly_payment(f_8h: float, params: FundingParams = FundingParams()) -> float:
    """Stage 3. Positive = longs pay shorts, negative = shorts pay longs."""
    return clamp(f_8h / params.hours_window, -params.hourly_cap, params.hourly_cap)


def payment_on_notional(notional: float, hourly_rate: float) -> float:
    """Dollars per hour exchanged between long and short sides for a given notional."""
    return notional * hourly_rate


def project_cost(notional: float, premium_samples: Iterable[float],
                 params: FundingParams = FundingParams()) -> dict:
    """Feed recent premium samples; get the projected hourly payment."""
    samples = list(premium_samples)
    if not samples:
        raise ValueError("need at least one premium sample")
    mean_p = sum(samples) / len(samples)
    f_8h = eight_hour_rate(mean_p, params)
    fr = hourly_payment(f_8h, params)
    return {
        "mean_premium": mean_p,
        "f_8h": f_8h,
        "hourly_rate": fr,
        "hourly_cost_on_notional": payment_on_notional(notional, fr),
        "daily_cost_on_notional": payment_on_notional(notional, fr) * 24,
    }


if __name__ == "__main__":
    # Example: BTC perp holding 0.3% above the index through the window.
    example = project_cost(notional=10_000, premium_samples=[0.003] * 12)
    for key, val in example.items():
        print(f"{key}: {val:.6f}")
    # Expected: f_8h = 0.0025 (0.25% / 8h), hourly ~0.031%, ~$3.10/hour on $10k.
