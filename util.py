import QuantLib as ql
import pandas as pd

def get_nearest_fixing_date(d, obs_index):
    # Returns the greatest date in obs_index that is <= d
    return max([date for date in obs_index if date <= d])

def year_fraction(schedule, dayCount, accoumulative=False):
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
        
def combine_schedule(*schedules):
    all_schedule = set()
    for scd in schedules:
        s = {d for d in scd}
        all_schedule = all_schedule.union(s)
    return sorted(all_schedule)

def leg_to_series(leg):
    """
    Convert a QuantLib Leg (list of CashFlows) to a pandas DataFrame.
    Index: payment date (as pd.Timestamp)
    Column: amount
    """
    dates = []
    amounts = []
    for cf in leg:
        dt = cf.date()  # You may want to convert to pd.Timestamp if needed
        dates.append(dt)
        amounts.append(cf.amount())
    return pd.DataFrame({'amount': amounts}, index=dates)