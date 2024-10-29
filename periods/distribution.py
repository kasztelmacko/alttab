from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from datetime import datetime, timedelta
import calendar

from periods.periods import Hour, Day, Month, Year

from generator import OrdersGenerator


class Distribution(BaseModel):
    probabilities: List[float] = Field(..., description="probability distribution for given period")

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

class YearlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int):
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.probabilities = self.calculate_probabilities()
        self.distribution = Distribution(probabilities=self.probabilities)

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
        for year_obj, probability in zip(self.generator.year, self.probabilities):
            year = Year(year=year_obj.year, year_probability=probability)
            years.append(year)
        return years
    
class MonthlyDistribution:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int, month_probabilities: List[float]):
        self.generator = OrdersGenerator(start_date, end_date, total_orders)
        self.probabilities = month_probabilities
        self.distribution = Distribution(probabilities=self.probabilities)
        self.yearly_distribution = YearlyDistribution(start_date, end_date, total_orders)
        self.month_probabilities = self.calculate_probabilities()
        self.validate_month_probabilities(month_probabilities)

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

        combined_probabilities = [self.probabilities[(month_obj.month - 1) % 12] * adjusted_probabilities[i] for i, month_obj in enumerate(self.generator.month)]

        year_indices = {}
        for i, month_obj in enumerate(self.generator.month):
            if month_obj.year not in year_indices:
                year_indices[month_obj.year] = []
            year_indices[month_obj.year].append(i)

        normalized_probabilities = [0] * month_count
        for year, indices in year_indices.items():
            year_combined_probabilities = [combined_probabilities[i] for i in indices]
            total_year_combined_prob = sum(year_combined_probabilities)
            for i in indices:
                normalized_probabilities[i] = combined_probabilities[i] / total_year_combined_prob

        return normalized_probabilities
    
    def generate_months(self) -> List[Month]:
        months = []
        for i, month_obj in enumerate(self.generator.month):
            year_probability = next(year.year_probability for year in self.yearly_distribution.generate_years() if year.year == month_obj.year)
            month_probability = self.month_probabilities[i]
            month = Month(year=month_obj.year, year_probability=year_probability, month=month_obj.month, month_probability= month_probability)
            months.append(month)
        return months
