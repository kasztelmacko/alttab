from periods.distribution import MonthlyDistribution
from datetime import datetime

start_date = datetime(2024, 10, 28)
end_date = datetime(2025, 2, 28)
total_orders = 1000

month_probabilities = [0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.10, 0.20, 0.15, 0.05, 0.05, 0.10]
day_of_week_factor = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4] 
# day_of_month_factor = [1.0] * 31  # Example day of month factors

noise_std_dev = 0.1

month = MonthlyDistribution(
    start_date=start_date,
    end_date=end_date,
    total_orders=total_orders,
    month_probabilities=month_probabilities,
    noise_std_dev=noise_std_dev
)

for month in month.generate_months():
    print(f"Year: {month.year}, Month: {month.month}, Year prob {month.year_probability:.4f}, Month Probability: {month.month_probability:.4f},")
    print(f"Orders {round(month.year_probability * month.month_probability * total_orders)}")