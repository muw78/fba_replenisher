import datetime

import numpy as np
import pandas as pd
from sktime.forecasting.naive import NaiveForecaster


class OutflowPredicter:
    """
    OutflowPredicter is a class for predicting future inventory outflows based on
    past order data. It uses the sktime library for time series forecasting. The
    forecasting model is a naive forecaster that predicts based on the mean of
    past values, however, it can be adapted to use other forecasting models.

    Args:
        csv_path_order_items (str): Path to CSV file containing past Amazon order items data

    Attributes:
        csv_path_order_items (str): Path to CSV file containing past Amazon order items data
        order_items (pd.DataFrame): Past Amazon order items data
        today (pd.Timestamp): Today's date
        days_back (int): Number of days back used for future sales prediction
        start_date (pd.Timestamp): The first day of the past periodu used for future sales prediction
        past (pd.DataFrame): Past sales data with one column per SKU and one row per day
        days_in_future (int): Number of days in future used for future sales prediction
        future (pd.DataFrame): Future sales data with one column per SKU and one row per day

    """

    def __init__(self, csv_path_order_items: str) -> None:
        self.csv_path_order_items = csv_path_order_items
        self.order_items = self.get_order_items(csv_path_order_items)
        self.today = pd.to_datetime(datetime.date.today())

    def get_order_items(self, csv_path_order_items) -> pd.DataFrame:
        """
        Reads order items data from CSV file and returns it as a DataFrame with the index
        set to the purchase date.

        Args:
            csv_path_order_items (str): Path to CSV file containing past Amazon order items data

        Returns:
            pd.DataFrame: Past Amazon order items data
        """

        order_items = pd.read_csv(csv_path_order_items)
        order_items.index = pd.to_datetime(
            pd.to_datetime(order_items["PurchaseDate"]).dt.date
        )
        order_items["QuantityOrdered"] = order_items["QuantityOrdered"].astype(int)
        return order_items

    def prepare_past(self, days_back: int) -> None:
        """
        Prepares past sales data for future sales prediction. The past sales data is pivoted into a DataFrame
        named past which has one column per SKU, one row per day and the values are the total quantity ordered.
        Days for which no sales data is available are filled with zeros.

        Args:
            days_back (int): Number of days back used for future sales prediction
        """

        self.days_back = days_back
        self.start_date = pd.to_datetime(
            self.today - datetime.timedelta(days=days_back)
        )
        self.order_items = self.order_items[
            (self.order_items.index >= self.start_date)
            & (self.order_items.index < self.today)
        ]
        self.past = (
            pd.pivot_table(
                self.order_items,
                values="QuantityOrdered",
                index=self.order_items.index,
                columns="SellerSKU",
                aggfunc=np.sum,
            )
            .reindex(pd.date_range(self.start_date, periods=days_back))
            .fillna(0)
        )
        self.past = self.past.reindex(sorted(self.past.columns), axis=1)

    def predict_future(self, days_in_future: int) -> None:
        """
        Predicts future sales based on past sales data. The future sales data is stored in a DataFrame
        named future which analoguous to the past dataframe has one column per SKU, one row per day and
        the values are the predicted total quantity ordered.
        This method uses the sktime library for time series forecasting. The forecasting model is a naive
        forecaster that predicts based on the mean of past values, however, it can be adapted to use other
        forecasting models.

        Args:
            days_in_future (int): Number of days in the future for which sales quantities are predicted
        """

        self.days_in_future = days_in_future
        self.future = pd.DataFrame(
            index=pd.date_range(self.today, periods=days_in_future, freq="D")
        )
        forecaster = NaiveForecaster(strategy="mean")
        for sku in self.past.columns:
            forecaster.fit(self.past[sku])
            self.future[sku] = forecaster.predict(self.future.index).astype(float)
