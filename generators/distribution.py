from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal

from noiser import Noiser

class Distribution(BaseModel):
    total_orders: Optional[int] = Field(None, description="total orders to be relocated by probability distribution")
    probabilities: List[float] = Field(..., description="probability distribution for given period")

    @classmethod
    def validate_probabilities(cls, values):
        probabilities = values.get("probabilities", [])
        
        if not (0.999 <= sum(probabilities) <= 1.001):
            raise ValueError("The sum of probabilities must be 1.")
        
        return values
    
    def distribute_orders(self):
        if self.total_orders is None:
            raise ValueError("total_orders must be set before calling distribute_orders")
        
        raw_orders = [self.total_orders * prob for prob in self.probabilities]
        int_orders = [int(order) for order in raw_orders]
        remainder = self.total_orders - sum(int_orders)

        fractional_parts = [(i, raw_orders[i] - int_orders[i]) for i in range(len(self.probabilities))]
        fractional_parts.sort(key=lambda x: x[1], reverse=True)

        for i in range(remainder):
            index = fractional_parts[i][0]
            int_orders[index] += 1
        
        return int_orders

class YearlyDistribution(Distribution):
    @classmethod
    def validate_period_length(cls, values):
        probabilities = values.get("probabilities", [])

        if len(probabilities) != 12:
            raise ValueError("Please provide probabilities for all 12 months")
        
        return values

class MonthlyDistribution(Distribution):
    month: int = Field(..., description="Month number (1-12)")
    year: int = Field(..., description="Year")
    monthly_orders: int = Field(..., description="Orders assigned to this month from YearlyDistribution")

    def distribute_orders(self):
        self.total_orders = self.monthly_orders
        self.adjust_probabilities()
        return super().distribute_orders()

    @classmethod
    def validate_period_length(cls, values):
        probabilities = values.get("probabilities", [])

        if len(probabilities) != 31:
            raise ValueError("Please provide probabilities for all 31 days")
        
        return values

    @staticmethod
    def days_in_month(month, year):
        if month == 2:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            else:
                return 28
        elif month in {4, 6, 9, 11}:
            return 30
        else:
            return 31

    def aggregate_probabilities(self, probabilities: List[float], target_days: int) -> List[float]:
        num_days = len(probabilities)
        
        if num_days == target_days:
            return probabilities
        
        new_probabilities = []
        
        if num_days > target_days:
            # If reducing the number of days
            groups = num_days // target_days
            remainder = num_days % target_days
            
            for i in range(target_days):
                if i < remainder:
                    group_prob = sum(probabilities[i * (groups + 1):(i + 1) * (groups + 1)])
                else:
                    group_prob = sum(probabilities[i * groups + remainder:(i + 1) * groups + remainder])
                new_probabilities.append(group_prob)

        return new_probabilities

    def adjust_probabilities(self):
        days_in_month = self.days_in_month(self.month, self.year)
        print(f"Adjusting probabilities from {len(self.probabilities)} to {days_in_month} days.")
        
        if len(self.probabilities) != days_in_month:
            self.probabilities = self.aggregate_probabilities(self.probabilities, days_in_month)
            print(f"Adjusted probabilities: {self.probabilities}")

# # Example usage
# yearly_probabilities = [0.110, 0.150, 0.134, 0.113, 0.064, 0.072, 0.055, 0.037, 0.094, 0.039, 0.054, 0.078]
# monthly_probabilities = [0.026, 0.057, 0.018, 0.009, 0.046, 0.020, 0.022, 0.032, 0.006,
#  0.030, 0.011, 0.031, 0.058, 0.053, 0.053, 0.018, 0.029, 0.052,
#  0.049, 0.057, 0.056, 0.053, 0.002, 0.005, 0.020, 0.035, 0.051,
#  0.012, 0.048, 0.020, 0.021]

# try:
#     yearly_distribution = YearlyDistribution(total_orders=3452, probabilities=yearly_probabilities)
    
#     monthly_orders = yearly_distribution.distribute_orders()
    
#     print("Monthly Orders Distribution:")
#     for month, orders in enumerate(monthly_orders, start=1):
#         print(f"Month {month}: {orders} orders")
    
#     print(f"\nTotal Orders: {yearly_distribution.total_orders}")

#     # Example for January (Month 1)
#     january_orders = monthly_orders[0]

#     # Apply noise to the probabilities
#     noiser = Noiser(noise_std_dev=0.05)
#     noisy_january_probabilities = noiser.apply_noise(monthly_probabilities)

#     monthly_distribution_january = MonthlyDistribution(monthly_orders=january_orders, probabilities=noisy_january_probabilities, month=1, year=2023)
    
#     daily_orders_january = monthly_distribution_january.distribute_orders()
    
#     print("\nDaily Orders Distribution for January:")
#     for day, orders in enumerate(daily_orders_january, start=1):
#         print(f"Day {day}: {orders} orders")
    
#     print(f"\nTotal Orders for January: {monthly_distribution_january.monthly_orders}")

#     # Example for April (Month 4)
#     april_orders = monthly_orders[3]

#     # Apply noise to the probabilities
#     noisy_april_probabilities = noiser.apply_noise(monthly_probabilities)

#     monthly_distribution_april = MonthlyDistribution(monthly_orders=april_orders, probabilities=noisy_april_probabilities, month=4, year=2023)
    
#     daily_orders_april = monthly_distribution_april.distribute_orders()
    
#     print("\nDaily Orders Distribution for April:")
#     for day, orders in enumerate(daily_orders_april, start=1):
#         print(f"Day {day}: {orders} orders")
    
#     print(f"\nTotal Orders for April: {monthly_distribution_april.monthly_orders}")

# except ValidationError as e:
#     print("Validation error:", e)