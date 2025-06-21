

def get_nearest_fixing_date(d, obs_index):
    # Returns the greatest date in obs_index that is <= d
    return max([date for date in obs_index if date <= d])

def year_fraction(schedule, dayCount, accoumulative=False):
    schedule = [d for d in schedule]
    if accoumulative:
        return [dayCount.yearFraction(schedule[0],d) for d in schedule]
    else:
        return [dayCount.yearFraction(d1, d2) for d1, d2 in zip(schedule[:-1], schedule[1:])]
        
def combine_schedule(*schedules):
    all_schedule = set()
    for scd in schedules:
        s = {d for d in scd}
        all_schedule = all_schedule.union(s)
    return sorted(all_schedule)
