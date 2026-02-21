"""
fastquant - A Python library that simplifies QuantLib for pricing exotic derivatives.

Modules
-------
curve_builder
    Bootstrap yield curves from market instruments for major currencies.
rate_helpers
    Create QuantLib rate helper objects (deposits, swaps, OIS, FRAs, bonds, SOFR futures).
vol_helper
    Construct volatility curves and surfaces; create calibration helpers.
models
    Financial models: HullWhiteModel, HestonModel, BlackScholesMertonModel,
    GarmanKohlagenProcessModel, MultiAssetModel.
conventions
    Pre-defined market conventions for USD, EUR, JPY, TWD, CHF, GBP.
leastSquareError
    Longstaff-Schwartz algorithm for Bermudan / American-style optionality.
util
    Date, schedule, and year-fraction utilities.
market_data
    Mock market data helpers for development and testing.
"""

from fastquant.curve_builder import bootstrap_curve, bootstrap_curve_with_instrument_helpers
from fastquant.rate_helpers import (
    create_deposit_rate_helpers,
    create_swap_rate_helpers,
    create_fra_rate_helpers,
    create_OIS_helper,
    create_bond_helper,
    create_sofr_future_rate_helpers,
)
from fastquant.vol_helper import (
    create_black_vol_curve,
    create_black_vol_surface,
    create_swaption_helper,
    create_heston_model_helper,
)
from fastquant.models import (
    HullWhiteModel,
    HestonModel,
    BlackScholesMertonModel,
    GarmanKohlagenProcessModel,
    MultiAssetModel,
)
from fastquant.conventions import Conventions
from fastquant.leastSquareError import LongstaffSchwartz
from fastquant.util import (
    year_fraction,
    combine_schedule,
    subset_to_bool,
    get_nearest_fixing_date,
    leg_to_series,
)

__version__ = "0.1.0"
__all__ = [
    # curve building
    "bootstrap_curve",
    "bootstrap_curve_with_instrument_helpers",
    # rate helpers
    "create_deposit_rate_helpers",
    "create_swap_rate_helpers",
    "create_fra_rate_helpers",
    "create_OIS_helper",
    "create_bond_helper",
    "create_sofr_future_rate_helpers",
    # vol helpers
    "create_black_vol_curve",
    "create_black_vol_surface",
    "create_swaption_helper",
    "create_heston_model_helper",
    # models
    "HullWhiteModel",
    "HestonModel",
    "BlackScholesMertonModel",
    "GarmanKohlagenProcessModel",
    "MultiAssetModel",
    # conventions
    "Conventions",
    # LSM
    "LongstaffSchwartz",
    # utilities
    "year_fraction",
    "combine_schedule",
    "subset_to_bool",
    "get_nearest_fixing_date",
    "leg_to_series",
]
