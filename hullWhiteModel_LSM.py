import numpy as np
from sklearn.linear_model import LinearRegression

def cancellable_swap_LSM(fixings, discountFactors, net_cashflows, exercise_dates, notional=1_000_000):
    """
    Price a cancellable interest rate swap using the Longstaff-Schwartz method.
    Args:
        fixings: np.ndarray, shape (numPaths, numPeriods), simulated forward rates at fixing dates
        discountFactors: np.ndarray, shape (numPaths, numPeriods), discount factors at payment dates
        net_cashflows: np.ndarray, shape (numPaths, numPeriods-1), net swap cashflows for each path
        exercise_dates: list of QuantLib Dates, early exercise schedule (same as fixing dates)
        notional: swap notional
    Returns:
        Estimated value of the cancellable swap (float)
    """
    numPaths, numPeriods = fixings.shape
    # net_cashflows: shape (numPaths, numPeriods-1)
    # For swap, early exercise is possible at each fixing date (except last)
    
    # Initialize: all swaps alive at start
    alive = np.ones((numPaths, numPeriods-1), dtype=bool)
    exercise_time = np.full(numPaths, numPeriods-1)  # default: exercise at final date
    
    # Discounted cashflow matrix for each path/period
    discounted_cf = np.zeros_like(net_cashflows)
    for t in range(numPeriods-1):
        discounted_cf[:, t] = net_cashflows[:, t] * discountFactors[:, t]
    
    # Backward induction for early exercise
    continuation = np.zeros((numPaths, numPeriods-1))
    value = np.zeros((numPaths, numPeriods-1))
    value[:, -1] = discounted_cf[:, -1]  # value at maturity
    
    for t in reversed(range(numPeriods-2)):
        # Only consider alive paths
        itm = discounted_cf[:, t] > 0  # in-the-money paths (holder benefits by cancelling)
        X = fixings[itm, t].reshape(-1, 1)  # basis: fixing rate at t
        Y = value[itm, t+1] / discountFactors[itm, t+1]  # continuation value, discounted back to t
        if len(X) > 0:
            # Regression: continuation value as function of state variable (fixing)
            model = LinearRegression().fit(X, Y)
            continuation_val = model.predict(fixings[:, t].reshape(-1, 1)) * discountFactors[:, t+1]
        else:
            continuation_val = np.zeros(numPaths)
        continuation[:, t] = continuation_val
        # If immediate exercise value > continuation, exercise
        exercise = (discounted_cf[:, t] > continuation_val) & alive[:, t]
        value[exercise, t] = discounted_cf[exercise, t]
        # If not exercised, carry forward value
        not_exercise = ~exercise & alive[:, t]
        value[not_exercise, t] = value[not_exercise, t+1]
        # Mark all future periods as dead for exercised paths
        for k in range(t+1, numPeriods-1):
            alive[exercise, k] = False
        # Record exercise time
        exercise_time[exercise] = t
    # Value is value at t=0 (discounted)
    price = np.mean(value[:, 0])
    return price

# Example usage (uncomment and adapt as needed):
# from hullWhiteModel import fixings, discountFactors, net_cashflows, fixingSchedule
# cancellable_value = cancellable_swap_LSM(fixings, discountFactors, net_cashflows, fixingSchedule, notional)
# print(f"Cancellable swap value (LSM): {cancellable_value}")
