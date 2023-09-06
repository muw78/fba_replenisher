import datetime

import numpy as np
import pandas as pd
from sktime.forecasting.naive import NaiveForecaster
from sktime.utils.plotting import plot_series
import matplotlib.pyplot as plt


class OutflowPredicter:
    def __init__(self, csv_path_order_items: str) -> None:
        self.csv_path_order_items = csv_path_order_items
        self.order_items = pd.read_csv(csv_path_order_items)
        self.order_items.index = pd.to_datetime(
            pd.to_datetime(self.order_items["PurchaseDate"]).dt.date
        )
        self.order_items["QuantityOrdered"] = self.order_items[
            "QuantityOrdered"
        ].astype(int)
        self.today = pd.to_datetime(datetime.date.today())

    def prepare_past(self, days_back: int) -> None:
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
        self.days_in_future = days_in_future
        self.future = pd.DataFrame(
            index=pd.date_range(self.today, periods=days_in_future, freq="D")
        )
        for sku in self.past.columns:
            naive_forecaster = NaiveForecaster(strategy="mean")
            naive_forecaster.fit(self.past[sku])
            self.future[sku] = naive_forecaster.predict(self.future.index).astype(float)


if __name__ == "__main__":
    outflow_predicter = OutflowPredicter("order_items.csv")
    outflow_predicter.prepare_past(7)
    outflow_predicter.predict_future(14)
