class WeatherStation:
    def record_temperature(self, celsius):
        """Record the current temperature reading."""
        return f"Temperature recorded: {celsius}°C"
    
    def record_humidity(self, percentage):
        """Record the current humidity level."""
        return f"Humidity recorded: {percentage}%"
    
    def get_forecast(self, days):
        """Generate a weather forecast for the specified number of days."""
        return [f"Day {i+1}: Sunny, 25°C" for i in range(days)]
    
    def check_alerts(self):
        """Check for any severe weather alerts or warnings."""
        return []