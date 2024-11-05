
# OrdersDF Generator

This module helps generate synthetic orders based on assumed distributions and factors. Each order is distributed across Periods with calculated probabilties. Then those probabilities are used to generate DataFrame of orders with given products.


## Screenshots

![App Screenshot](https://github.com/kasztelmacko/alttab/blob/master/static/OrderGenerator.png)


## Features

- Distribute orders into Year, Month, Day, Hour
- Plot distributions
- Create a orders dataframe with your products


# Arguments
OrderDistributionGenerator has:
- start_date: start date of the period, 
- end_date: end date of the period, 
- total_orders: number of orders to distribute in period, 
- month_probabilities: list of probabilites for each month (needed for Monthly, Daily, Hourly Distributions), 
- day_of_week_factor: list of multipliers for each day of week (Optional)
- day_of_month_factor: list of multipliers for each day of month (Optional), 
- hour_probabilities: list of probabilites for each hour (needed for Hourly Distribution), ,
- linear_trend: slope of linear trend (only yearly and monthly)
- noise_std_dev: standard deviation for the noising


## Installation

You can install the project with pip

```bash
    git clone https://github.com/kasztelmacko/alttab.git
    cd alttab
```
then create an envirometn and
```bash
    pip install -r requirements.txt
```

## TODO

- ~~Add the DataFrame creator with user given products~~
- ~~Add linear trend option to Distributions~~
- Add product seasonality
- Add Markov-Chain mode so future order count depends on previous period

