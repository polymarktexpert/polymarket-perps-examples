# Polymarket Perps Examples

Reference implementations for Polymarket's perpetual futures mechanics, based on the official documentation (docs.polymarket.com/perps).

## Contents

- **`funding_monitor.py`** — tracks the documented funding formula: premium index sampling, the 8-hour rate with its clamp band, and the hourly cap.
- **Live calculator** — https://polymarktexpertaisfang-perps-calculator.static.hf.space/index.html (interactive: IM, MMR, F_8h, hourly funding, withdrawal floor, adverse move to margin call)

## Formulas covered

```
IM  = Notional / Leverage
MMR = 0.5 / MaxLeverage
F_8h = scale * (mean_P + clamp(0.0001 - mean_P, -0.0005, 0.0005))
FR_hour = clamp(F_8h / 8, -0.04, 0.04)    # scale: 1.0 crypto, 0.5 other
Withdrawable = max(0, Collateral + CrossUnrealizedPnL - WithdrawalMarginRequired - PendingOrderMargin)
Floor = max(CollateralReserved, 0.10 * TotalPositionValue)
```

## Writing

Longer explainers: https://polymarkexpert.substack.com/

---

Educational content. Not financial advice.
