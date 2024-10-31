from periods.distribution import YearlyDistribution, MonthlyDistribution, DailyDistribution, HourlyDistribution
from datetime import datetime
from typing import List, Optional
import polars as pl
import seaborn as sns
import matplotlib.pyplot as plt

start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 1, 31)
total_orders = 10000

month_probabilities = [0.05, 0.05, 0.05, 0.05, 0.05, 0.10, 0.10, 0.20, 0.15, 0.05, 0.05, 0.10]
day_of_week_factor = [1, 1, 1, 1, 1, 1.5, 1.5] 
day_of_month_factor = [1.0] * 31
hour_probabilities = [0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.15, 0.15, 0, 0, 0, 0]

noise_std_dev = 0.2

class OrderDistributionGenerator:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, 
                 month_probabilities: Optional[List[float]] = None, 
                 day_of_week_factor: Optional[List[float]] = None, 
                 day_of_month_factor: Optional[List[float]] = None, 
                 hour_probabilities: Optional[List[float]] = None, 
                 noise_std_dev: Optional[float] = None):
        
        self.start_date = start_date
        self.end_date = end_date
        self.total_orders = total_orders
        self.month_probabilities = month_probabilities
        self.day_of_week_factor = day_of_week_factor if day_of_week_factor else [1.0] * 7
        self.day_of_month_factor = day_of_month_factor if day_of_month_factor else [1.0] * 31
        self.hour_probabilities = hour_probabilities if hour_probabilities else [1.0 / 24] * 24
        self.noise_std_dev = noise_std_dev

        self.yearly_distribution = YearlyDistribution(start_date, end_date, total_orders, noise_std_dev)
        self.monthly_distribution = MonthlyDistribution(start_date, end_date, total_orders, month_probabilities, noise_std_dev)
        self.daily_distribution = DailyDistribution(start_date, end_date, total_orders, month_probabilities, day_of_week_factor, day_of_month_factor, noise_std_dev)
        self.hourly_distribution = HourlyDistribution(start_date, end_date, total_orders, month_probabilities, hour_probabilities, day_of_week_factor, day_of_month_factor, noise_std_dev)

    def print_orders(self, distribution_type: str):
        if distribution_type == 'year':
            generator = self.yearly_distribution.generate_years()
            format_str = "Year: {year}, Year prob {year_probability:.4f}, Orders {total_orders}"
        elif distribution_type == 'month':
            generator = self.monthly_distribution.generate_months()
            format_str = "Year: {year}, Month: {month}, Year prob {year_probability:.4f}, Month Probability: {month_probability:.4f}, Orders {total_orders}"
        elif distribution_type == 'day':
            generator = self.daily_distribution.generate_days()
            format_str = "Year: {year}, Month: {month}, Day of Week: {day_of_week}, Day of Month: {day_of_month}, Year Probability: {year_probability:.2f}, Month Probability: {month_probability:.2f}, Day Probability: {day_probability:.2f}, Orders {total_orders}"
        elif distribution_type == 'hour':
            generator = self.hourly_distribution.generate_hours()
            format_str = "Year: {year}, Month: {month}, Day of Week: {day_of_week}, Day of Month: {day_of_month}, Hour: {hour_in_day}, Year Probability: {year_probability:.2f}, Month Probability: {month_probability:.2f}, Day Probability: {day_probability:.2f}, Hour Probability: {hour_probability:.2f}, Orders {total_orders}"
        else:
            raise ValueError("Invalid distribution type. Choose from 'year', 'month', 'day', 'hour'.")

        sum_orders = 0
        for item in generator:
            print(format_str.format(**item.__dict__))
            sum_orders += item.total_orders
        print(f"Total Orders: {sum_orders}")

    def plot_orders(self, distribution_type: str):
        if distribution_type == 'year':
            generator = self.yearly_distribution.generate_years()
            x_label = 'Year'
        elif distribution_type == 'month':
            generator = self.monthly_distribution.generate_months()
            x_label = 'Year-Month'
        elif distribution_type == 'day':
            generator = self.daily_distribution.generate_days()
            x_label = 'Year-Month-Day'
        elif distribution_type == 'hour':
            generator = self.hourly_distribution.generate_hours()
            x_label = 'Year-Month-Day-Hour'
        else:
            raise ValueError("Invalid distribution type. Choose from 'year', 'month', 'day', 'hour'.")

        data = []
        for item in generator:
            data.append({
                'x': f"{item.year}-{item.month:02d}-{item.day_of_month:02d}-{item.hour_in_day:02d}" if distribution_type == 'hour' else
                     f"{item.year}-{item.month:02d}-{item.day_of_month:02d}" if distribution_type == 'day' else
                     f"{item.year}-{item.month:02d}" if distribution_type == 'month' else
                     f"{item.year}",
                'total_orders': item.total_orders
            })

        df = pl.DataFrame(data)
        sns.barplot(x='x', y='total_orders', data=df)
        plt.xlabel(x_label)
        plt.ylabel('Total Orders')
        plt.title(f'Total Orders by {x_label}')
        plt.xticks(rotation=45)
        plt.show()



orders = OrderDistributionGenerator(
    start_date=start_date,
    end_date=end_date,
    total_orders=total_orders,
    month_probabilities=month_probabilities,
    day_of_week_factor=day_of_week_factor,
    day_of_month_factor=day_of_month_factor,
    hour_probabilities=hour_probabilities,
    noise_std_dev=noise_std_dev
)

# orders.print_orders('year')
# orders.print_orders('month')
# orders.print_orders('day')
# orders.print_orders('hour')
orders.plot_orders('day')