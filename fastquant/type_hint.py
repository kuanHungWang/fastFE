from typing import Literal, List, Dict, Optional, Tuple, Callable, TypeAlias, ParamSpec
import QuantLib as ql
import pandas as pd


import numpy as np

# typeAlias
IndexFactory: TypeAlias = Callable[[ql.YieldTermStructureHandle], ql.Index]
Schedule: TypeAlias = Literal[List[ql.Date], ql.Schedule]
ExercisePayoff: TypeAlias = Callable[[np.ndarray], np.ndarray]
Exercisable: TypeAlias =pd.Series
Series: TypeAlias = Literal[pd.Series, pd.DataFrame]

# node definition ,all output is dict[str, ], and usually end with Creator
ScheduleCreator: TypeAlias = Callable[..., Dict[str, Schedule]]
CurveCreator: TypeAlias = Callable[..., Dict[str, ql.YieldTermStructureHandle]]
IndexFactoriesCreator: TypeAlias = Callable[..., Dict[str, IndexFactory]]
ExercisePayoffCreator: TypeAlias = Callable[..., Dict[str, ExercisePayoff]]
ExercisableCreator: TypeAlias = Callable[..., Dict[str, Exercisable]]
DataFrameCreator: TypeAlias = Callable[..., Dict[str, pd.DataFrame]]

ExtraParams = ParamSpec('ExtraParams')

CashflowsCreator: TypeAlias = Callable[[Dict[str, Series], Schedule, ExtraParams], Dict[str, pd.DataFrame]]


