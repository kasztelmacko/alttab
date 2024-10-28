from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from datetime import datetime, timedelta

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
            year.probability = year_probability
            probabilities.append(year_probability)

        return probabilities

    def distribute_orders(self):
        return self.distribution.distribute_orders(self.generator.total_orders)

    def generate_years(self) -> List[Year]:
        return self.generator.generate_periods(Year)

# class MonthlyDistribution(Distribution):
#     monthly_orders: int = Field(..., description="Orders assigned to this month from YearlyDistribution")

#     def distribute_orders(self):
#         self.total_orders = self.monthly_orders
#         self.adjust_probabilities()
#         return super().distribute_orders()

#     @classmethod
#     def validate_period_length(cls, values):
#         probabilities = values.get("probabilities", [])

#         if len(probabilities) != 31:
#             raise ValueError("Please provide probabilities for all 31 days")
        
#         return values

#     @staticmethod
#     def days_in_month(month, year):
#         if month == 2:
#             if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
#                 return 29
#             else:
#                 return 28
#         elif month in {4, 6, 9, 11}:
#             return 30
#         else:
#             return 31

#     def aggregate_probabilities(self, probabilities: List[float], target_days: int) -> List[float]:
#         num_days = len(probabilities)
        
#         if num_days == target_days:
#             return probabilities
        
#         new_probabilities = []
        
#         if num_days > target_days:
#             # If reducing the number of days
#             groups = num_days // target_days
#             remainder = num_days % target_days
            
#             for i in range(target_days):
#                 if i < remainder:
#                     group_prob = sum(probabilities[i * (groups + 1):(i + 1) * (groups + 1)])
#                 else:
#                     group_prob = sum(probabilities[i * groups + remainder:(i + 1) * groups + remainder])
#                 new_probabilities.append(group_prob)

#         return new_probabilities

#     def adjust_probabilities(self):
#         days_in_month = self.days_in_month(self.month, self.year)
#         if len(self.probabilities) != days_in_month:
#             self.probabilities = self.aggregate_probabilities(self.probabilities, days_in_month)

# class DailyDistribution(Distribution):
#     pass
