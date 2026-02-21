# fastquant

A Python library that simplifies [QuantLib](https://www.quantlib.org/) for pricing exotic derivatives. It provides high-level abstractions for yield curve bootstrapping, volatility surface construction, financial model calibration, and Monte Carlo simulation — so you can focus on the economics of a trade rather than QuantLib's low-level API.

## Features

- **Curve bootstrapping** — build yield curves from deposits, swaps, OIS, FRAs, bonds, and SOFR futures for USD, EUR, JPY, TWD, CHF, and GBP with a single function call
- **Volatility surfaces** — construct 1D vol curves and 2D vol surfaces; create calibration helpers for swaptions and Heston models
- **Financial models** — Hull-White (interest rate), Heston (stochastic vol equity), Black-Scholes-Merton (equity/FX), Garman-Kohlhagen (FX), and multi-asset correlation models
- **Monte Carlo paths** — all models expose a uniform `monte_carlo_paths()` interface returning pandas DataFrames indexed by `ql.Date`
- **Longstaff-Schwartz** — built-in LSM engine for Bermudan and American-style early-exercise products
- **Market conventions** — pre-defined fixed and floating leg conventions for major currencies via `Conventions`
- **Schedule utilities** — helpers for combining schedules, computing year fractions, and resolving fixing dates

## Installation

```bash
pip install fastquant
```

QuantLib must be installed separately (see [QuantLib-Python installation guide](https://github.com/lballabio/QuantLib)):

```bash
pip install QuantLib
```

## Quick Start

### Build a yield curve

```python
import QuantLib as ql
import pandas as pd
from fastquant import bootstrap_curve

today = ql.Date().todaysDate()

df_deposit = pd.DataFrame({
    'tenor': ['1M', '2M', '3M', '6M', '9M'],
    'rates': [0.015, 0.018, 0.02, 0.022, 0.025]
})
df_swap = pd.DataFrame({
    'tenor': ['1Y', '2Y', '5Y', '7Y', '10Y'],
    'rate':  [0.015, 0.018, 0.02, 0.022, 0.025]
})

curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)
print(curve.discount(today + ql.Period('1Y')))
```

`bootstrap_curve` automatically applies the correct market conventions for the currency inferred from the helpers. Pass `currency='EUR'` to override.

See [`examples/examples.py`](examples/examples.py) for a complete reference of all rate helper types (OIS, FRA, bond, SOFR futures).

---

### Construct a volatility surface

```python
import QuantLib as ql
import pandas as pd
from fastquant import create_black_vol_curve, create_black_vol_surface

today = ql.Date().todaysDate()

# 1D vol curve
vol_series = pd.Series(
    [0.15, 0.18, 0.20, 0.22, 0.25],
    index=['1M', '2M', '3M', '6M', '9M']
)
vol_curve = create_black_vol_curve(vol_series, today)

# 2D vol surface (rows = expiry tenors, columns = strikes)
vol_df = pd.DataFrame(
    [[0.20, 0.22, 0.24],
     [0.21, 0.23, 0.25],
     [0.22, 0.24, 0.26]],
    index=['1M', '3M', '6M'],
    columns=[90.0, 100.0, 110.0]
)
vol_surface = create_black_vol_surface(vol_df, today)
```

---

### Price an equity derivative with Black-Scholes-Merton

```python
import QuantLib as ql
from fastquant import BlackScholesMertonModel, create_black_vol_curve

today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
calendar = ql.WeekendsOnly()
spot = 100.0

risk_free = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))
dividend  = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, dayCount))

vol_curve = create_black_vol_curve(
    pd.Series([0.20, 0.21, 0.22, 0.23], index=['3M', '6M', '9M', '1Y']),
    today
)

model = BlackScholesMertonModel(risk_free, dividend, vol_curve, spot)

fixing_schedule = ql.MakeSchedule(
    today, today + ql.Period('1Y'), ql.Period('1M'), calendar=calendar
)
paths = model.monte_carlo_paths(fixing_schedule, numPaths=1000)
# paths: pd.DataFrame, shape (len(fixing_schedule), 1000)
```

See [`examples/equity_link_example.py`](examples/equity_link_example.py) for a complete equity-linked structured product (Heston model, Bermudan knock-out, European knock-in, auto-call).

---

### Price an FX derivative with Garman-Kohlhagen

```python
import QuantLib as ql
from fastquant import GarmanKohlagenProcessModel, create_black_vol_surface

today = ql.Date().todaysDate()
dayCount = ql.Actual365Fixed()
spot = 1.10  # EURUSD

domestic = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.04, dayCount))
foreign  = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.02, dayCount))

# vol_surface: see "Construct a volatility surface" above
fx_model = GarmanKohlagenProcessModel(domestic, foreign, vol_surface, spot)

daily_schedule = ql.MakeSchedule(
    today, today + ql.Period('1Y'), ql.Period('1D'), calendar=ql.WeekendsOnly()
)
fx_paths = fx_model.monte_carlo_paths(daily_schedule, numPaths=1000)
```

See [`examples/fx_linked_example.py`](examples/fx_linked_example.py) for an FX range accrual note, and [`examples/target_redemption_example.py`](examples/target_redemption_example.py) for a Target Redemption Forward (TRF).

---

### Price an interest rate derivative with Hull-White

```python
import QuantLib as ql
import pandas as pd
from fastquant import HullWhiteModel, bootstrap_curve

today = ql.Date().todaysDate()
ql.Settings.instance().evaluationDate = today

curve = bootstrap_curve(today, deposit=df_deposit, swap=df_swap)

hw_model = HullWhiteModel(today, curve)
hw_model.calibrate(df_swaption)  # df_swaption: DataFrame with maturity, length, volatility

def create_libor_6M(ts):
    return ql.IborIndex(
        'Libor6M', ql.Period('6M'), 2, ql.USDCurrency(),
        ql.UnitedStates(ql.UnitedStates.Settlement),
        ql.ModifiedFollowing, True, ql.Thirty360(ql.Thirty360.USA), ts
    )

underlying_path, fixings, discount_factors = hw_model.monte_carlo_paths(
    index_factories={'libor_6M': create_libor_6M},
    fixingSchedule=fixing_schedule,
    paymentSchedule=payment_schedule,
    numPaths=1000
)
libor_fixings = fixings['libor_6M']  # pd.DataFrame
```

See [`examples/irs_examle.py`](examples/irs_examle.py) for a cancellable Libor IRS, [`examples/sofr_irs_example.py`](examples/sofr_irs_example.py) for a cancellable SOFR IRS with daily compounding, and [`examples/ir_linked_example.py`](examples/ir_linked_example.py) for a CMS spread cancellable IRS.

---

### Bermudan / American optionality with Longstaff-Schwartz

```python
import numpy as np
import pandas as pd
from fastquant import LongstaffSchwartz, subset_to_bool

# cashflows: pd.DataFrame (payment_dates x paths)
# discount_factors: pd.DataFrame (payment_dates x 1)
# exercise_payoff: callable, receives array of path values, returns cashflow array

exercisable = subset_to_bool(exercise_dates, cashflows.index)

lsm = LongstaffSchwartz(
    cashflows=cashflows,
    discountFactors=discount_factors,
    exercisable=exercisable,
    exercise_payoff=lambda x: np.zeros(len(x)),
    observable=libor_fixings
)

lsm.backward_induction()
print(lsm.confidence_interval())       # (lower, upper) at 95%
print(lsm.survival_probability())      # probability of not exercising early
print(lsm.exercise_cashflows())        # expected cashflows from early exercise
print(lsm.exercise_mask())             # bool DataFrame: exercise decision per path
```

See [`examples/examples.py`](examples/examples.py) for a standalone LSM example with mock data.

---

### Multi-asset Monte Carlo

```python
from fastquant import MultiAssetModel

corr_matrix = [[1.0, 0.6], [0.6, 1.0]]

# Combine a BSM equity process and a GK FX process
multi_model = MultiAssetModel(
    processes=[equity_model.process, fx_model.process],
    corrMatrix=corr_matrix
)

fixings = multi_model.monte_carlo_paths(fixing_schedule, numPaths=1000)
equity_paths = fixings[0]   # pd.DataFrame
fx_paths     = fixings[1]   # pd.DataFrame
```

See [`examples/multi_stock_examle.py`](examples/multi_stock_examle.py) for a multi-asset example.

---

### Market conventions

`Conventions` provides pre-built fixed and floating leg convention dictionaries for USD, EUR, JPY, TWD, CHF, and GBP, ready to pass directly into rate helper constructors.

```python
from fastquant import Conventions, create_deposit_rate_helpers, create_swap_rate_helpers

deposit_helpers = create_deposit_rate_helpers(df_deposit, Conventions.USFixedLegConventions())
swap_helpers    = create_swap_rate_helpers(
    df_swap,
    fixed_leg_conventions=Conventions.USFixedLegConventions(),
    floating_leg_conventions=Conventions.USFloatingLegConventions()
)
```

---

## Examples

| File | Description |
|------|-------------|
| [`examples/examples.py`](examples/examples.py) | Comprehensive reference — dates, schedules, all rate helpers, all model types, LSM |
| [`examples/irs_examle.py`](examples/irs_examle.py) | Cancellable fixed-vs-Libor IRS using Hull-White + LSM |
| [`examples/sofr_irs_example.py`](examples/sofr_irs_example.py) | Cancellable fixed-vs-SOFR IRS with daily compounding |
| [`examples/ir_linked_example.py`](examples/ir_linked_example.py) | CMS 5Y-2Y spread cancellable IRS (Hull-White + LSM) |
| [`examples/equity_link_example.py`](examples/equity_link_example.py) | Equity-linked note with Heston model, knock-out, knock-in, auto-call |
| [`examples/fx_linked_example.py`](examples/fx_linked_example.py) | FX daily range accrual note (Garman-Kohlhagen) |
| [`examples/target_redemption_example.py`](examples/target_redemption_example.py) | Target Redemption Forward (TRF) in EURUSD |
| [`examples/multi_stock_examle.py`](examples/multi_stock_examle.py) | Multi-asset correlated Monte Carlo |

## API Reference

### `bootstrap_curve(today, *, deposit=None, swap=None, OIS=None, fra=None, bond=None, sofr=None, currency='USD')`

Bootstraps a yield curve from any combination of instrument DataFrames. Returns a `ql.YieldTermStructureHandle`.

### `HullWhiteModel(today, curve)`

Interest rate model. Call `.calibrate(df_swaption)` to fit to market swaptions, then `.monte_carlo_paths(index_factories, fixingSchedule, paymentSchedule, numPaths)` to generate short-rate paths and index fixings.

### `HestonModel(risk_free_curve, dividend_curve, calendar)`

Stochastic volatility equity model. Call `.calibrate(vol_df, spot)`, then `.monte_carlo_paths(schedule, numPaths)`.

### `BlackScholesMertonModel(risk_free_curve, dividend_curve, vol, spot)`

Equity/index model. Accepts constant vol, vol curve, or vol surface. Call `.monte_carlo_paths(schedule, numPaths)`.

### `GarmanKohlagenProcessModel(domestic_curve, foreign_curve, vol, spot)`

FX model. Same vol options and `monte_carlo_paths` interface as BSM.

### `MultiAssetModel(processes, corrMatrix)`

Combines multiple GBM processes with a correlation matrix. Returns a list of DataFrames from `.monte_carlo_paths(schedule, numPaths)`.

### `LongstaffSchwartz(cashflows, discountFactors, exercisable, exercise_payoff, observable)`

Longstaff-Schwartz LSM engine. Call `.backward_induction()` first, then access `.valuations()`, `.confidence_interval()`, `.survival_probability()`, `.exercise_cashflows()`, `.exercise_mask()`.

### `Conventions`

Class with class methods: `USFixedLegConventions()`, `USFloatingLegConventions()`, `EURFixedLegConventions()`, `EURFloatingLegConventions()`, `JPYFixedLegConventions()`, `JPYFloatingLegConventions()`, and equivalents for TWD, CHF, GBP.

## Requirements

- Python >= 3.9
- QuantLib >= 1.32
- pandas >= 1.5
- numpy >= 1.23
- scikit-learn >= 1.2

## License

MIT
