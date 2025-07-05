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

today = ql.Date().todaysDate()
calendar = ql.NullCalendar()
dayCounter = ql.Actual365Fixed()
spot = 100
r, q = 0.02, 0.05

spotQuote = ql.QuoteHandle(ql.SimpleQuote(spot))
ratesTs = ql.YieldTermStructureHandle(ql.FlatForward(today, r, dayCounter))
dividendTs = ql.YieldTermStructureHandle(ql.FlatForward(today, q, dayCounter))

# Market options price quotes
optionStrikes = [95, 97.5, 100, 102.5, 105, 90, 95, 100, 105, 110, 80, 90, 100, 110, 120]
optionMaturities = ["3M", "3M", "3M", "3M", "3M", "6M", "6M", "6M", "6M", "6M", "1Y", "1Y", "1Y", "1Y", "1Y"]
optionQuotedVols = [0.11, 0.105, 0.1, 0.095, 0.095, 0.12, 0.11, 0.105, 0.1, 0.105, 0.12, 0.115, 0.11, 0.11, 0.115]

calibrationSet = ql.CalibrationSet()

for strike, expiry, impliedVol in zip(optionStrikes, optionMaturities, optionQuotedVols):
  payoff = ql.PlainVanillaPayoff(ql.Option.Call, strike)
  exercise = ql.EuropeanExercise(calendar.advance(today, ql.Period(expiry)))

  calibrationSet.push_back((ql.VanillaOption(payoff, exercise), ql.SimpleQuote(impliedVol)))

ahInterpolation = ql.AndreasenHugeVolatilityInterpl(calibrationSet, spotQuote, ratesTs, dividendTs)
ahLocalSurface = ql.AndreasenHugeLocalVolAdapter(ahInterpolation)
ts = ql.BlackVolTermStructureHandle(ahLocalSurface)
print(f'ahLocalSurface: \n{ahLocalSurface}')