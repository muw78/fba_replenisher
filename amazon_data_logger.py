import csv
import os
import logging
from time import sleep
from datetime import date, timedelta

from sp_api.api import Orders, Inventories
from sp_api.base import Marketplaces
from sp_api.base.exceptions import SellingApiRequestThrottledException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class AmazonDataLogger:
    """
    AmazonDataLogger is a utility class to log order items and inventory levels from Amazon via the SP API.
    It stores the data in 2 csv files.

    Args:
        creds_spapi (dict): Dictionary containing the credentials for the SP API
        marketplace (str): The Amazon marketplace to log data from as country code
        csv_path_order_items (str): Path to the csv file to store the order items
        csv_path_inventory_levels (str): Path to the csv file to store the current inventory levels

    Attributes:
        orders_client (Orders): An instance of the SP API Orders class
        inventories_client (Inventories): An instance of the SP API Inventories class
        csv_path_order_items (str): Path to the csv file to store the order items
        csv_path_inventory_levels (str): Path to the csv file to store the current inventory levels
        order_items (list): List of order items from already stored csv_path_order_items file
    """

    def __init__(
        self,
        creds_spapi: dict,
        marketplace: str,
        csv_path_order_items: str,
        csv_path_inventory_levels: str,
    ) -> None:
        self.marketplace = getattr(Marketplaces, marketplace)
        self.orders_client = Orders(
            credentials=creds_spapi, marketplace=self.marketplace
        )
        self.inventories_client = Inventories(
            credentials=creds_spapi, marketplace=self.marketplace
        )
        self.csv_path_order_items = csv_path_order_items
        self.csv_path_inventory_levels = csv_path_inventory_levels
        self.order_items = self.get_order_items_from_csv()

    def get_order_items_from_csv(self) -> list:
        """
        Retrieves order items from the csv_path_order_items file

        Returns:
            list: List of dictionaries representing order items
        """

        if os.path.isfile(self.csv_path_order_items):
            with open(self.csv_path_order_items, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                return [row for row in reader]
        else:
            return []

    def add_order_items_to_csv(self, order_items: list) -> None:
        """
        Add dictionaries representing order items to the csv_path_order_items file.

        Args:
            order_items (list): List of dictionaries representing order items
        """

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
        """
        Request recent orders from the SP API. If the request is throttled,
        sleep for 60 seconds and try again.

        Args:
            days_back (int): Number of days back in time to request orders from

        Returns:
            list: List of dictionaries representing orders as returned by the SP API
        """

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
        """
        Requests recent orders from the SP API via request_recent_orders_from_spapi and
        returns a list of dictionaries containing only the PurchaseDate and AmazonOrderId.

        Args:
            days_back (int): Number of days back in time to request orders from

        Returns:
            list: List of dictionaries representing orders containing only the PurchaseDate and
            AmazonOrderId
        """

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
        """
        Request order items for a given order id from the SP API. If the request is throttled,
        sleep for 5 seconds and try again.

        Args:
            order_id (str): The AmazonOrderId to request order items for

        Returns:
            list: List of dictionaries representing order items as returned by the SP API
        """

        logging.info(f"Requesting order items of order {order_id}")
        while True:
            try:
                return self.orders_client.get_order_items(order_id=order_id)
            except SellingApiRequestThrottledException as e:
                logging.exception(f"Exception: {e} \n --> Sleeping for 2 seconds")
                sleep(5)

    def get_order_items(self, orders: list) -> list:
        """
        Requests order items for a list of orders from the SP API via request_order_items_from_spapi

        Args:
            orders (list): List of dictionaries representing orders containing only the PurchaseDate
            and AmazonOrderId

        Returns:
            list: List of dictionaries representing order items containing
                AmazonOrderId,
                PurchaseDate,
                ASIN,
                SellerSKU,
                QuantityOrdered
        """

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
        """
        Get order items for orders from the last days_back days and add them to the
        csv_path_order_items file. If an order item is already represented with an order item
        in the csv_path_order_items file, order items for this order are not requested and
        added.

        Args:
            days_back (int): Number of days back in time to request orders from
        """

        orders = self.get_recent_orders(days_back)
        csv_order_ids = set(
            [order_item["AmazonOrderId"] for order_item in self.order_items]
        )
        orders = [
            order for order in orders if order["AmazonOrderId"] not in csv_order_ids
        ]
        order_items = self.get_order_items(orders)
        self.add_order_items_to_csv(order_items)

    def request_inventory_levels_from_spapi(self) -> list:
        """
        Request inventory levels from the SP API. If the request is throttled, sleep for 2 seconds
        and try again.

        Returns:
            list: List of dictionaries representing inventory levels as returned by the SP API
        """

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

    def collect_invetory_levels(self):
        """
        Request inventory levels from the SP API via request_inventory_levels_from_spapi and
        add them as provided by the SP API to the csv_path_inventory_levels file.
        """

        inventory = self.request_inventory_levels_from_spapi()
        logging.info(f"Writing {len(inventory)} inventory levels to csv")
        with open(self.csv_path_inventory_levels, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=inventory[0].keys())
            writer.writeheader()
            writer.writerows(inventory)
