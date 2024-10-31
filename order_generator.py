from periods.distribution import YearlyDistribution, MonthlyDistribution, DailyDistribution, HourlyDistribution

from datetime import datetime
from typing import List, Optional

import numpy as np
import polars as pl

import seaborn as sns
import matplotlib.pyplot as plt

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
        self.month_probabilities = month_probabilities if month_probabilities else [1.0 / 12] * 12
        self.day_of_week_factor = day_of_week_factor if day_of_week_factor else [1.0] * 7
        self.day_of_month_factor = day_of_month_factor if day_of_month_factor else [1.0] * 31
        self.hour_probabilities = hour_probabilities if hour_probabilities else [1.0 / 24] * 24
        self.noise_std_dev = noise_std_dev

    def get_distribution(self, distribution_type: str):
        if distribution_type == 'year':
            generator =  YearlyDistribution(self.start_date, self.end_date, self.total_orders, self.noise_std_dev)
            return generator.generate_years()
        elif distribution_type == 'month':
            generator =  MonthlyDistribution(self.start_date, self.end_date, self.total_orders, self.month_probabilities, self.noise_std_dev)
            return generator.generate_months()
        elif distribution_type == 'day':
            generator =  DailyDistribution(self.start_date, self.end_date, self.total_orders, self.month_probabilities, self.day_of_week_factor, self.day_of_month_factor, self.noise_std_dev)
            return generator.generate_days()
        elif distribution_type == 'hour':
            generator =  HourlyDistribution(self.start_date, self.end_date, self.total_orders, self.month_probabilities, self.hour_probabilities, self.day_of_week_factor, self.day_of_month_factor, self.noise_std_dev)
            return generator.generate_hours()
        else:
            raise ValueError("Invalid distribution type. Choose from 'year', 'month', 'day', 'hour'.")

    def print_orders_cumulated(self, distribution_type: str):
        generator = self.get_distribution(distribution_type)
        
        if distribution_type == 'year':
            format_str = "Year: {year}, Year prob {year_probability:.4f}, Orders {total_orders}"
        elif distribution_type == 'month':
            format_str = "Year: {year}, Month: {month}, Year prob {year_probability:.4f}, Month Probability: {month_probability:.4f}, Orders {total_orders}"
        elif distribution_type == 'day':
            format_str = "Year: {year}, Month: {month}, Day of Week: {day_of_week}, Day of Month: {day_of_month}, Year Probability: {year_probability:.2f}, Month Probability: {month_probability:.2f}, Day Probability: {day_probability:.2f}, Orders {total_orders}"
        elif distribution_type == 'hour':
            format_str = "Year: {year}, Month: {month}, Day of Week: {day_of_week}, Day of Month: {day_of_month}, Hour: {hour_in_day}, Year Probability: {year_probability:.2f}, Month Probability: {month_probability:.2f}, Day Probability: {day_probability:.2f}, Hour Probability: {hour_probability:.2f}, Orders {total_orders}"
        else:
            raise ValueError("Invalid distribution type. Choose from 'year', 'month', 'day', 'hour'.")

        sum_orders = 0
        for item in generator:
            print(format_str.format(**item.__dict__))
            sum_orders += item.total_orders
        print(f"Total Orders: {sum_orders}")

    def plot_orders_cumulated(self, distribution_type: str):
        generator = self.get_distribution(distribution_type)
        
        if distribution_type == 'year':
            x_label = 'Year'
        elif distribution_type == 'month':
            x_label = 'Year-Month'
        elif distribution_type == 'day':
            x_label = 'Year-Month-Day'
        elif distribution_type == 'hour':
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

    def create_orders_df(self, distribution_type: str, 
                        item_data: pl.DataFrame, 
                        item_name_col: str, 
                        item_price_col: Optional[str] = None, 
                        item_popularity_col: Optional[str] = None, 
                        allow_order_multiple: Optional[bool] = False,
                        order_multiple_probability: Optional[float] = None) -> pl.DataFrame:
        
        generator = self.get_distribution(distribution_type)
        
        if distribution_type == 'year':
            time_col_names = ['year']
        elif distribution_type == 'month':
            time_col_names = ['year', 'month']
        elif distribution_type == 'day':
            time_col_names = ['year', 'month', 'day_of_month']
        elif distribution_type == 'hour':
            time_col_names = ['year', 'month', 'day_of_month', 'hour']
        else:
            raise ValueError("Invalid distribution_type. Supported types are 'year', 'month', 'day_of_month', 'hour'.")
        
        time_periods = {col: [] for col in time_col_names}
        item_names = []
        item_prices = []
        order_ids = []
        order_dates = []
        
        order_id_counter = 1
        
        for time_info in generator:
            time_values = [getattr(time_info, col) for col in time_col_names]
            total_orders_for_period = int(time_info.total_orders)
            
            for _ in range(total_orders_for_period):
                if allow_order_multiple:
                    num_items = np.random.geometric(p=order_multiple_probability)
                else:
                    num_items = 1
                
                if item_popularity_col:
                    weights = item_data[item_popularity_col].to_list()
                    weights = np.array(weights) / np.sum(weights)
                    selected_item_names = np.random.choice(
                        item_data[item_name_col].to_list(),
                        p=weights,
                        size=num_items,
                        replace=True
                    )
                else:
                    selected_item_names = np.random.choice(
                        item_data[item_name_col].to_list(),
                        size=num_items,
                        replace=True
                    )
                
                for col, value in zip(time_col_names, time_values):
                    time_periods[col].extend([value] * num_items)
                item_names.extend(selected_item_names)
                
                if item_price_col:
                    item_price_dict = dict(zip(item_data[item_name_col], item_data[item_price_col]))
                    selected_item_prices = [item_price_dict[item] for item in selected_item_names]
                    item_prices.extend(selected_item_prices)
                
                order_ids.extend([order_id_counter] * num_items)
                order_id_counter += 1
                
                if distribution_type != 'year':
                    date_format = {
                        'month': '%Y-%m',
                        'day': '%Y-%m-%d',
                        'hour': '%Y-%m-%d %H:%M:%S'
                    }.get(distribution_type)
                    
                    order_date = datetime(
                        year=time_values[0],
                        month=time_values[1] if len(time_values) > 1 else 1,
                        day=time_values[2] if len(time_values) > 2 else 1,
                        hour=time_values[3] if len(time_values) > 3 else 0
                    ).strftime(date_format)
                    order_dates.extend([order_date] * num_items)
        
        orders_df = pl.DataFrame({
            "order_id": order_ids,
            **time_periods,
            "item_name": item_names
        })
        
        if item_price_col:
            orders_df = orders_df.with_columns(pl.Series("item_price", item_prices))
        
        if distribution_type != 'year':
            orders_df = orders_df.with_columns(pl.Series("order_date", order_dates))

        columns = list(orders_df.columns)
        if 'order_date' in columns:
            columns.remove('order_date')
            order_date_index = columns.index('order_id') + 1
            columns.insert(order_date_index, 'order_date')
        
        orders_df = orders_df.select(columns)
        
        print(orders_df)
        return orders_df