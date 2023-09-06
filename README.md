# Inventory Replenishment Predictor for Amazon FBA Sellers

This repository contains Python code for logging Amazon orders and inventory levels via the Selling Partner API (SP API). It also includes tools to predict future sales quantities and propose replenishment quantities based on current inventory levels and predicted future sales.

## Amazon Data Logger

The `AmazonDataLogger` class in the `amazon_data_logger.py` file is a utility for logging order items and inventory levels from Amazon via the SP API. It stores the data in two CSV files. Here's a brief overview of its functionality:

### Usage

1. Ensure you have the necessary SP API credentials in a file named `creds.py`. For further details, see the [Python Amazon SP API documentation](https://sp-api-docs.saleweaver.com/from_code).

2. Modify the constants at the beginning of the script to customize the file paths and other settings as needed.

3. Run the script. It will collect order items from the last `SYNC_DAYS_BACK` days and add them to the CSV file with the specified path for order items. It will also fetch current inventory levels and store them in the CSV file with the specified path for inventory levels.

### Class Methods

- `get_recent_orders(days_back)`: Requests recent orders via the SP API and returns a list of dictionaries containing purchase date and Amazon order ID.

- `get_order_items(orders)`: Requests order items for a list of orders from the SP API and returns a list of dictionaries with the keys PurchaseDate, AmazonOrderId, SKU, ASIN and Quantity.

- `collect_order_items(days_back)`: Collects order items that are not yet repesented in the CSV file for the specified number of days back via `get_order_items` and adds them to the specified CSV file.

- `collect_inventory_levels()`: Collects current inventory levels as provided by the SP API and adds them to the specified CSV file.

## Outflow Predictor

The `OutflowPredicter` class in the `outflow_predicter.py` file is used for predicting future inventory outflows based on past order data. It employs the sktime library for time series forecasting and uses a naive forecaster that predicts based on the mean of past values, however it can be easily modified to be used with other forcaster from the sktime library.

Here's a summary of its functionality:

### Usage

1. Create an instance of the `OutflowPredicter` class, providing the path to the order items CSV file.

2. Use the class methods `prepare` to prepare the historical sales data and `predict` to predict future sales quantities.

3. Access the `past` and `future` DataFrames to access the past and predicted future sales data.

### Class Methods

- `prepare_past(days_back)`: Prepares past sales data for forecasting based on the specified number of days back.

- `predict_future(days_in_future)`: Predicts future sales quantities for the specified number of days in the future.

## Replenishment Report

The `ReplenishmentReport` class in the `replenishment_report.py` file uses the predictions from the `OutflowPredicter` and current inventory levels to calculate predicted out-of-stock dates. It also proposes replenishment quantities based on a date until which the inventory should not go below 0.

Here's an overview of its functionality:

### Usage

1. Create an instance of the `ReplenishmentReport` class, providing the paths to the order items and inventory levels CSV files, and specifying the number of days back and days in the future for prediction.

2. Use the class methods to predict out-of-stock dates and propose replenishment quantities based on a target replenishment date.

3. Access the predicted `out_of_stock_dates`, `days_left` until out-of-stock, and `proposed_replenishment` quantities.

### Class Methods

- `predict_out_of_stock_dates()`: Calculates predicted out-of-stock dates for each SKU based on inventory levels and future sales predictions.

- `propose_replenishment_quantities(replenish_until_date)`: Calculates proposed replenishment quantities for each SKU based on predicted future sales and a date until which the inventory should not go below 0

## Example Usage

To see these classes in action, you can refer to the code in the `if __name__ == "__main__":` sections at the bottom of each script. These sections demonstrate how to use the classes to collect data, make predictions, and generate replenishment reports.

## Dependencies

This code relies on the following Python libraries:

- `sp_api`: The Selling Partner API Python SDK for Amazon SP API.
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


Please ensure you have the necessary API credentials in `creds.py` and the CSV data files with order items and inventory levels before running the scripts.

Feel free to explore and adapt this code for your Amazon inventory management needs!