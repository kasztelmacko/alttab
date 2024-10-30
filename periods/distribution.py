from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from datetime import datetime, timedelta
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
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, noise_std_dev: Optional[float] = None):
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.probabilities = self.calculate_probabilities()
        self.distribution = Distribution(probabilities=self.probabilities, noise_std_dev=noise_std_dev)
        self.distribution.apply_noise()

    def calculate_probabilities(self) -> List[float]:
        probabilities = []
        total_days = (self.generator.end_date - self.generator.start_date).days + 1

        for year in self.generator.year:
            year_start = datetime(year.year, 1, 1)
            year_end = datetime(year.year, 12, 31)

            if year.year == self.generator.start_date.year:
                year_start = self.generator.start_date
            if year.year == self.generator.end_date.year:
                year_end = self.generator.end_date

            year_days = (year_end - year_start).days + 1
            year_probability = year_days / total_days
            year.year_probability = year_probability
            probabilities.append(year_probability)

        return probabilities

    def generate_years(self) -> List[Year]:
        years = []
        for year_obj, probability in zip(self.generator.year, self.distribution.probabilities):
            year = Year(year=year_obj.year, year_probability=probability)
            years.append(year)
        return years
    
class MonthlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, month_probabilities: List[float], noise_std_dev: Optional[float] = None):
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.validate_month_probabilities(month_probabilities)
        self.distribution = Distribution(probabilities=month_probabilities, noise_std_dev=noise_std_dev)
        self.month_probabilities = self.calculate_probabilities()
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
        for i, month_obj in enumerate(self.generator.month):
            year_probability = next(year.year_probability for year in self.yearly_distribution.generate_years() if year.year == month_obj.year)
            month_probability = self.month_probabilities[i]
            month = Month(year=month_obj.year, year_probability=year_probability, month=month_obj.month, month_probability=month_probability)
            months.append(month)
        return months
    
class DailyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, month_probabilities: List[float], day_of_week_factor: Optional[List[float]] = None, day_of_month_factor: Optional[List[float]] = None, noise_std_dev: Optional[float] = None):
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
            adjusted_probabilities[i] = self.day_of_month_factor[day_obj.day_in_month - 1] * self.day_of_week_factor[day_obj.weekday] * self.distribution.probabilities[i]

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
        for i, day_obj in enumerate(self.generator.day):
            year_probability = next(year.year_probability for year in self.yearly_distribution.generate_years() if year.year == day_obj.year)
            month_probability = next(month.month_probability for month in self.monthly_distribution.generate_months() if month.year == day_obj.year and month.month == day_obj.month)
            day_probability = self.day_probabilities[i]
            day = Day(year=day_obj.year, year_probability=year_probability, month=day_obj.month, month_probability=month_probability, day_in_month=day_obj.day_in_month, weekday=day_obj.weekday, day_probability=day_probability)
            days.append(day)
        return days

