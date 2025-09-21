import numpy as np
import pandas as pd
import QuantLib as ql

s = pd.Series(index=[1,2,3,4,5], data=True)
print(s)
s.iloc[0] = False
s.iloc[-1] = False
print(s)

