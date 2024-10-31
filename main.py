from periods.distribution import YearlyDistribution, MonthlyDistribution, DailyDistribution, HourlyDistribution
from datetime import datetime

import random

start_date = datetime(2025, 1, 2)
end_date = datetime(2025, 1, 2)
total_orders = 1000

month_probabilities = [0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.10, 0.20, 0.15, 0.05, 0.05, 0.10]
hour_probabilities = [0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0, 0, 0, 0]
day_of_week_factor = [1, 1, 1, 1, 1, 1.5, 1.5] 
day_of_month_factor = [1.0] * 31

noise_std_dev = 0

# year = YearlyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     noise_std_dev=noise_std_dev
# )
# sum = 0
# for year in year.generate_years():
#     print(f"Year: {year.year}, Year prob {year.year_probability:.4f}")
#     print(f"Orders {year.total_orders}")
#     sum += year.total_orders
# print(sum)


# month = MonthlyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     month_probabilities=month_probabilities,
#     noise_std_dev=noise_std_dev
# )

# sum = 0
# for month in month.generate_months():
#     print(f"Year: {month.year}, Month: {month.month}, Year prob {month.year_probability:.4f}, Month Probability: {month.month_probability:.4f},")
#     print(f"Orders {month.total_orders}")
#     sum += month.total_orders
# print(sum)

# day = DailyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     month_probabilities=month_probabilities,
#     day_of_week_factor=day_of_week_factor,
#     day_of_month_factor=day_of_month_factor,
#     noise_std_dev=noise_std_dev
# )
# sum = 0
# for day in day.generate_days():
#     print(f"year: {day.year}, month: {day.month}, day_ow: {day.day_of_week}, day_om: {day.day_of_month}, yp: {day.year_probability:.2f}, mp: {day.month_probability:.2f}, dp: {day.day_probability:.2f}")
#     print(f"Orders {day.total_orders}")
#     sum += day.total_orders

# print(sum)

# hour = HourlyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     month_probabilities=month_probabilities,
#     hour_probabilities=hour_probabilities,
#     day_of_week_factor=day_of_week_factor,
#     day_of_month_factor=day_of_month_factor,
#     noise_std_dev=noise_std_dev
# )

# sum = 0
# for hour in hour.generate_hours():
#     print(f"year: {hour.year}, month: {hour.month}, day_ow: {hour.day_of_week}, day_om: {hour.day_of_month} hour: {hour.hour_in_day}, yp: {hour.year_probability:.2f}, mp: {hour.month_probability:.2f}, dp: {hour.day_probability:.2f}, hp: {hour.hour_probability:.2f}")
#     print(f"Orders {hour.total_orders}")
#     sum += hour.total_orders

# print(sum)