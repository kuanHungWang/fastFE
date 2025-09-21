from typing import Literal, List, Dict, Optional, Tuple, Callable, TypeAlias
import QuantLib as ql
import pandas as pd


import numpy as np

# typeAlias
IndexFactory: TypeAlias = Callable[[ql.YieldTermStructureHandle], ql.Index]
Schedule: TypeAlias = Literal[List[ql.Date], ql.Schedule]
ExercisePayoff: TypeAlias = Callable[[np.ndarray], np.ndarray]
ExerciseSchedule: TypeAlias =pd.Series
Series: TypeAlias = Literal[pd.Series, pd.DataFrame]

# node definition ,all output is dict[str, ], and usually end with Creator
ScheduleCreator: TypeAlias = Callable[..., Dict[str, Schedule]]
CurveCreator: TypeAlias = Callable[..., Dict[str, ql.YieldTermStructureHandle]]
IndexFactoriesCreator: TypeAlias = Callable[..., Dict[str, IndexFactory]]
ExercisePayoffCreator: TypeAlias = Callable[..., Dict[str, ExercisePayoff]]
ExerciseScheduleCreator: TypeAlias = Callable[..., Dict[str, ExerciseSchedule]]
DataFrameCreator: TypeAlias = Callable[..., Dict[str, pd.DataFrame]]


CashflowsCreator: TypeAlias = Callable[[Dict[str, Series], Dict[str, Schedule]], Dict[str, pd.DataFrame]]


