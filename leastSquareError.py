import pandas as pd
import numpy as np
from typing import List, Callable
from sklearn import linear_model
from util import get_nearest_fixing_date, year_fraction

class LongstaffSchwartz():
    def __init__(self, cashflows: pd.DataFrame, 
                 discountFactors: pd.DataFrame, 
                 exercise_schedule: pd.Series|List, 
                 exercise_payoff: Callable|np.ndarray|pd.DataFrame,
                 observable: pd.DataFrame):
        self.cashflows = cashflows
        self.discountFactors = discountFactors
        self.exercise_schedule = exercise_schedule
        self.observable = observable
        self.exercise_payoff_func = exercise_payoff

        

    def backward_induction(self):
        np.set_printoptions(precision=2, suppress=True)
        pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
        self.regressors = []
        self._exercise_cashflows = pd.DataFrame(np.zeros(self.cashflows.shape), index=self.cashflows.index, columns=self.cashflows.columns)
        valuation = np.zeros(self.cashflows.shape[1])  # shape_single_step
        print(f'valuation.shape: {valuation.shape}')
        survival = pd.DataFrame(
            np.ones(self.cashflows.shape,dtype=bool),  # or proper shape
            index=self.cashflows.index,
            columns=self.cashflows.columns
            
        )
        print('\n ****************Backward Longstaff-Schwartz method begin:*******************')
        for d in reversed(self.cashflows.index):
            print(f'\nTime step {d}')
            current_cf = self.cashflows.loc[d]
            if self.exercise_schedule.loc[d]:
                print('\n  Process exercise')
                print('Valuation of future cf:')
                print(np.round(valuation.values, 2))
                reg = linear_model.LinearRegression()
                nearest_fixing_date = get_nearest_fixing_date(d, self.observable.index)
                print(f'using fixing date: {nearest_fixing_date} for early exercise call date: {d}')
                x = self.observable.loc[nearest_fixing_date].values.reshape(-1, 1)
                reg.fit(x, valuation)
                y = reg.predict(x)
                print(f'Predicted valuation of not exercising: {np.round(y, 2)}')
                exe_payoff = self.exercise_payoff_func(self.observable.loc[nearest_fixing_date,:].values)
                self._exercise_cashflows.loc[d] = exe_payoff
                print(f'payoff of early exercise: {np.round(exe_payoff, 2)}')
                not_exercise = y > exe_payoff
                exercise = y < exe_payoff
                print(f'Whether to exercise: {exercise}')

                optimized = not_exercise * valuation + exercise * exe_payoff
                print('optimized value:')
                print(np.round(optimized.values, 2))
                valuation = current_cf + optimized
                print('cashflow of current step:')
                print(np.round(current_cf.values, 2))
                print('optimized value plus current cf:')
                print(np.round(valuation.values, 2))
                survival.loc[d,:] = not_exercise
                self.regressors.insert(0, reg)
            else:
                print('\n   No early exercise, add current')
                print('Valuation of future cf:')
                print(np.round(valuation, 2))
                valuation = current_cf + valuation
                print('cashflow of current step:')
                print(np.round(current_cf.values, 2))
                print('Futre npv plus current cf:')
                print(np.round(valuation.values, 2))
            valuation = self.discountFactors.loc[d] * valuation
            print('discount:')
            print(np.round(valuation.values, 2))
        self.valuation = valuation
        print(f'valuation of monte carlo simulation: {valuation.mean():,.2f}')
        self.survival = survival


    def valuations(self):
        return self.valuation

    def confidence_interval(self, alpha=0.05):
        # asume sampled valuation is normal distribution, alpha for two tail area.
        std = self.valuation.std()
        mean = self.valuation.mean()
        return [mean - std * np.sqrt(alpha/2), mean + std * np.sqrt(alpha/2)]
        
    def survival_probability(self):
        print(f'original survival: \n', self.survival)
        survival = self.survival.cumprod(axis=0)
        print(f'cumprod survival: \n', survival)
        self.accumulated_survival = survival
        return survival.mean(axis=1)

    def exercise_mask(self):
        exercise_mask = pd.DataFrame(np.zeros(self.cashflows.shape), index=self.cashflows.index, columns=self.cashflows.columns, dtype=bool)
        has_exercised = np.zeros(self.cashflows.shape[1], dtype=bool)
        for d in self.cashflows.index:
            will_exercise = np.bitwise_not(self.survival.loc[d])
            will_exercise = np.bitwise_and(will_exercise, np.bitwise_not(has_exercised))
            exercise_mask.loc[d] = will_exercise
            has_exercised = np.bitwise_or(has_exercised, will_exercise)
        return exercise_mask

    def exercise_cashflows(self):
        exercise_mask = self.exercise_mask()
        cf = self._exercise_cashflows * exercise_mask
        print(f'exercise cashflows: \n{cf}')
        return cf.mean(axis=1)



        