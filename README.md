# Inventory Replenishment Predicter for Amazon FBA Sellers

This library is intended for Amazon FBA sellers who want to automate their inventory management. It includes Python classes and methods to suggest replenishment quantities based on current inventory levels and predicted future sales.

It uses the [Selling Partner API (SP API)](https://developer.amazonservices.com) to retrieve order data and current inventory levels from the connected Amazon account. To ensure fast performance and avoid throttling, it includes a class with methods to store the requested order data and inventory levels in CSV files.

To predict future sales, it makes use of the [sktime](https://www.sktime.net/en/stable/) library for time series forecasting. It uses a naive forecaster to predict future sales based on the average of past sales quantities, however, depending on business needs and the amount of data available, it can easily be modified with other, more sophisticated forecasters from the sktime library.

Note that this library depends on the [PYTHON-AMAZON-SP-API](https://github.com/saleweaver/python-amazon-sp-api) wrapper for accessing the Amazon Selling Partner API.

## Amazon Data Logger

The `AmazonDataLogger` class in the `amazon_data_logger.py` file is a utility for logging order items and inventory levels from Amazon via the SP API. It stores this data in two CSV files. Here's a brief overview of its functionality:

### Usage

1. Ensure you have the necessary credentials for the SP API. For further details, how to get the API credentials, see the [Python Amazon SP API documentation](https://sp-api-docs.saleweaver.com/from_code).

2. Ensure you have the [PYTHON-AMAZON-SP-API](https://github.com/saleweaver/python-amazon-sp-api) wrapper installed.

3. Create an instance of the `AmazonDataLogger` class. Make sure to pass your API credentials, the country code of the marketplace you are active in, and the paths to the CSV files for order items and stock levels. The available country codes can be found [here](https://developer-docs.amazon.com/sp-api/docs/marketplace-ids).

4. Use the class methods `collect_order_items` and `collect_inventory_levels` to retrieve past order items and current inventory levels from Amazon. When calling the `collect_order_items` class, you need to specify the number of days back that you want to collect order items for. Note that the method will only request and store order quantities for orders that are not yet represented in the CSV file.

### Class Methods

- `get_recent_orders(days_back)`: Requests recent orders via the SP API and returns a list of dictionaries containing purchase date and Amazon order ID.

- `get_order_items(orders)`: Requests order items for a list of orders from the SP API and returns a list of dictionaries with the keys PurchaseDate, AmazonOrderId, SKU, ASIN and Quantity.

- `collect_order_items(days_back)`: Collects order items that are not yet repesented in the CSV file for the specified number of days back via `get_order_items` and adds them to the specified CSV file.

- `collect_inventory_levels()`: Collects current inventory levels as provided by the SP API and adds them to the specified CSV file.

## Outflow Predicter

The `OutflowPredicter` class in the `outflow_predicter.py` file is used for predicting future inventory outflows based on past order data. It employs the sktime library for time series forecasting and uses a naive forecaster that predicts future sales based on the mean of past order quantities. Note that it can be easily modified to be used with other forecasters from the sktime library.

Here is a summary of its functionality:

### Usage

1. Create an instance of the `OutflowPredicter` class, by passing the path to the order items CSV file.

2. Use the class methods `prepare` and `predict` to specify the number of past days to be used for the forecasting and the number of days into the future to be predicted.

3. Access the `past` and `future` DataFrames to access the past and predicted future sales data.

### Class Methods

- `prepare_past(days_back)`: Prepares past sales data for forecasting based on the specified number of days back.

- `predict_future(days_in_future)`: Predicts future sales quantities for the specified number of days in the future.

## Replenishment Report

The `ReplenishmentReport` class in the `replenishment_report.py` file uses predictions from the `OutflowPredicter` and current inventory levels to calculate predicted out-of-stock dates. It also proposes replenishment quantities based on a date until which the inventory should not go below 0.

Here's an overview of its functionality:

### Usage

1. Create an instance of the `ReplenishmentReport` class by providing the paths to the order items and inventory levels CSV files, and specifying the number of days back and days in the future for prediction. The instance will automatically create an instance of the `OutflowPredicter` class, which will forecast future sales and which can be accessed via the `outflow_predicter` attribute. It will also create DataFrames with *by SKU* out-of-stock dates and *by SKU* days-left until out-of-stock.

2. To calculate replenishment quantities, call the `propose_replenishment_quantities` method and pass a date until which the inventory should not go below 0.

3. Access the predicted `out_of_stock_dates`, `days_left`, and `proposed_replenishment` quantities via the respective attributes.

### Class Methods

- `_predict_out_of_stock_dates()`: Calculates predicted out-of-stock dates for each SKU based on inventory levels and future sales predictions. This method is called automatically when creating an instance of the `ReplenishmentReport` class.

- `propose_replenishment_quantities(replenish_until_date)`: Calculates proposed replenishment quantities for each SKU based on predicted future sales and a date until which the inventory should not go below 0

## Dependencies

This code relies on the following Python libraries:

- `sp_api`: A Selling Partner API Python wrapper.
- `numpy`: For numerical operations.
- `pandas`: For data manipulation.
- `sktime`: For time series forecasting.
- `datetime`: For date and time manipulation.
- `logging`: For logging messages.
- `csv`: For CSV file handling.

You can install these dependencies using pip:

```bash
pip install sp-api numpy pandas scikit-time-series datetime
```

## Licence

This code is licensed under the MIT license. Feel free to explore and adapt this code for your Amazon inventory management needs.