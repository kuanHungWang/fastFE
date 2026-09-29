import numpy as np
import pytest
import QuantLib as ql

from fastFE.models import BlackScholesMertonModel, GarmanKohlagenProcessModel

TODAY = ql.Date(15, 6, 2024)
DC = ql.Actual365Fixed()
R, Q, S0 = 0.03, 0.01, 100.0
N_PATHS = 100_000


@pytest.fixture(autouse=True)
def eval_date():
    ql.Settings.instance().evaluationDate = TODAY


def _curves():
    return (ql.YieldTermStructureHandle(ql.FlatForward(TODAY, R, DC)),
            ql.YieldTermStructureHandle(ql.FlatForward(TODAY, Q, DC)))


def _surface():
    expiries = [TODAY + ql.Period(p) for p in ['3M', '6M', '1Y', '2Y']]
    strikes = [50.0, 70.0, 85.0, 100.0, 115.0, 130.0, 160.0]
    vols = ql.Matrix(len(strikes), len(expiries))
    for i, k in enumerate(strikes):
        for j in range(len(expiries)):  # mild smooth smile, arbitrage free, so local vol stays well behaved
            vols[i][j] = 0.2 + 0.04 * ((k - 100) / 100) ** 2 - 0.02 * (k - 100) / 100 + 0.005 * j
    surf = ql.BlackVarianceSurface(TODAY, ql.NullCalendar(), expiries, strikes, vols, DC)
    surf.enableExtrapolation()
    return ql.BlackVolTermStructureHandle(surf)


def _flat_vol():
    return ql.BlackVolTermStructureHandle(ql.BlackConstantVol(TODAY, ql.NullCalendar(), 0.25, DC))


def _models(vol):
    r, q = _curves()
    return {'bsm': BlackScholesMertonModel(r, q, vol, S0),
            'gk': GarmanKohlagenProcessModel(q, r, vol, S0)}  # foreign=q, domestic=r


SCHEDULE = ql.MakeSchedule(TODAY, TODAY + ql.Period('2Y'), ql.Period('1M'))


@pytest.mark.parametrize('vol_factory', [_surface, _flat_vol], ids=['local_vol', 'constant_vol'])
@pytest.mark.parametrize('kind', ['bsm', 'gk'])
def test_mean_matches_forward_each_date(vol_factory, kind):
    """Under the risk-neutral measure E[S_t] = S0 * exp((r - q) t) at every date (martingale property)."""
    df = _models(vol_factory())[kind].monte_carlo_paths(SCHEDULE, N_PATHS, seed=7)
    t = np.array([DC.yearFraction(TODAY, d) for d in SCHEDULE])
    forward = S0 * np.exp((R - Q) * t)
    se = df.std(axis=1, ddof=1).to_numpy() / np.sqrt(N_PATHS)
    z = (df.mean(axis=1).to_numpy() - forward)[1:] / se[1:]
    assert np.abs(z).max() < 4.5, z


def test_local_vol_call_price_matches_black():
    """Dupire local vol reproduces the vanilla prices of the surface it is built from."""
    r, q = _curves()
    vol = _surface()
    df = BlackScholesMertonModel(r, q, vol, S0).monte_carlo_paths(SCHEDULE, 200_000, seed=3)
    T = DC.yearFraction(TODAY, SCHEDULE[len(SCHEDULE) - 1])
    strike = 100.0
    payoff = np.maximum(df.iloc[-1].to_numpy() - strike, 0.0) * np.exp(-R * T)
    mc, se = payoff.mean(), payoff.std(ddof=1) / np.sqrt(len(payoff))
    black = ql.blackFormula(ql.Option.Call, strike, S0 * np.exp((R - Q) * T), vol.blackVol(T, strike) * np.sqrt(T),
                            np.exp(-R * T))
    assert abs(mc - black) < 4 * se + 0.1, (mc, black, se)


def test_output_contract_and_seed():
    model = _models(_surface())['bsm']
    a = model.monte_carlo_paths(SCHEDULE, 50, seed=5)
    b = model.monte_carlo_paths(SCHEDULE, 50, seed=5)
    c = model.monte_carlo_paths(SCHEDULE, 50, seed=6)
    assert a.shape == (len(SCHEDULE), 50)
    assert list(a.index) == [d for d in SCHEDULE]
    assert (a.iloc[0] == S0).all()
    assert (a.to_numpy() > 0).all()
    assert a.equals(b)
    assert not a.equals(c)
