from periods.noiser import Noiser
from periods.schemas import Hour, Day, Month, Year

from pydantic import ValidationError, BaseModel
from typing import List, Union, Any, Type

from datetime import datetime, timedelta


class OrdersGenerator:
    def __init__(self, start_date: datetime, end_date: datetime, total_orders: int):
        self.start_date = start_date
        self.end_date = end_date
        self.total_orders = total_orders

        self.year: List[Year] = self.generate_periods(Year)
        self.month: List[Month] = self.generate_periods(Month)
        self.day: List[Day] = self.generate_periods(Day)
        self.hour: List[Hour] = self.generate_periods(Hour)

    def generate_periods(self, period_class: Type[Year] | Type[Month] | Type[Day] | Type[Hour]) -> List[Year | Month | Day | Hour]:
        periods = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            if period_class == Year:
                period = period_class(year=current_date.year)
            elif period_class == Month:
                period = period_class(year=current_date.year, month=current_date.month)
            elif period_class == Day:
                period = period_class(year=current_date.year, month=current_date.month, day_of_month=current_date.day, day_of_week=current_date.weekday())
            elif period_class == Hour:
                for hour_in_day in range(24):
                    period = period_class(year=current_date.year, month=current_date.month, day_of_month=current_date.day, day_of_week=current_date.weekday(), hour_in_day=hour_in_day)
                    periods.append(period)
                current_date += timedelta(days=1)
                continue
            else:
                raise ValueError(f"Unsupported period class: {period_class}")
            
            periods.append(period)
            
            if period_class == Year:
                current_date = datetime(current_date.year + 1, 1, 1)
            elif period_class == Month:
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)
            elif period_class == Day:
                current_date += timedelta(days=1)
        
        return periods

