import QuantLib as ql
import pandas as pd
import numpy as np

def subset_to_bool(subset_dates, full_dates)->pd.Series:
    """
    Convert subset_dates to a boolean series indexed by full_dates to represent its presents in full_dates.
    For example, if subset_dates = [d1, d2, d3] and full_dates = [d1, d2, d3, d4], the result will be [True, True, True, False].
    Parameters:
        subset_dates: list-like or index-like
            Must be a subset of full_dates.
        full_dates: list-like or index-like
            The full set of dates to use as the index.
    
    Returns:
        pd.Series: Boolean Series indexed by full_dates, with True values where 
                  the date exists in subset_dates, False otherwise.
    """
    if not isinstance(full_dates, list):
        full_dates = [d for d in full_dates]
    if not isinstance(subset_dates, list):
        subset_dates = [d for d in subset_dates]
    
    subset_set = set(subset_dates)
    return pd.Series([date in subset_set for date in full_dates], index=full_dates)
    
def get_nearest_fixing_date(d, obs_index):
    """
    Find the most recent fixing date in the observation index that is on or before the given date.
    
    Parameters:
        d: The reference date (QuantLib Date or comparable date object).
        obs_index: List or iterable of dates representing the observation/fixing schedule.
        
    Returns:
        The greatest date in obs_index that is <= d.
        
    Raises:
        ValueError: If no date in obs_index is <= d.
    """
    # Returns the greatest date in obs_index that is <= d
    return max([date for date in obs_index if date <= d])

def year_fraction(schedule, dayCount: ql.DayCounter, accoumulative=False):
    """
    Calculate year fractions for a schedule of dates using a specified day count convention.
    When to use: to calculate cashflows.
    Parameters:
        schedule (list or ql.Schedule): List of dates or a QuantLib Schedule object.
        dayCount: QuantLib DayCounter object used to compute year fractions.
        accoumulative (bool, optional): If True, returns the year fraction from the first date to each date in the schedule (accumulative). If False, returns the year fraction between each consecutive pair of dates (default).

    Returns:
        list: List of year fractions. If accoumulative is False, the first element is 0. This will keep the length of the list the same as the schedule regardless of the value of accoumulative.
    """

    if isinstance(schedule, ql.Schedule):
        schedule = [d for d in schedule]
    if not isinstance(schedule, list):
        raise ValueError("schedule must be a list or a QuantLib Schedule")
    if accoumulative:
        return [dayCount.yearFraction(schedule[0],d) for d in schedule]
    else:
        result= [dayCount.yearFraction(d1, d2) for d1, d2 in zip(schedule[:-1], schedule[1:])]
        result.insert(0, 0)
        return result
        
def simulation_time_grid(dates, dayCount: ql.DayCounter):
    """
    Build a strictly increasing Monte Carlo time grid from a list of dates.
    When to use: to build the time grid for a path generator from simulation dates.
    Parameters:
        dates (list or ql.Schedule): Simulation dates, in increasing order.
        dayCount: QuantLib DayCounter used to convert dates into times. It should be the day counter
            of the term structure driving the process, so that path times match curve times.

    Returns:
        tuple: (times, index) where times is a strictly increasing list of distinct times starting at 0,
        and index is a numpy array mapping each input date to its position in times. Some day counters
        (e.g. 30/360) give consecutive dates the same time; those dates share one grid point, so a
        path simulated on times can be expanded back to every input date with path[index].
    """
    if isinstance(dates, ql.Schedule):
        dates = [d for d in dates]
    times = []
    index = []
    for d in dates:
        t = dayCount.yearFraction(dates[0], d)
        if times and t < times[-1]:
            raise ValueError(f"dates must be in increasing order, got {d} after a later time")
        if not times or t > times[-1]:
            times.append(t)
        index.append(len(times) - 1)
    return times, np.array(index)

def combine_schedule(*schedules):
    """
    Combine multiple schedules into a single sorted list of unique dates.
    
    Parameters:
        *schedules: Variable number of schedule objects (QuantLib Schedule, list, or iterable of dates).
                   Each schedule should contain date objects that can be iterated over.
    
    Returns:
        list: A sorted list of unique dates from all input schedules combined.

    """
    all_schedule = set()
    for scd in schedules:
        s = {d for d in scd}
        all_schedule = all_schedule.union(s)
    return sorted(all_schedule)

def leg_to_series(leg):
    """
    Convert a QuantLib Leg (list of CashFlows) to a pandas DataFrame.
    
    Parameters:
        leg: QuantLib Leg object (list of CashFlow objects).
    
    Returns:
        pd.DataFrame: DataFrame with payment dates as index and cash flow amounts as 'amount' column.
    """
    dates = []
    amounts = []
    for cf in leg:
        dt = cf.date()  # You may want to convert to pd.Timestamp if needed
        dates.append(dt)
        amounts.append(cf.amount())
    return pd.DataFrame({'amount': amounts}, index=dates)


if __name__ == '__main__':
    # Example for subset_to_bool
    subset_dates = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('6M'))
    full_dates = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('3M'))
    print('subset_to_bool:', subset_to_bool(subset_dates, full_dates))

    # Example for get_nearest_fixing_date
    d = ql.Date(15, 6, 2020)
    schedule = ql.MakeSchedule(ql.Date(1,1,2020), ql.Date(1,1,2021), ql.Period('1M'))
    print('get_nearest_fixing_date:', get_nearest_fixing_date(d, schedule))

    # Example for year_fraction
    schedule = [ql.Date(1, 1, 2020), ql.Date(1, 7, 2020), ql.Date(1, 1, 2021)]
    dayCount = ql.Actual360()
    print('year_fraction (acculumative):', year_fraction(schedule, dayCount, accoumulative=True))
    print('year_fraction (between pairs):', year_fraction(schedule, dayCount, accoumulative=False))

    # Example for combine_schedule
    schedule1 = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('6M'))
    schedule2 = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('3M'))
    print('combine_schedule:', combine_schedule(schedule1, schedule2))

    # Example for leg_to_series
    # Create a mock leg with minimal QuantLib CashFlow-like objects
    schedule = ql.MakeSchedule(ql.Date(15,6,2020), ql.Date(15,6,2021), ql.Period('6M'))
    dayCount = ql.Actual360()
    leg = ql.FixedRateLeg(schedule, dayCount, [100.], [0.05])
    print('leg_to_series:\n', leg_to_series(leg))

