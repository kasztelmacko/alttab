from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import calendar

from periods.schemas import Hour, Day, Month, Year
from periods.noiser import Noiser

from generator import OrdersGenerator

class Distribution(BaseModel):
    probabilities: List[float] = Field(..., description="probability distribution for given period")
    noise_std_dev: Optional[float] = Field(None, description="Standard deviation for noise to be applied to probabilities")

    @classmethod
    def validate_probabilities(cls, values):
        probabilities = values.get("probabilities", [])
        
        if not (0.999 <= sum(probabilities) <= 1.001):
            raise ValueError("The sum of probabilities must be 1.")
        
        return values
    
    def distribute_orders(self, total_orders: int) -> List[int]:
        raw_orders = [total_orders * prob for prob in self.probabilities]
        int_orders = [int(order) for order in raw_orders]
        remainder = total_orders - sum(int_orders)

        fractional_parts = [(i, raw_orders[i] - int_orders[i]) for i in range(len(self.probabilities))]
        fractional_parts.sort(key=lambda x: x[1], reverse=True)

        for i in range(remainder):
            index = fractional_parts[i][0]
            int_orders[index] += 1
        
        return int_orders

    def apply_noise(self) -> List[float]:
        if self.noise_std_dev is not None:
            noiser = Noiser(self.noise_std_dev)
            self.probabilities = noiser.apply_noise(self.probabilities)
        return self.probabilities

class YearlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, 
                 noise_std_dev: Optional[float] = None):
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.distribution = Distribution(probabilities=[1.0] * len(self.generator.year), noise_std_dev=noise_std_dev)
        self.year_probabilities = self.calculate_probabilities()
        self.total_orders = total_orders

    def calculate_probabilities(self) -> List[float]:
        self.distribution.apply_noise()
        total = sum(self.distribution.probabilities)
        normalized_probabilities = [prob / total for prob in self.distribution.probabilities]
        return normalized_probabilities

    def generate_years(self) -> List[Year]:
        years = []
        for i, year_obj in enumerate(self.generator.year):
            year_probability = self.year_probabilities[i]
            year_total_orders = self.total_orders * year_probability

            year = Year(
                year=year_obj.year,
                year_probability=year_probability,
                total_orders=year_total_orders
            )
            years.append(year)

        return years
    
class MonthlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, 
                 month_probabilities: List[float], 
                 noise_std_dev: Optional[float] = None):
        
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.validate_month_probabilities(month_probabilities)
        self.distribution = Distribution(probabilities=month_probabilities, noise_std_dev=noise_std_dev)
        self.month_probabilities = self.calculate_probabilities()
        self.total_orders = total_orders
        self.yearly_distribution = YearlyDistribution(start_date, end_date, total_orders, noise_std_dev)

    def validate_month_probabilities(self, month_probabilities: List[float]):
        if len(month_probabilities) != 12:
            raise ValueError(f"Please provide probabilities for every month in a year. Got {len(month_probabilities)}.")
        
        Distribution.validate_probabilities({"probabilities": month_probabilities})

    def calculate_probabilities(self) -> List[float]:
        month_count = len(self.generator.month)
        adjusted_probabilities = [0] * month_count

        for i, month_obj in enumerate(self.generator.month):
            total_days_in_month = calendar.monthrange(month_obj.year, month_obj.month)[1]

            if i == 0:  # First month
                end_of_month = datetime(month_obj.year, month_obj.month, total_days_in_month)
                days_remaining = (end_of_month - self.generator.start_date).days + 1
                adjusted_probabilities[i] = days_remaining / total_days_in_month
            elif i == month_count - 1:  # Last month
                days_used = (self.generator.end_date - datetime(month_obj.year, month_obj.month, 1)).days + 1
                adjusted_probabilities[i] = days_used / total_days_in_month
            else:  # Middle months
                adjusted_probabilities[i] = 1

        combined_probabilities = [self.distribution.probabilities[(month_obj.month - 1) % 12] * adjusted_probabilities[i] for i, month_obj in enumerate(self.generator.month)]
        
        self.distribution.probabilities = combined_probabilities
        self.distribution.apply_noise()

        total = sum(self.distribution.probabilities)
        normalized_probabilities = [prob / total for prob in self.distribution.probabilities]

        return normalized_probabilities

    def generate_months(self) -> List[Month]:
        months = []
        yearly_data = {year.year: year for year in self.yearly_distribution.generate_years()}
        for i, month_obj in enumerate(self.generator.month):
            year_info = yearly_data[month_obj.year]
            month_probability = self.month_probabilities[i]
            cumulative_probability = year_info.year_probability * month_probability
            month_total_orders = self.total_orders * cumulative_probability

            month = Month(
                year=month_obj.year,
                year_probability=year_info.year_probability,
                total_orders=month_total_orders,
                month=month_obj.month,
                month_probability=month_probability
            )
            months.append(month)

        return months
    
class DailyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, 
                 month_probabilities: List[float], 
                 day_of_week_factor: Optional[List[float]] = None, 
                 day_of_month_factor: Optional[List[float]] = None, 
                 noise_std_dev: Optional[float] = None):
        
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.day_of_week_factor = day_of_week_factor if day_of_week_factor else [1.0] * 7
        self.day_of_month_factor = day_of_month_factor if day_of_month_factor else [1.0] * 31
        self.validate_factors()

        day_count = len(self.generator.day)
        uniform_probabilities = [1.0 / day_count] * day_count
        self.distribution = Distribution(probabilities=uniform_probabilities, noise_std_dev=noise_std_dev)
        self.distribution.apply_noise()
        self.day_probabilities = self.calculate_probabilities()

        self.yearly_distribution = YearlyDistribution(start_date, end_date, total_orders, noise_std_dev)
        self.monthly_distribution = MonthlyDistribution(start_date, end_date, total_orders, month_probabilities, noise_std_dev)

    def validate_factors(self):
        if len(self.day_of_week_factor) != 7:
            raise ValueError(f"Please provide factors for every day in a week. Got {len(self.day_of_week_factor)}.")
        if len(self.day_of_month_factor) != 31:
            raise ValueError(f"Please provide factors for every day in a month. Got {len(self.day_of_month_factor)}.")

    def calculate_probabilities(self) -> List[float]:
        day_count = len(self.generator.day)
        adjusted_probabilities = [0] * day_count

        for i, day_obj in enumerate(self.generator.day):
            adjusted_probabilities[i] = self.day_of_month_factor[day_obj.day_of_month - 1] * self.day_of_week_factor[day_obj.day_of_week] * self.distribution.probabilities[i]

        month_indices = {}
        for i, day_obj in enumerate(self.generator.day):
            if day_obj.month not in month_indices:
                month_indices[day_obj.month] = []
            month_indices[day_obj.month].append(i)

        normalized_probabilities = [0] * day_count
        for month, indices in month_indices.items():
            month_combined_probabilities = [adjusted_probabilities[i] for i in indices]
            total_month_combined_prob = sum(month_combined_probabilities)
            for i in indices:
                normalized_probabilities[i] = adjusted_probabilities[i] / total_month_combined_prob

        return normalized_probabilities

    def generate_days(self) -> List[Day]:
        days = []
        monthly_data = {(month.year, month.month): month for month in self.monthly_distribution.generate_months()}

        for i, day_obj in enumerate(self.generator.day):
            month_info = monthly_data[(day_obj.year, day_obj.month)]
            day_probability = self.day_probabilities[i]

            cumulative_probability = month_info.month_probability * day_probability
            day_total_orders = self.generator.total_orders * cumulative_probability

            day = Day(
                year=day_obj.year,
                year_probability=month_info.year_probability,
                month=day_obj.month,
                month_probability=month_info.month_probability,
                day_of_month=day_obj.day_of_month,
                day_of_week=day_obj.day_of_week,
                day_probability=day_probability,
                total_orders=day_total_orders
            )
            days.append(day)

        return days


class HourlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, 
                 month_probabilities: List[float], 
                 hour_probabilities: List[float], 
                 day_of_week_factor: Optional[List[float]] = None, 
                 day_of_month_factor: Optional[List[float]] = None, 
                 noise_std_dev: Optional[float] = None):
        
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.validate_hour_probabilities(hour_probabilities)
        self.distribution = Distribution(probabilities=hour_probabilities, noise_std_dev=noise_std_dev)
        self.hour_probabilities = self.calculate_probabilities(hour_probabilities)

        self.yearly_distribution = YearlyDistribution(start_date, end_date, total_orders, noise_std_dev)
        self.monthly_distribution = MonthlyDistribution(start_date, end_date, total_orders, month_probabilities, noise_std_dev)
        self.daily_distribution = DailyDistribution(start_date, end_date, total_orders, month_probabilities, day_of_week_factor, day_of_month_factor, noise_std_dev)

    def validate_hour_probabilities(self, hour_probabilities: List[float]):
        if len(hour_probabilities) != 24:
            raise ValueError(f"Please provide probabilities for every hour in a day. Got {len(hour_probabilities)}.")
        
        Distribution.validate_probabilities({"probabilities": hour_probabilities})
        
    def calculate_probabilities(self, hour_probabilities: List[float]) -> List[float]:
        self.distribution.probabilities = hour_probabilities
        self.distribution.apply_noise()

        total = sum(self.distribution.probabilities)
        normalized_probabilities = [prob / total for prob in self.distribution.probabilities]

        return normalized_probabilities
    
    def generate_hours(self) -> List[Hour]:
        hours = []
        num_days = (self.generator.end_date - self.generator.start_date).days + 1
        hour_probabilities_repeated = self.hour_probabilities * num_days

        yearly_data = {year.year: year for year in self.yearly_distribution.generate_years()}
        monthly_data = {(month.year, month.month): month for month in self.monthly_distribution.generate_months()}
        daily_data = {(day.year, day.month, day.day_of_month): day for day in self.daily_distribution.generate_days()}

        for i, hour_obj in enumerate(self.generator.hour):
            year_info = yearly_data[hour_obj.year]
            month_info = monthly_data[(hour_obj.year, hour_obj.month)]
            day_info = daily_data[(hour_obj.year, hour_obj.month, hour_obj.day_of_month)]
            hour_probability = hour_probabilities_repeated[i % 24]

            cumulative_probability = (
                year_info.year_probability * 
                month_info.month_probability * 
                day_info.day_probability * 
                hour_probability
            )
            hour_total_orders = self.generator.total_orders * cumulative_probability

            hour = Hour(
                year=hour_obj.year,
                year_probability=year_info.year_probability, 
                month=hour_obj.month, 
                month_probability=month_info.month_probability, 
                day_of_month=hour_obj.day_of_month, 
                day_of_week=hour_obj.day_of_week, 
                day_probability=day_info.day_probability, 
                hour_in_day=hour_obj.hour_in_day, 
                hour_probability=hour_probability,
                total_orders=hour_total_orders
            )
            hours.append(hour)

        return hours