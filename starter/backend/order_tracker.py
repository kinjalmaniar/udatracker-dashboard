# This module contains the OrderTracker class, which encapsulates the core
# business logic for managing orders.

VALID_STATUSES = ("pending", "processing", "shipped")


class OrderNotFoundError(ValueError):
    """Raised when an operation targets an order that does not exist."""


class OrderTracker:
    """
    Manages customer orders, providing functionalities to add, update,
    and retrieve order information.
    """
    def __init__(self, storage):
        required_methods = ['save_order', 'get_order', 'get_all_orders']
        for method in required_methods:
            if not hasattr(storage, method) or not callable(getattr(storage, method)):
                raise TypeError(f"Storage object must implement a callable '{method}' method.")
        self.storage = storage

    def add_order(self, order_id: str, item_name: str, quantity: int, customer_id: str, status: str = "pending"):
        self._require_text(order_id, "order_id")
        self._require_text(item_name, "item_name")
        self._require_text(customer_id, "customer_id")
        # bool is a subclass of int, so it is excluded explicitly
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        self._validate_status(status)

        if self.storage.get_order(order_id):
            raise ValueError(f"Order with ID '{order_id}' already exists.")

        order = {
            "order_id": order_id,
            "item_name": item_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "status": status
        }
        self.storage.save_order(order_id, order)
        return order

    def get_order_by_id(self, order_id: str):
        self._require_text(order_id, "order_id")
        return self.storage.get_order(order_id)

    def update_order_status(self, order_id: str, new_status: str):
        order = self._get_existing_order(order_id)
        self._validate_status(new_status)

        order["status"] = new_status
        self.storage.save_order(order_id, order)
        return order

    def delete_order(self, order_id: str):
        order = self._get_existing_order(order_id)
        self.storage.delete_order(order_id)
        return order

    def list_all_orders(self):
        return list(self.storage.get_all_orders().values())

    def list_orders_by_status(self, status: str):
        self._validate_status(status)
        return [order for order in self.list_all_orders() if order["status"] == status]

    def list_orders_by_customer(self, customer_id: str, status: str = None):
        self._require_text(customer_id, "customer_id")
        orders = self.list_orders_by_status(status) if status else self.list_all_orders()
        return [order for order in orders if order["customer_id"] == customer_id]

    def _get_existing_order(self, order_id: str):
        order = self.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found.")
        return order

    @staticmethod
    def _require_text(value, field: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"'{field}' is required.")

    @staticmethod
    def _validate_status(status: str):
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}.")
