from periods.distribution import MonthlyDistribution
from datetime import datetime

start_date = datetime(2024, 10, 28)
end_date = datetime(2025, 9, 28)
total_orders = 1000

month_probabilities = [0.05,0.05,0.05,0.05,0.05,0.10,0.10,0.20,0.15,0.05,0.05,0.10]

monthly_distribution = MonthlyDistribution(
    start_date=start_date,
    end_date=end_date,
    total_orders=total_orders,
    month_probabilities=month_probabilities
)


for month in monthly_distribution.generate_months():
    print(f"Year: {month.year}, Month: {month.month}, Year prob {month.year_probability}, Month Probability: {month.month_probability:.2f}, Orders {round(month.year_probability * month.month_probability * total_orders)}")