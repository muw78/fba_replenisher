from outflow_predicter import OutflowPredicter
import pandas as pd


class ReplenishmentReport:
    """
    ReplenishmentReport is a class that predicts out of stock dates based on
    stock levels and future sales predictions. It also proposes replenishment
    quantities based on the sales predictions and the predicted out of stock dates.

    Args:
        csv_path_order_items (str): Path to csv file with order items
        csv_path_inventory_levels (str): Path to csv file with inventory levels
        days_back (int): Number of days back used for future sales prediction
        days_in_future (int): Number of days in the future for which sales quantities are predicted

    Attributes:
        outflow_predicter (OutflowPredicter): OutflowPredicter object
        past (pd.DataFrame): Past sales quatntities with one column per SKU and one row per day
        furture (pd.DataFrame): Predicted future sales quantities with one column per SKU and one row per day
        inventory_levels (pd.DataFrame): Current inventory levels
        out_of_stock_dates (pd.Series): Predicted out of stock dates for each SKU with predicted future sales
        days_left (pd.Series): Days left until out of stock for each SKU with predicted future sales

    """

    def __init__(
        self,
        csv_path_order_items: str,
        csv_path_inventory_levels: str,
        days_back: int,
        days_in_future: int,
    ) -> None:
        self.outflow_predicter = OutflowPredicter(csv_path_order_items)
        self.outflow_predicter.prepare_past(days_back)
        self.outflow_predicter.predict_future(days_in_future)
        self.past = self.outflow_predicter.past
        self.future = self.outflow_predicter.future
        self.inventory_levels = pd.read_csv(csv_path_inventory_levels)
        self._predict_out_of_stock_dates()

    def _predict_out_of_stock_dates(self) -> None:
        """
        This method calculates the predicted out of stock dates for each SKU with predicted future sales.
        It also calculates the days left until out of stock for each SKU with predicted future sales.
        """

        self.out_of_stock_dates = pd.Series(dtype="float64")
        for sku in self.future.columns:
            inventory_level = int(
                self.inventory_levels[self.inventory_levels["sellerSku"] == sku][
                    "totalQuantity"
                ]
            )
            for date in self.future.index:
                inventory_level -= self.future[sku][date]
                if inventory_level < 0:
                    self.out_of_stock_dates[sku] = date
                    break
        self.days_left = self.out_of_stock_dates - pd.to_datetime("today")

    def propose_replenishment_quantities(self, replenish_until_date: str) -> None:
        """
        This method calculates proposed replenishment quantities for each SKU based on predicted future sales
        and a date unitl the stock should not go out of stock.

        Args:
            replenish_until_date (str): Date until the stock should not go out of stock
        """

        self.replenischment_quantities = pd.Series(dtype="float64")
        for sku in self.future.columns:
            inventory_level = int(
                self.inventory_levels[self.inventory_levels["sellerSku"] == sku][
                    "totalQuantity"
                ]
            )
            for date in self.future.index:
                inventory_level -= self.future[sku][date]
                if date >= pd.to_datetime(replenish_until_date):
                    self.replenischment_quantities[sku] = -inventory_level
                    break
