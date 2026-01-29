class Restaurant:
    def add_to_menu(self, dish, price):
        """Add a new dish to the restaurant menu with its price."""
        return f"{dish} added to menu at ${price}"
    
    def take_order(self, table_number, items):
        """Record an order for a specific table."""
        return f"Order received for table {table_number}: {items}"
    
    def calculate_bill(self, table_number):
        """Calculate the total bill for a table."""
        return 45.50
    
    def reserve_table(self, date, time, guests):
        """Reserve a table for a specific date and time."""
        return f"Table reserved for {guests} guests on {date} at {time}"