import csv
import os
import logging
from time import sleep
from datetime import date, timedelta

from sp_api.api import Orders, Inventories
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiRequestThrottledException

from creds import CREDS_SPAPI

CSV_PATH_ORDER_ITEMS = "order_items.csv"
CSV_PATH_INVENTORY_LEVELS = "inventory_levels.csv"
MARKETPLACE = Marketplaces.DE
SYNC_DAYS_BACK = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class AmazonDataLogger:
    def __init__(
        self,
        creds_spapi: dict,
        marketplace: Marketplaces,
        csv_path_order_items: str,
        csv_path_inventory_levels: str,
    ) -> None:
        self.orders_client = Orders(credentials=creds_spapi, marketplace=marketplace)
        self.inventories_client = Inventories(
            credentials=creds_spapi, marketplace=marketplace
        )
        self.csv_path_order_items = csv_path_order_items
        self.csv_path_inventory_levels = csv_path_inventory_levels
        self.order_items = self.get_order_items_from_csv()

    def get_order_items_from_csv(self) -> list:
        if os.path.isfile(self.csv_path_order_items):
            with open(self.csv_path_order_items, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                return [row for row in reader]
        else:
            return []

    def add_order_items_to_csv(self, order_items: list) -> None:
        if order_items:
            if os.path.isfile(self.csv_path_order_items):
                logging.info(f"Adding {len(order_items)} order items to csv")
                with open(self.csv_path_order_items, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
                    writer.writerows(order_items)
            else:
                logging.info(f"Creating csv with {len(order_items)} order items")
                with open(self.csv_path_order_items, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
                    writer.writeheader()
                    writer.writerows(order_items)

    def request_recent_orders_from_spapi(self, days_back: int) -> list:
        created_after = date.today() - timedelta(days=days_back)
        orders_ = []
        next_token = "start"
        while next_token:
            logging.info(
                f"Requesting orders created after {created_after} \n NextToken: {next_token}"
            )
            try:
                if next_token == "start":
                    res = self.orders_client.get_orders(CreatedAfter=created_after)
                else:
                    res = self.orders_client.get_orders(
                        NextToken=res.payload["NextToken"],
                    )
                orders_.extend(res.payload["Orders"])
                next_token = res.next_token
            except SellingApiRequestThrottledException as e:
                logging.exception(f"Exception: {e} \n --> Sleeping for 60 seconds")
                sleep(60)
        return orders_

    def get_recent_orders(self, days_back: int) -> list:
        orders_ = self.request_recent_orders_from_spapi(days_back)
        orders = [
            {
                "PurchaseDate": order_["PurchaseDate"],
                "AmazonOrderId": order_["AmazonOrderId"],
            }
            for order_ in orders_
        ]
        return orders

    def request_order_items_from_spapi(self, order_id: str) -> list:
        logging.info(f"Requesting order items of order {order_id}")
        while True:
            try:
                return self.orders_client.get_order_items(order_id=order_id)
            except SellingApiRequestThrottledException as e:
                logging.exception(f"Exception: {e} \n --> Sleeping for 2 seconds")
                sleep(2)

    def get_order_items(self, orders: list) -> list:
        order_items = []
        for order in orders:
            order_items_ = self.request_order_items_from_spapi(
                order["AmazonOrderId"]
            ).payload["OrderItems"]
            order_items.extend(
                [
                    {
                        "AmazonOrderId": order["AmazonOrderId"],
                        "PurchaseDate": order["PurchaseDate"],
                        "ASIN": order_item_["ASIN"],
                        "SellerSKU": order_item_["SellerSKU"],
                        "QuantityOrdered": order_item_["QuantityOrdered"],
                    }
                    for order_item_ in order_items_
                ]
            )
        return order_items

    def collect_order_items(self, days_back: int) -> None:
        orders = self.get_recent_orders(days_back)
        csv_order_ids = set(
            [order_item["AmazonOrderId"] for order_item in self.order_items]
        )
        orders = [
            order for order in orders if order["AmazonOrderId"] not in csv_order_ids
        ]
        order_items = self.get_order_items(orders)
        self.add_order_items_to_csv(order_items)

    def request_inventory_levels_from_spapi(self) -> set:
        logging.info("Requesting inventory levels")
        inventory = []
        next_token = "start"
        while next_token:
            try:
                if next_token == "start":
                    res = self.inventories_client.get_inventory_summary_marketplace()
                else:
                    res = self.inventories_client.get_inventory_summary_marketplace(
                        nextToken=next_token
                    )
                inventory.extend(res.payload["inventorySummaries"])
                next_token = res.next_token
            except SellingApiRequestThrottledException:
                sleep(2)
        return inventory

    def collect_invetory_levels(self) -> set:
        inventory = self.request_inventory_levels_from_spapi()
        logging.info(f"Writing {len(inventory)} inventory levels to csv")
        with open(self.csv_path_inventory_levels, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=inventory[0].keys())
            writer.writeheader()
            writer.writerows(inventory)


if __name__ == "__main__":
    amazon_data_logger = AmazonDataLogger(
        creds_spapi=CREDS_SPAPI,
        marketplace=MARKETPLACE,
        csv_path_order_items=CSV_PATH_ORDER_ITEMS,
        csv_path_inventory_levels=CSV_PATH_INVENTORY_LEVELS,
    )

    amazon_data_logger.collect_order_items(days_back=7)
    inventory = amazon_data_logger.collect_invetory_levels()
