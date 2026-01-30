class Inventory:
    def add_item(self, item_name, quantity):
        """Add a specified quantity of an item to the inventory."""
        return f"Added {quantity} units of '{item_name}' to inventory"

    def remove_item(self, item_name, quantity):
        """Remove a specified quantity of an item from the inventory."""
        return f"Removed {quantity} units of '{item_name}' from inventory"

    def check_stock(self, item_name):
        """Check the current stock level of an item."""
        return f"'{item_name}' has 42 units in stock"

    def set_reorder_threshold(self, item_name, threshold):
        """Set the minimum stock level that triggers a reorder alert."""
        return f"Reorder threshold for '{item_name}' set to {threshold}"

    def is_in_stock(self, item_name):
        """Check whether an item is currently available in stock."""
        return True

    def get_low_stock_items(self):
        """Return a list of all items below their reorder threshold."""
        return ["Widget A", "Gadget B", "Component C"]

    def transfer_stock(self, item_name, quantity, destination):
        """Transfer stock of an item to another warehouse location."""
        return f"Transferred {quantity} units of '{item_name}' to {destination}"
