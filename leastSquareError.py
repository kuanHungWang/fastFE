import pandas as pd
import numpy as np
from typing import List, Callable
from sklearn import linear_model
from util import get_nearest_fixing_date, year_fraction
import QuantLib as ql
class LongstaffSchwartz():
    def __init__(self, cashflows: pd.DataFrame, 
                 discountFactors: pd.DataFrame, 
                 exercisable: pd.Series, 
                 exercise_payoff: Callable|np.ndarray|pd.DataFrame,
                 observable: pd.DataFrame):

        """
        Initialize a Longstaff-Schwartz object.

        Parameters
        ----------
        cashflows : pd.DataFrame
            The net cashflows of a financial contract before applying discounting and early exercise (index: time, columns: path)
        discountFactors : pd.DataFrame
            Discount factor, for interest rate model, it has multiple column like cashflow, otherwise, if using deterministic discounting, it has only one column.
        exercise_schedule : pd.Series|List
            The early exercise schedule, single column value, for panda series, index must the same as cashflows, and dtype is bool, representing exercisable or not.
        exercise_payoff : Callable|np.ndarray|pd.DataFrame
            The payoff of early exercise, if callable, it takes fixing as input, if numpy array or pandas dataframe, it must have the same shape as cashflows.
        observable : pd.DataFrame
            The observable for least sqaure error estimation for early exercise, usually the fixing values of underling value.
        """
        self.cashflows = cashflows.iloc[1:]
        single_period_dcf = discountFactors/discountFactors.shift(1)  # Discount factor for one time period (from t to t-1), not discount to t0
        self.discountFactors = single_period_dcf  
        self.exercisable = exercisable
        self.observable = observable
        self.exercise_payoff_func = exercise_payoff

        

    def backward_induction(self, verbose=False):
        """
        Execute the Longstaff-Schwartz backward induction algorithm.
        
        Uses linear regression to estimate continuation values and determine optimal
        early exercise decisions at each time step.
        
        Parameters
        ----------
        verbose : bool, optional
            Print detailed step-by-step calculations. Default is False.
            
        Returns
        -------
        None
            Updates instance attributes: valuation, survival, regressors, _exercise_cashflows
            
        Notes
        -----
        After execution, use these methods to access results:
        - valuations() : Get final valuations.
        - confidence_interval() : Calculate confidence interval of valuations
        - survival_probability() : Get survival probabilities at each time step
        - exercise_cashflows() : Get expected cashflow from exercise payoff
        - exercise_mask() : Get boolean mask of exercise decisions
        """
        np.set_printoptions(precision=2, suppress=True)
        pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
        self.regressors = []
        self._exercise_cashflows = pd.DataFrame(np.zeros(self.cashflows.shape), index=self.cashflows.index, columns=self.cashflows.columns)
        valuation = np.zeros(self.cashflows.shape[1])  # shape_single_step
        if verbose:
            print(f'valuation.shape: {valuation.shape}, type: {type(valuation)}')
        survival = pd.DataFrame(
            np.ones(self.cashflows.shape,dtype=bool),  # or proper shape
            index=self.cashflows.index,
            columns=self.cashflows.columns
            
        )
        if verbose:
            print('\n ****************Backward Longstaff-Schwartz method begin:*******************')
        for d in reversed(self.cashflows.index):
            if verbose:
                print(f'\nTime step {d}')
            current_cf = self.cashflows.loc[d]
            if self.exercisable.loc[d]:
                if verbose:
                    print('\n  Process exercise')
                    print(f'Valuation of future cf:')
                    print(np.round(valuation, 2))
                reg = linear_model.LinearRegression()
                nearest_fixing_date = get_nearest_fixing_date(d, self.observable.index)
                if verbose:
                    print(f'using fixing date: {nearest_fixing_date} for early exercise call date: {d}')
                x = self.observable.loc[nearest_fixing_date].values.reshape(-1, 1)
                reg.fit(x, valuation)
                y = reg.predict(x)
                if verbose:
                    print(f'Predicted valuation of not exercising: {np.round(y, 2)}')
                exe_payoff = self.exercise_payoff_func(self.observable.loc[nearest_fixing_date,:].values)
                self._exercise_cashflows.loc[d] = exe_payoff
                if verbose:
                    print(f'payoff of early exercise: {np.round(exe_payoff, 2)}')
                not_exercise = y > exe_payoff
                exercise = y < exe_payoff
                if verbose:
                    print(f'Whether to exercise: {exercise}')

                optimized = not_exercise * valuation + exercise * exe_payoff
                if verbose:
                    print('optimized value:')
                    print(np.round(optimized, 2))
                valuation = current_cf + optimized
                if verbose:
                    print('cashflow of current step:')
                    print(np.round(current_cf, 2))
                    print('optimized value plus current cf:')
                    print(np.round(valuation, 2))
                survival.loc[d,:] = not_exercise
                self.regressors.insert(0, reg)
            else:
                if verbose:
                    print('\n   No early exercise, add current')
                    print('Valuation of future cf:')
                    print(np.round(valuation, 2))
                valuation = current_cf + valuation
                if verbose:
                    print('cashflow of current step:')
                    print(np.round(current_cf, 2))
                    print('Futre npv plus current cf:')
                    print(np.round(valuation, 2))
            valuation = self.discountFactors.loc[d].values * valuation
            if verbose:
                print('discount:')
                print(np.round(valuation, 2))
        self.valuation = valuation
        if verbose:
            print(f'valuation of monte carlo simulation: {valuation.mean():,.2f}')
        self.survival = survival


    def valuations(self):
        """
        Return the expected discounted net present value, i.e. the fair value of the contract.
        
        Returns
        -------
        pd.Series
            Expected discounted net present value of each path.
        """
        return self.valuation

    def confidence_interval(self, alpha=0.05):
        """
        Return the confidence interval of the fair value with given significance level(two tail).
        
        Parameters
        ----------
        alpha : float, optional
            The significance level for the confidence interval. Default is 0.05.
        
        Returns
        -------
        list
            The confidence interval of the fair value.
        """
        # asume sampled valuation is normal distribution, alpha for two tail area.
        std = self.valuation.std()
        mean = self.valuation.mean()
        return [mean - std * np.sqrt(alpha/2), mean + std * np.sqrt(alpha/2)]
        
    def survival_probability(self):
        """
        Return the survival probability of each period.
        
        Returns
        -------
        pd.Series
            Survival probability of each period.
        """
        survival = self.survival.cumprod(axis=0)
        self.accumulated_survival = survival
        return survival.mean(axis=1)

    def exercise_mask(self):
        """
        Return the boolean exercise mask of each path.
        
        Returns
        -------
        pd.DataFrame
            Boolean exercise mask of each path.
        """
        exercise_mask = pd.DataFrame(np.zeros(self.cashflows.shape), index=self.cashflows.index, columns=self.cashflows.columns, dtype=bool)
        has_exercised = np.zeros(self.cashflows.shape[1], dtype=bool)
        for d in self.cashflows.index:
            will_exercise = np.bitwise_not(self.survival.loc[d])
            will_exercise = np.bitwise_and(will_exercise, np.bitwise_not(has_exercised))
            exercise_mask.loc[d] = will_exercise
            has_exercised = np.bitwise_or(has_exercised, will_exercise)
        return exercise_mask

    def exercise_cashflows(self):
        """
        Return the expected value of exercise payoff with consideration of exercise decisions.
        
        Returns
        -------
        pd.Series
            Expected value of exercise payoff with consideration of exercise decisions.
        """
        exercise_mask = self.exercise_mask()
        cf = self._exercise_cashflows * exercise_mask
        return cf.mean(axis=1)

if __name__ == '__main__':


    # Example of using LongstaffSchwartz
    # LongstaffSchwartz(cashflows, discountFactor, exercise_schedule, payoff, fixing)
    # cashflows: pd.DataFrame, the net cashflows of a financial contract before applying discounting and early exercise (index: time, columns: path)
    # discountFactors: pd.DataFrame, discount factor for one time period (from t to t-1), not discount to t0, for interest rate model, it has multiple column like cashflow, otherwise, if using deterministic discounting, it has only one column.
    # exercise_schedule: pd.Series|List, the early exercise scheulde, single column value, for panda series, index must the same as cashflows, and dtype is bool, representing exercisable or not.
    # exercise_payoff: Callable|np.ndarray|pd.DataFrame, the payoff of early exercise, if callable, it takes fixing as input, if numpy array or pandas dataframe, it must have the same shape as cashflows.
    # observable: pd.DataFrame, the observable for early exercise, usually the fixing values of underling value.

    today = ql.Date().todaysDate()
    settlmentDate = today + ql.Period('2D')
    paymentSchedule = ql.MakeSchedule(settlmentDate, settlmentDate + ql.Period('1Y'), ql.Period('3M'))
    paymentSchedule = [d for d in paymentSchedule]
    fixingSchedule = [d - ql.Period('2D') for d in paymentSchedule]
    notional = 1_000

    # we use mock data for cashflows, discountFactors, fixing, and payoff in this example.
    # in real case it depends on the contract type and the model used.
    cashflows = pd.DataFrame(np.random.randn(len(paymentSchedule), 3) * notional, index=paymentSchedule)
    discountFactor = pd.DataFrame([1/((1+np.random.uniform(0,0.05))) for i in range(len(paymentSchedule))], index=paymentSchedule)
    fixing = pd.DataFrame(np.random.randn(len(paymentSchedule), 3), index=fixingSchedule)
    payoff = lambda fixing: np.maximum(fixing - 1, 0)
    exercise_schedule = pd.Series(np.ones(len(paymentSchedule), dtype=bool), index=paymentSchedule)
    exercise_schedule.iloc[0] = False
    ls = LongstaffSchwartz(cashflows, discountFactor, exercise_schedule, payoff, fixing)
    ls.backward_induction()

    # demostration of instance function of LongstaffSchwartz class
    print(f'\nvaluation: {ls.valuations().mean():,.2f}')  # valuation of each path, take average to get expetated value.
    print(f'\nconfidence interval: {ls.confidence_interval()}')  # confidence interval of the valuation
    print(f'\nsurvival probability: {ls.survival_probability()}')  # survival probability of the contract
    print(f'\nexercise cashflows: \n{ls.exercise_cashflows()}') # expected value of exercise payoff with consideration of early exercise.
    print(f'\nexercise mask: \n{ls.exercise_mask()}')  # whether exercise at each time step and each path



