from periods.distribution import MonthlyDistribution, DailyDistribution, HourlyDistribution
from datetime import datetime

import random

start_date = datetime(2024, 10, 28)
end_date = datetime(2024, 10, 31)
total_orders = 1000

month_probabilities = [0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.10, 0.20, 0.15, 0.05, 0.05, 0.10]
hour_probabilities = [0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0, 0, 0, 0]
day_of_week_factor = [1, 1, 1, 1, 1, 1.5, 1.5] 
day_of_month_factor = [1.0] * 31

noise_std_dev = 0.2

# month = MonthlyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     month_probabilities=month_probabilities,
#     noise_std_dev=noise_std_dev
# )


# for month in month.generate_months():
#     print(f"Year: {month.year}, Month: {month.month}, Year prob {month.year_probability:.4f}, Month Probability: {month.month_probability:.4f},")
#     print(f"Orders {round(month.year_probability * month.month_probability * total_orders)}")

# day = DailyDistribution(
#     start_date=start_date,
#     end_date=end_date,
#     total_orders=total_orders,
#     month_probabilities=month_probabilities,
#     day_of_week_factor=day_of_week_factor,
#     day_of_month_factor=day_of_month_factor,
#     noise_std_dev=noise_std_dev
# )

# for day in day.generate_days():
#     print(f"y: {day.year}, yp: {day.year_probability}, m: {day.month}, mp: {day.month_probability}, dow: {day.day_of_week}, dom: {day.day_of_month}, dp: {day.day_probability}")

hourly_distribution = HourlyDistribution(
    start_date=start_date,
    end_date=end_date,
    total_orders=total_orders,
    month_probabilities=month_probabilities,
    hour_probabilities=hour_probabilities,
    day_of_week_factor=day_of_week_factor,
    day_of_month_factor=day_of_month_factor,
    noise_std_dev=noise_std_dev
)

for hour in hourly_distribution.generate_hours():
    print(f"Year: {hour.year}, Month: {hour.month}, Day: {hour.day_of_month}, Hour: {hour.hour_in_day}, Probability: {hour.hour_probability:.4f}")
    print(f"Total Orders: {hour.total_orders:.2f}")