from pydantic import BaseModel, Field
from typing import Optional

class Year(BaseModel):
    year: int = Field(..., description="Year")
    year_probability: Optional[float] = Field(None, description="Probability of orders for this year")

class Month(Year):
    month: int = Field(..., description="Month number (1-12)")
    month_probability: Optional[float] = Field(None, description="Probability of orders for this month")

class Day(Month):
    day_in_month: int = Field(..., description="Day in the month (1-31)")
    weekday: Optional[int] = Field(None, description="Weekday number (0-6, where 0 is Monday and 6 is Sunday)")
    day_probability: Optional[float] = Field(None, description="Probability of orders for this day")

class Hour(Day):
    hour_in_day: int = Field(..., description="Hour in the day (0-23)")
    hour_probability: Optional[float] = Field(None, description="Probability of orders for this hour")
