import QuantLib as ql



# cashflow of interest rate swap
# pay floating, receive fixed
paySchedule = [d for d in paySchedule]
recSchedule = [d for d in recSchedule]
fixed_rate = 0.02
notional = 1_000_000
year_fraction_pay = np.array(year_fraction(paySchedule, dayCount, accoumulative=False))[:,np.newaxis]
year_fraction_rec = np.array(year_fraction(recSchedule, dayCount, accoumulative=False))[:,np.newaxis]
fixed_cashflows = notional * fixed_rate * year_fraction_rec
print(f'fixed_cashflows.shape: {fixed_cashflows.shape}')
fixed_cashflows_df = pd.DataFrame(fixed_cashflows, index=recSchedule[1:])
floating_cashflows = notional * fixings[:-1, :] * year_fraction_pay
floating_cashflows_df = pd.DataFrame(floating_cashflows, index=paySchedule[1:])
net_cashflows_df = fixed_cashflows_df - floating_cashflows_df
net_cashflows = fixed_cashflows - floating_cashflows

print(fixed_cashflows_df)
print(floating_cashflows_df)
print(net_cashflows_df)