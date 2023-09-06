from outflow_predicter import OutflowPredicter
import pandas as pd


class ReplenishmentReport:
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

    def predict_out_of_stock_dates(self) -> None:
        self.out_of_stock_dates = pd.Series()
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
        return self.out_of_stock_dates

    def propose_replenishment_quantities(self, replenish_until_date: str) -> None:
        self.replenischment_quantities = pd.Series()
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
        return self.replenischment_quantities


if __name__ == "__main__":
    rr = ReplenishmentReport("order_items.csv", "inventory_levels.csv", 21, 360)
    print(rr.predict_out_of_stock_dates())
    print(rr.propose_replenishment_quantities("2024-03-31"))
