import QuantLib as ql
import numpy as np
import pandas as pd
from util import year_fraction
sigma = 0.2
today = ql.Date().todaysDate()
initialValue = ql.QuoteHandle(ql.SimpleQuote(100))
domesticRiskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.03, ql.Actual365Fixed()))
foreignRiskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, ql.Actual365Fixed()))

# 1. Constant Volatility
volTS = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), sigma, ql.Actual365Fixed()))
process = ql.GarmanKohlagenProcess(initialValue, foreignRiskFreeTS, domesticRiskFreeTS, volTS)

# 2. Volatility Curve
expirations = [today+ql.Period(tenor) for tenor in ['1M', '6M', '9M', '1Y']]
volatilities = [.145, .156, .165, .175]
volatilityCurve = ql.BlackVarianceCurve(today, expirations, volatilities, ql.Actual360())
volatilityCurve.enableExtrapolation()
volTS = ql.BlackVolTermStructureHandle(volatilityCurve)
process = ql.GarmanKohlagenProcess(initialValue, foreignRiskFreeTS, domesticRiskFreeTS, volTS)


# 3. Volatility Surface (local volatility)

strikes = [50.0, 100.0, 110.0]
expirations = ['1M', '6M', '9M', '1Y']
df=pd.DataFrame(index=strikes, columns=expirations)
df.values.fill(0.2)
print(df)

volMatrix = ql.Matrix(len(strikes), len(expirations))
expirations = [today+ql.Period(tenor) for tenor in df.columns]
for i, strike in enumerate(strikes):
    for j, expiration in enumerate(expirations):
        volMatrix[i][j] = df.iloc[i,j]
volatilitySurface = ql.BlackVarianceSurface(today, ql.WeekendsOnly(), expirations, strikes, volMatrix, ql.Business252())
volTS = ql.BlackVolTermStructureHandle(volatilitySurface)
process = ql.GarmanKohlagenProcess(initialValue, foreignRiskFreeTS, domesticRiskFreeTS, volTS)



# 4. Monte Carlo
schedule = ql.MakeSchedule(today, today+ql.Period('1Y'), ql.Period('1M'))
time_grid = year_fraction(schedule, ql.Actual360(), accoumulative=True)
n_steps = len(schedule) - 1
dimension = process.factors()
rng = ql.UniformRandomSequenceGenerator(dimension * n_steps, ql.UniformRandomGenerator())
sequenceGenerator = ql.GaussianRandomSequenceGenerator(rng)
pathGenerator = ql.GaussianMultiPathGenerator(process, time_grid, sequenceGenerator, False)


samplePath = pathGenerator.next()