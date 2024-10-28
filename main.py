from periods.distribution import YearlyDistribution
from datetime import datetime

# Example usage of YearlyDistribution
start_date = datetime(2024, 10, 28)
end_date = datetime(2025, 10, 28)
total_orders = 1000

yearly_distribution = YearlyDistribution(start_date=start_date, end_date=end_date, total_orders=total_orders)

# Distribute orders
year_orders = yearly_distribution.distribute_orders()

# Print the distributed orders for each year
for year, orders in zip(yearly_distribution.generate_years(), year_orders):
    print(f"Year: {year.year}, Probability: {year.probability}, Orders: {orders}")